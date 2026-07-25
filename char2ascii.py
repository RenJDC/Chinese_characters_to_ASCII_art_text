#!/usr/bin/env python3
"""
汉字 → ASCII 艺术字转换器
将单个汉字渲染为位图，再用 ASCII 字符密度映射输出。
"""

import argparse
import sys
from PIL import Image, ImageDraw, ImageFont

CHARSETS = {
    # 经典 ASCII 密度映射
    "classic":      "@%#WMo=-~:. ",
    # 简洁高对比
    "simple":       "@#=-. ",
    # 方块像素风（像素画感）
    "blocks":       "█▓▒░ ",
    # 极简
    "minimal":      "#=-. ",
    # 3D 立体阴影（用立体字符营造厚度感）
    "3d":           "@%#WMBRW$&8XOZmwqpdbao*+=-:. ",
    # 斜线流动风（用斜线营造动感）
    "italic":       "///\\\\\\|||;;;:::,,,;;;|||\\\\\\/// ",
    # 粗块厚重风（超密集，适合大标题）
    "bold":         "█▇▆▅▄▃▂▁ ",
    # 细线极简风（细线条，适合窄栏）
    "thin":         "─━═║┃┆┇┊┋ ",
    # 哥特复古风（棱角字符）
    "gothic":       "▓█▄▀▌▐■□◆◇●○ ",
    # 涂鸦艺术风（不规则符号）
    "graffiti":     "@%#MW&8B$S#%W@ ",
    # 渐变灰阶（平滑过渡）
    "gradient":     "@%#WMo=-~^:;,. ",
    # Braille 精细风（Unicode 点阵，细节最丰富）
    "braille":      "⣿⣷⣯⣟⡿⢿⣻⣽⣾⣶⣴⣲⣳⣱⠀⠀ ",
    # 半块像素风（比 blocks 更精细）
    "halfblock":    "▀▄█▓▒░ ",
    # 制表符几何风
    "box":          "█▓▒░╔╗╚╝═║┌┐└┘├┤┬┴┼ ",
    # 圆点矩阵风
    "dots":         "●◉◎∘○○∘◎◉● ",
    # 星号装饰风
    "stars":        "★☆✦✧✪✫✬✭✮✯ ",
}

DEFAULT_FONT = "/System/Library/Fonts/PingFang.ttc"


def find_font(preferred=None):
    import os
    import platform

    if preferred and os.path.isfile(preferred):
        return preferred

    # 优先从项目 fonts/ 目录查找
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
        # 找 fonts/ 下任意 ttf/otf/ttc 文件
        for f in sorted(os.listdir(local_fonts_dir)):
            if f.lower().endswith((".ttf", ".otf", ".ttc")):
                return os.path.join(local_fonts_dir, f)

    # 回退到系统字体
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

            # 交互命令
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
