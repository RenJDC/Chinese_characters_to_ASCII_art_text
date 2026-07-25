#!/usr/bin/env python3
"""
汉字 → ASCII 艺术字转换器

API 用法:
    from char2ascii import convert, batch_convert, CHARSETS, find_font

    # 单字转换
    print(convert("龙", width=40, charset_name="classic"))

    # 多字并排
    print(batch_convert("龙猫", width=30, charset_name="blocks", gap=3))

    # 查看可用字符集
    print(list(CHARSETS.keys()))

    # 查找字体
    font_path = find_font()
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

__all__ = [
    "CHARSETS",
    "find_font",
    "char_to_bitmap",
    "render_ascii",
    "convert",
    "batch_convert",
]

# ─── 字符集定义 ───────────────────────────────────────────────

CHARSETS = {
    "classic":   "@%#WMo=-~:. ",
    "simple":    "@#=-. ",
    "blocks":    "█▓▒░ ",
    "minimal":   "#=-. ",
    "3d":        "@%#WMBRW$&8XOZmwqpdbao*+=-:. ",
    "italic":    "///\\\\\\|||;;;:::,,,;;;|||\\\\\\/// ",
    "bold":      "█▇▆▅▄▃▂▁ ",
    "thin":      "─━═║┃┆┇┊┋ ",
    "gothic":    "▓█▄▀▌▐■□◆◇●○ ",
    "graffiti":  "@%#MW&8B$S#%W@ ",
    "gradient":  "@%#WMo=-~^:;,. ",
    "braille":   "⣿⣷⣯⣟⡿⢿⣻⣽⣾⣶⣴⣲⣳⣱⠀⠀ ",
    "halfblock": "▀▄█▓▒░ ",
    "box":       "█▓▒░╔╗╚╝═║┌┐└┘├┤┬┴┼ ",
    "dots":      "●◉◎∘○○∘◎◉● ",
    "stars":     "★☆✦✧✪✫✬✭✮✯ ",
}


# ─── 字体查找 ─────────────────────────────────────────────────

def find_font(preferred=None):
    """
    查找可用的中文字体。

    查找顺序:
        1. preferred 参数指定的路径
        2. 项目 fonts/ 目录下的字体
        3. 系统字体（按平台自动检测）

    Args:
        preferred: 优先使用的字体文件路径，为 None 时自动查找

    Returns:
        str: 字体文件路径，找不到返回 None
    """
    if preferred and os.path.isfile(preferred):
        return preferred

    # 项目 fonts/ 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_fonts_dir = os.path.join(script_dir, "fonts")
    local_font_prefs = [
        "NotoSansSC-Regular.otf",
        "NotoSansSC-Bold.otf",
        "NotoSansSC-Medium.otf",
        "SourceHanSansSC-Regular.otf",
        "WenQuanYiMicroHei.ttf",
    ]
    if os.path.isdir(local_fonts_dir):
        for name in local_font_prefs:
            path = os.path.join(local_fonts_dir, name)
            if os.path.isfile(path):
                return path
        for f in sorted(os.listdir(local_fonts_dir)):
            if f.lower().endswith((".ttf", ".otf", ".ttc")):
                return os.path.join(local_fonts_dir, f)

    # 系统字体
    import platform
    system = platform.system()
    if system == "Darwin":
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    elif system == "Linux":
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]
    elif system == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        font_paths = [
            os.path.join(windir, "Fonts", "msyh.ttc"),
            os.path.join(windir, "Fonts", "simhei.ttf"),
            os.path.join(windir, "Fonts", "simsun.ttc"),
            os.path.join(windir, "Fonts", "msyhbd.ttc"),
        ]
    else:
        font_paths = []

    for p in font_paths:
        if os.path.isfile(p):
            return p
    return None


# ─── 底层渲染 ─────────────────────────────────────────────────

def char_to_bitmap(char, font_path, cell_w, cell_h):
    """
    将单个字符渲染为灰度位图。

    Args:
        char:       要渲染的字符（单个）
        font_path:  字体文件路径
        cell_w:     输出宽度（像素）
        cell_h:     输出高度（像素）

    Returns:
        PIL.Image: 灰度图（L 模式），笔画白色(255)，背景黑色(0)

    Raises:
        ValueError: 字体加载失败时抛出
    """
    scale = 4
    big_w, big_h = cell_w * scale, cell_h * scale
    img = Image.new("L", (big_w, big_h), 0)
    draw = ImageDraw.Draw(img)

    font_size = int(min(big_w, big_h) * 0.8)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        raise ValueError(f"字体加载失败 ({os.path.basename(font_path)}): {e}")

    bbox = draw.textbbox((0, 0), char, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (big_w - tw) // 2 - bbox[0]
    y = (big_h - th) // 2 - bbox[1]
    draw.text((x, y), char, fill=255, font=font)

    img = img.resize((cell_w, cell_h), Image.LANCZOS)
    return img


def render_ascii(img, charset, invert=False):
    """
    将灰度图映射为 ASCII 字符串。

    Args:
        img:      PIL.Image 灰度图
        charset:  字符集字符串（从密到疏排列）
        invert:   是否反转明暗

    Returns:
        str: 多行 ASCII 字符串
    """
    w, h = img.size
    lines = []
    for y in range(h):
        line = []
        for x in range(w):
            px = img.getpixel((x, y))
            if invert:
                px = 255 - px
            idx = int((1 - px / 255) * (len(charset) - 1))
            idx = max(0, min(idx, len(charset) - 1))
            line.append(charset[idx])
        lines.append("".join(line))
    return "\n".join(lines)


# ─── 高层 API ─────────────────────────────────────────────────

def convert(char, width=40, charset_name="classic", font_path=None,
            invert=False, height_ratio=1.0):
    """
    将单个汉字转换为 ASCII 艺术字。

    Args:
        char:          要转换的汉字（单个字符）
        width:         输出宽度，即每行字符数（默认 40）
        charset_name:  字符集名称或自定义字符集字符串（默认 "classic"）
        font_path:     字体文件路径，None 时自动查找
        invert:        是否反转明暗（默认 False，白底黑字）
        height_ratio:  高度与宽度的比例（默认 1.0）

    Returns:
        str: 多行 ASCII 艺术字字符串

    Raises:
        ValueError: 找不到字体时抛出

    Example:
        >>> print(convert("龙", width=30, charset_name="braille"))
    """
    charset = CHARSETS.get(charset_name, charset_name)
    font = find_font(font_path)
    if not font:
        raise ValueError("未找到中文字体，请用 font_path 参数指定，或放入 fonts/ 目录")

    cell_w = width
    cell_h = int(width * height_ratio)

    img = char_to_bitmap(char, font, cell_w, cell_h)
    return render_ascii(img, charset, invert)


def batch_convert(text, width=40, charset_name="classic", font_path=None,
                  invert=False, height_ratio=1.0, gap=2):
    """
    将多个汉字并排转换为 ASCII 艺术字。

    Args:
        text:          要转换的汉字字符串（多个字符并排显示）
        width:         每个字符的输出宽度（默认 40）
        charset_name:  字符集名称或自定义字符集字符串（默认 "classic"）
        font_path:     字体文件路径，None 时自动查找
        invert:        是否反转明暗（默认 False）
        height_ratio:  高度与宽度的比例（默认 1.0）
        gap:           字符之间的空格数（默认 2）

    Returns:
        str: 多行 ASCII 艺术字字符串（多字并排）

    Raises:
        ValueError: 找不到字体时抛出

    Example:
        >>> print(batch_convert("龙猫", width=25, charset_name="blocks"))
    """
    charset = CHARSETS.get(charset_name, charset_name)
    font = find_font(font_path)
    if not font:
        raise ValueError("未找到中文字体，请用 font_path 参数指定，或放入 fonts/ 目录")

    cell_w = width
    cell_h = int(width * height_ratio)
    gap_str = " " * gap

    bitmaps = [char_to_bitmap(ch, font, cell_w, cell_h) for ch in text]

    result_lines = [""] * cell_h
    for i, bm in enumerate(bitmaps):
        for y in range(cell_h):
            row = []
            for x in range(cell_w):
                px = bm.getpixel((x, y))
                if invert:
                    px = 255 - px
                idx = int((1 - px / 255) * (len(charset) - 1))
                idx = max(0, min(idx, len(charset) - 1))
                row.append(charset[idx])
            suffix = gap_str if i < len(bitmaps) - 1 else ""
            result_lines[y] += "".join(row) + suffix

    return "\n".join(result_lines)


# ─── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="汉字 → ASCII 艺术字")
    parser.add_argument("char", nargs="?", help="要转换的汉字（单个或多个）")
    parser.add_argument("-w", "--width", type=int, default=40, help="输出宽度（字符数，默认40）")
    parser.add_argument("-H", "--height-ratio", type=float, default=1.0, help="高度比例（默认1.0）")
    parser.add_argument("-c", "--charset", default="classic",
                        choices=list(CHARSETS.keys()),
                        help="字符集（默认 classic）")
    parser.add_argument("-f", "--font", default=None, help="字体路径")
    parser.add_argument("-i", "--invert", action="store_true", help="反转明暗")
    parser.add_argument("-g", "--gap", type=int, default=2, help="多字间距空格数（默认2）")
    parser.add_argument("--list-charsets", action="store_true", help="列出可用字符集")
    args = parser.parse_args()

    if args.list_charsets:
        print("可用字符集:")
        for name, chars in CHARSETS.items():
            print(f"  {name:10s} → {chars}")
        sys.exit(0)

    if not args.char:
        charset_name = args.charset
        width = args.width
        invert = args.invert
        gap = args.gap
        height_ratio = args.height_ratio
        font_path = args.font

        HELP_TEXT = """交互命令:
  /c <风格>    切换字符集    例: /c braille
  /w <宽度>    调整宽度      例: /w 60
  /i           反转明暗      例: /i
  /g <间距>    调整字间距    例: /g 4
  /r <比例>    调整高度比    例: /r 1.2
  /s           查看当前设置
  /l           列出所有字符集
  /help        查看帮助
  q            退出"""

        def show_status():
            inv = "是" if invert else "否"
            print(f"  风格: {charset_name}  宽度: {width}  间距: {gap}  高度比: {height_ratio}  反色: {inv}")

        print("请输入汉字（q 退出，/help 查看命令）:")
        print(f"  当前: ", end="")
        show_status()
        print()
        while True:
            try:
                text = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text:
                continue
            if text.lower() in ("q", "quit", "exit"):
                break

            if text.startswith("/"):
                parts = text.split(maxsplit=1)
                cmd = parts[0].lower()
                val = parts[1].strip() if len(parts) > 1 else ""

                if cmd in ("/help",):
                    print(HELP_TEXT)
                elif cmd in ("/s", "/status"):
                    show_status()
                elif cmd in ("/l", "/list"):
                    for name, chars in CHARSETS.items():
                        mark = " ←" if name == charset_name else ""
                        print(f"  {name:12s}{chars}{mark}")
                elif cmd in ("/c", "/charset"):
                    if val in CHARSETS:
                        charset_name = val
                        print(f"  已切换: {charset_name}")
                    else:
                        print(f"  未知风格，/l 查看可用")
                elif cmd in ("/w", "/width"):
                    try:
                        width = max(10, min(200, int(val)))
                        print(f"  宽度: {width}")
                    except ValueError:
                        print("  用法: /w <数字>")
                elif cmd in ("/g", "/gap"):
                    try:
                        gap = max(0, min(20, int(val)))
                        print(f"  间距: {gap}")
                    except ValueError:
                        print("  用法: /g <数字>")
                elif cmd in ("/r", "/ratio", "/rh"):
                    try:
                        height_ratio = max(0.3, min(3.0, float(val)))
                        print(f"  高度比: {height_ratio}")
                    except ValueError:
                        print("  用法: /r <数字>")
                elif cmd == "/i":
                    invert = not invert
                    state = "开" if invert else "关"
                    print(f"  反色: {state}")
                else:
                    print(f"  未知命令，/help 查看帮助")
                continue

            print()
            if len(text) == 1:
                print(convert(text, width, charset_name, font_path, invert, height_ratio))
            else:
                print(batch_convert(text, width, charset_name, font_path,
                                    invert, height_ratio, gap))
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
