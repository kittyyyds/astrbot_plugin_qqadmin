import argparse
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from menu import MENU_SECTIONS

WIDTH = 1000
INK = "#20292C"
MUTED = "#697779"
LINE = "#DCE5E5"
GREEN = "#087F6D"
PAPER = "#FFFFFF"


class Renderer:
    def __init__(self, regular: str, bold: str):
        self.font_paths = (regular, bold)
        self.fonts = {}

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(self.font_paths[bold], size)
        return self.fonts[key]

    def text(self, draw, position, text, size, color=INK, bold=False, max_width=None):
        font = self.font(size, bold)
        while max_width and draw.textlength(text, font=font) > max_width and size > 24:
            size -= 1
            font = self.font(size, bold)
        if max_width and draw.textlength(text, font=font) > max_width:
            raise ValueError(f"Menu text exceeds its column: {text}")
        draw.text(position, text, fill=color, font=font)

    def canvas(self, height):
        image = Image.new("RGB", (WIDTH, height), PAPER)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, WIDTH, 14), fill=GREEN)
        return image, draw

    def header(self, draw, title, subtitle, number=None):
        self.text(draw, (54, 48), "KITTY / QQ ADMIN", 24, GREEN, True)
        self.text(draw, (52, 89), title, 67, bold=True)
        self.text(draw, (56, 183), subtitle, 27, MUTED)
        draw.line((56, 244, 944, 244), fill=LINE, width=2)
        if number:
            self.text(draw, (867, 60), number, 38, GREEN, True)

    def footer(self, draw, y):
        draw.line((56, y, 944, y), fill=LINE, width=2)
        self.text(draw, (56, y + 22), "管理操作需要相应群权限，权限以本群配置为准", 24, MUTED)
        self.text(draw, (56, y + 62), "菜单首页  /菜单       完整帮助  /群管帮助", 26, GREEN, True)

    def home(self):
        image, draw = self.canvas(1510)
        self.header(draw, "Kitty 群管", "常用指令", "00")
        for index, section in enumerate(MENU_SECTIONS.values()):
            x = 56 + (index % 2) * 466
            y = 291 + (index // 2) * 440
            color = section["color"]
            self.text(draw, (x, y), f"0{index + 1}", 25, color, True)
            self.text(draw, (x + 52, y - 8), section["title"], 37, bold=True)
            draw.line((x, y + 52, x + 422, y + 52), fill=color, width=3)
            for row, (syntax, description) in enumerate(section["featured"]):
                top = y + 78 + row * 77
                self.text(draw, (x, top), f"/{syntax}", 30, bold=True, max_width=422)
                self.text(draw, (x, top + 40), description, 24, MUTED, max_width=422)
        y = 1170
        draw.rectangle((56, y, 944, y + 172), fill="#EDF7F4")
        self.text(draw, (80, y + 16), "分类详情", 26, GREEN, True)
        for index, section in enumerate(MENU_SECTIONS.values()):
            self.text(draw, (80 + index % 2 * 434, y + 65 + index // 2 * 48),
                      f"/菜单 {section['keyword']}", 29, bold=True)
        self.footer(draw, 1380)
        return image

    def detail(self, key, index):
        section = MENU_SECTIONS[key]
        height = 302 + len(section["commands"]) * 112 + 154
        image, draw = self.canvas(height)
        self.header(draw, section["title"], f"Kitty 群管  /  /菜单 {section['keyword']}", f"0{index}")
        for row, (_, syntax, description) in enumerate(section["commands"]):
            y = 280 + row * 112
            draw.rectangle((56, y + 10, 62, y + 44), fill=section["color"])
            self.text(draw, (80, y), f"/{syntax}", 34, bold=True, max_width=856)
            self.text(draw, (80, y + 51), description, 25, MUTED, max_width=856)
            draw.line((80, y + 98, 944, y + 98), fill=LINE, width=1)
        self.footer(draw, height - 125)
        return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", default="C:/Windows/Fonts/msyh.ttc")
    parser.add_argument("--bold-font", default="C:/Windows/Fonts/msyhbd.ttc")
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "menu")
    args = parser.parse_args()
    renderer = Renderer(args.font, args.bold_font)
    args.output.mkdir(parents=True, exist_ok=True)
    renderer.home().save(args.output / "home.png", optimize=True)
    for index, key in enumerate(MENU_SECTIONS, 1):
        renderer.detail(key, index).save(args.output / f"{key}.png", optimize=True)


if __name__ == "__main__":
    main()
