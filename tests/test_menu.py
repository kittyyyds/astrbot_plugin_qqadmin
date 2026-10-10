import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from menu import MENU_SECTIONS, get_menu_page, menu_image_path, menu_text


class MenuTests(unittest.TestCase):
    def test_all_registered_management_commands_are_documented(self):
        tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
        registered = {
            decorator.args[0].value
            for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "command"
        }
        documented = {name for section in MENU_SECTIONS.values() for name, _, _ in section["commands"]}
        self.assertEqual(registered - {"群管帮助"}, documented)

    def test_category_aliases_and_invalid_input(self):
        for index, (key, section) in enumerate(MENU_SECTIONS.items(), 1):
            for alias in (key, str(index), section["keyword"], section["title"]):
                self.assertEqual(get_menu_page(f" {alias} "), key)
        self.assertEqual(get_menu_page(), "home")
        self.assertIsNone(get_menu_page("../../cmd_config"))
        with self.assertRaises(ValueError):
            menu_image_path("../cmd_config")

    def test_images_are_bundled_and_text_fallback_is_complete(self):
        for page in ("home", *MENU_SECTIONS):
            path = menu_image_path(page)
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertIn("Kitty 群管", menu_text(page))
        for key, section in MENU_SECTIONS.items():
            for _, syntax, _ in section["commands"]:
                self.assertIn(syntax, menu_text(key))


if __name__ == "__main__":
    unittest.main()
