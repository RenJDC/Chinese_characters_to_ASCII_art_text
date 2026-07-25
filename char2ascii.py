#!/usr/bin/env python3
"""
汉字 → ASCII 艺术字转换器
将单个汉字渲染为位图，再用 ASCII 字符密度映射输出。
"""

import argparse
import sys
from PIL import Image, ImageDraw, ImageFont

CHARSETS = {
    "classic":  "@%#WMo=-~:. ",
    "simple":   "@#=-. ",
    "blocks":   "█▓▒░ ",
    "minimal":  "#=-. ",
}

DEFAULT_FONT = "/System/Library/Fonts/PingFang.ttc"


def find_font(preferred=None):
    import os
    font_paths = [
        DEFAULT_FONT,
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    if preferred and os.path.isfile(preferred):
        return preferred
    for p in font_paths:
        if os.path.isfile(p):
            return p
    return None


def char_to_bitmap(char, font_path, cell_w, cell_h):
    """渲染汉字到灰度位图，笔画白色，背景黑色"""
    # 放大渲染再缩放，抗锯齿效果更好
    scale = 4
    big_w, big_h = cell_w * scale, cell_h * scale
    img = Image.new("L", (big_w, big_h), 0)
    draw = ImageDraw.Draw(img)

    font_size = int(min(big_w, big_h) * 0.8)
    font = ImageFont.truetype(font_path, font_size)

    bbox = draw.textbbox((0, 0), char, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (big_w - tw) // 2 - bbox[0]
    y = (big_h - th) // 2 - bbox[1]
    draw.text((x, y), char, fill=255, font=font)

    # 缩小回来取平均亮度，更平滑
    img = img.resize((cell_w, cell_h), Image.LANCZOS)
    return img


def render_ascii(img, charset, invert=False):
    """将灰度图映射为 ASCII 字符串"""
    w, h = img.size
    lines = []
    for y in range(h):
        line = []
        for x in range(w):
            px = img.getpixel((x, y))
            if invert:
                px = 255 - px
            # 亮→稀疏字符, 暗→密集字符（白底黑字效果）
            idx = int((1 - px / 255) * (len(charset) - 1))
            idx = max(0, min(idx, len(charset) - 1))
            line.append(charset[idx])
        lines.append("".join(line))
    return "\n".join(lines)


def convert(char, width=40, charset_name="classic", font_path=None, invert=False, height_ratio=1.0):
    charset = CHARSETS.get(charset_name, charset_name)
    font = find_font(font_path)
    if not font:
        print("错误: 未找到中文字体", file=sys.stderr)
        sys.exit(1)

    cell_w = width
    cell_h = int(width * height_ratio)

    img = char_to_bitmap(char, font, cell_w, cell_h)
    return render_ascii(img, charset, invert)


def batch_convert(text, width=40, charset_name="classic", font_path=None,
                   invert=False, height_ratio=1.0, gap=2):
    """多字并排渲染，gap 控制字间空格数"""
    charset = CHARSETS.get(charset_name, charset_name)
    font = find_font(font_path)
    if not font:
        print("错误: 未找到中文字体", file=sys.stderr)
        sys.exit(1)

    cell_w = width
    cell_h = int(width * height_ratio)
    gap_str = " " * gap

    bitmaps = [char_to_bitmap(ch, font, cell_w, cell_h) for ch in text]

    result_lines = [""] * cell_h
    for bm in bitmaps:
        for y in range(cell_h):
            row = []
            for x in range(cell_w):
                px = bm.getpixel((x, y))
                if invert:
                    px = 255 - px
                idx = int((1 - px / 255) * (len(charset) - 1))
                idx = max(0, min(idx, len(charset) - 1))
                row.append(charset[idx])
            result_lines[y] += "".join(row) + gap_str

    return "\n".join(result_lines)


def main():
    parser = argparse.ArgumentParser(description="汉字 → ASCII 艺术字")
    parser.add_argument("char", nargs="?", help="要转换的汉字（单个或多个）")
    parser.add_argument("-w", "--width", type=int, default=40, help="输出宽度（字符数，默认40）")
    parser.add_argument("-H", "--height-ratio", type=float, default=1.0, help="高度比例（默认1.0，即宽=高）")
    parser.add_argument("-c", "--charset", default="classic",
                        choices=list(CHARSETS.keys()),
                        help="字符集（默认 classic）")
    parser.add_argument("-f", "--font", default=None, help="字体路径")
    parser.add_argument("-i", "--invert", action="store_true", help="反转明暗（黑底白字 ↔ 白底黑字）")
    parser.add_argument("-g", "--gap", type=int, default=2, help="多字间距空格数（默认2）")
    parser.add_argument("--list-charsets", action="store_true", help="列出可用字符集")
    args = parser.parse_args()

    if args.list_charsets:
        print("可用字符集:")
        for name, chars in CHARSETS.items():
            print(f"  {name:10s} → {chars}")
        sys.exit(0)

    if not args.char:
        print("请输入汉字（输入 q 退出，多字自动并排）:")
        while True:
            try:
                text = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if text.lower() in ("q", "quit", "exit"):
                break
            if not text:
                continue
            print()
            if len(text) == 1:
                print(convert(text, args.width, args.charset, args.font, args.invert, args.height_ratio))
            else:
                print(batch_convert(text, args.width, args.charset, args.font,
                                    args.invert, args.height_ratio, args.gap))
            print()
    else:
        text = args.char
        if len(text) == 1:
            print(convert(text, args.width, args.charset, args.font, args.invert, args.height_ratio))
        else:
            print(batch_convert(text, args.width, args.charset, args.font,
                                args.invert, args.height_ratio, args.gap))


if __name__ == "__main__":
    main()
