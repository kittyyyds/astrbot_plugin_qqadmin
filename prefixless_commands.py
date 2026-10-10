from astrbot.api.event import filter
from astrbot.core.message.components import At
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.filter.command import CommandFilter
from astrbot.core.star.star_handler import star_handlers_registry


class PrefixlessGroupCommandFilter(CommandFilter):
    def filter(self, event, cfg) -> bool:
        if event.is_at_or_wake_command:
            return super().filter(event, cfg)
        if not isinstance(event, AiocqhttpMessageEvent):
            return False
        if event.is_private_chat() or not event.get_group_id():
            return False
        if str(event.get_sender_id()) == str(event.get_self_id()):
            return False
        messages = event.get_messages()
        if messages and isinstance(messages[0], At):
            return False
        words = event.get_message_str().split(maxsplit=1)
        if not words or not self.equals(words[0]):
            return False

        # Temporarily allow the native parser without waking other plugins' commands.
        event.is_at_or_wake_command = True
        try:
            matched = super().filter(event, cfg)
        finally:
            event.is_at_or_wake_command = False
        if matched:
            event.should_call_llm(False)
        return matched


def command(command_name: str, alias: set | None = None, **kwargs):
    native_decorator = filter.command(command_name, alias=alias, **kwargs)

    def decorator(handler):
        handler = native_decorator(handler)
        metadata = star_handlers_registry.get_handler_by_full_name(
            f"{handler.__module__}_{handler.__name__}"
        )
        if metadata is None or not isinstance(metadata.event_filters[-1], CommandFilter):
            raise RuntimeError("Cannot extend the registered QQAdmin command")
        native_filter = metadata.event_filters[-1]
        group_filter = PrefixlessGroupCommandFilter(
            native_filter.command_name,
            native_filter.alias,
            metadata,
            native_filter.parent_command_names,
        )
        group_filter.custom_filter_list = native_filter.custom_filter_list
        metadata.event_filters[-1] = group_filter
        return handler

    return decorator
