#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage, Text2Image

def convert_to_charpic(image_path: str, output_path: str):
    str_map = "@@$$&B88QMMGW##EE93SPPDOOU**==()+^,\"--''.  "
    num = len(str_map)

    t2m = Text2Image.from_text("@", 15)
    ratio = t2m.width / t2m.height

    img = BuildImage.open(image_path).convert("RGBA").resize_width(150).convert("L")
    img = img.resize((img.width, round(img.height * ratio)))

    lines = []
    for y in range(img.height):
        line = []
        for x in range(img.width):
            gray = img.image.getpixel((x, y))
            line.append(str_map[int(num * gray / 256)] if gray != 0 else " ")
        lines.append("".join(line))
    text = "\n".join(lines)

    char_image = Text2Image.from_text(text, 15).to_image(bg_color="white")
    char_image.save(output_path)
    print(f"字符画已保存至: {output_path}")


if __name__ == "__main__":
    import traceback

    try:
        # 这里进行你的参数长度判断
        if len(sys.argv) >= 3:
            # 调用你的生成函数
            generate_something(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print("错误：传入参数不足，需要 input 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 【关键】把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)