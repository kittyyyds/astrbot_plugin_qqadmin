import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@unittest.skipUnless(importlib.util.find_spec("astrbot"), "Requires AstrBot runtime")
class PrefixlessCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from astrbot.core.message.components import At, Plain
        from astrbot.core.platform.message_type import MessageType
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
            AiocqhttpMessageEvent,
        )
        from astrbot.core.star.filter.command import CommandFilter
        from prefixless_commands import PrefixlessGroupCommandFilter

        cls.At = At
        cls.Plain = Plain
        cls.MessageType = MessageType
        cls.Event = AiocqhttpMessageEvent
        cls.NativeFilter = CommandFilter
        cls.GroupFilter = PrefixlessGroupCommandFilter

    def event(self, text, *, private=False, sender="10001", messages=None):
        event = object.__new__(self.Event)
        event.message_str = text
        event.message_obj = SimpleNamespace(
            type=self.MessageType.FRIEND_MESSAGE if private else self.MessageType.GROUP_MESSAGE,
            group_id="" if private else "10002",
            self_id="10000",
            sender=SimpleNamespace(user_id=sender),
            message=messages if messages is not None else [self.Plain(text)],
        )
        event.platform_meta = SimpleNamespace(name="aiocqhttp")
        event.is_at_or_wake_command = False
        event.is_wake = False
        event.call_llm = True
        event._extras = {}
        event._result = None
        event._force_stopped = False
        return event

    def command_filter(self, name, aliases=None, handler=None, native=False):
        async def menu_handler(self, event, category=""):
            pass

        filter_class = self.NativeFilter if native else self.GroupFilter
        return filter_class(name, aliases, SimpleNamespace(handler=handler or menu_handler))

    def test_menu_aliases_and_category_use_native_parser(self):
        command_filter = self.command_filter("群管帮助", {"菜单", "群管菜单"})
        for text, category in [("菜单", ""), ("菜单 基础", "基础"), ("菜单\t2", "2"),
                               ("群管帮助", ""), ("群管菜单 资料", "资料")]:
            with self.subTest(text=text):
                event = self.event(text)
                self.assertTrue(command_filter.filter(event, {}))
                self.assertEqual(event.get_extra("parsed_params"), {"category": category})
                self.assertFalse(event.is_at_or_wake_command)
                self.assertFalse(event.call_llm)
                self.assertEqual(event.message_str, text)

    def test_management_arguments_and_mentions_are_preserved(self):
        async def ban_handler(self, event, duration=None):
            pass

        command_filter = self.command_filter("禁言", handler=ban_handler)
        event = self.event("禁言 300", messages=[self.Plain("禁言 300 "), self.At(qq="10003")])
        self.assertTrue(command_filter.filter(event, {}))
        self.assertEqual(event.get_extra("parsed_params"), {"duration": 300})
        self.assertEqual(str(event.get_messages()[1].qq), "10003")

    def test_ordinary_chat_does_not_change_wake_or_ai_state(self):
        command_filter = self.command_filter("群管帮助", {"菜单", "群管菜单"})
        for text in ["", "你好", "这个菜单不错", "菜单真漂亮", "群管菜单在哪", "菜单基础", "/菜单"]:
            with self.subTest(text=text):
                event = self.event(text)
                self.assertFalse(command_filter.filter(event, {}))
                self.assertFalse(event.is_at_or_wake_command)
                self.assertFalse(event.is_wake)
                self.assertTrue(event.call_llm)
                self.assertEqual(event._extras, {})

    def test_new_matching_only_applies_to_other_users_in_qq_groups(self):
        command_filter = self.command_filter("菜单")
        other_platform = SimpleNamespace(is_at_or_wake_command=False, call_llm=True)
        for event in [self.event("菜单", private=True), self.event("菜单", sender="10000"),
                      self.event("菜单", messages=[self.At(qq="10003"), self.Plain("菜单")]),
                      other_platform]:
            self.assertFalse(command_filter.filter(event, {}))
            self.assertTrue(event.call_llm)

    def test_existing_prefix_and_mention_path_is_unchanged(self):
        command_filter = self.command_filter("菜单")
        event = self.event("菜单 防护")
        event.is_at_or_wake_command = True
        self.assertTrue(command_filter.filter(event, {}))
        self.assertTrue(event.is_at_or_wake_command)
        self.assertTrue(event.call_llm)
        self.assertEqual(event.get_extra("parsed_params"), {"category": "防护"})

    def test_native_commands_in_other_plugins_are_not_awakened(self):
        event = self.event("菜单")
        self.assertTrue(self.command_filter("菜单").filter(event, {}))
        self.assertFalse(self.command_filter("菜单", native=True).filter(event, {}))

    def test_invalid_parameters_restore_wake_state(self):
        async def integer_handler(self, event, duration: int):
            pass

        command_filter = self.command_filter("禁言", handler=integer_handler)
        for text in ["禁言", "禁言 abc"]:
            event = self.event(text)
            with self.assertRaises(ValueError):
                command_filter.filter(event, {})
            self.assertFalse(event.is_at_or_wake_command)
            self.assertTrue(event.call_llm)


if __name__ == "__main__":
    unittest.main()
