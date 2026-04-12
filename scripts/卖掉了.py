#!/usr/bin/env python3
import os  # 💡 核心修改：将 os 移动到最顶部
import sys
from pathlib import Path
from PIL import Image, ImageSequence
from pil_utils import BuildImage

# 统一采用军火库标准路径定位到 data
script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "卖掉了"


def process_frame(frame_img: BuildImage, icon: BuildImage) -> Image.Image:
    """处理单帧：缩放、加遮罩、贴图标"""
    frame = frame_img.convert("RGBA")

    # 调整底图尺寸，保证短边为 600
    if frame.width > frame.height:
        frame = frame.resize_height(600)
    else:
        frame = frame.resize_width(600)

    # 添加半透明遮罩
    mask = BuildImage.new("RGBA", frame.size, (0, 0, 0, 64))
    frame.paste(mask, alpha=True)

    # 动态调整图标大小（底图宽度的 80%）
    target_w = int(frame.width * 0.8)
    resized_icon = icon.resize_width(target_w)

    # 居中贴上图标
    x = (frame.width - resized_icon.width) // 2
    y = (frame.height - resized_icon.height) // 2
    frame.paste(resized_icon, (x, y), alpha=True)

    return frame.image


def generate_sold_out(image_path: str, output_path_in: str):
    icon_path = img_dir / "0.png"
    if not icon_path.exists():
        raise FileNotFoundError(f"找不到图标文件 {icon_path}")

    icon = BuildImage.open(icon_path).convert("RGBA")

    output_base = os.path.splitext(output_path_in)[0]

    with Image.open(image_path) as im:
        # 判断是否为动图
        if getattr(im, "is_animated", False):
            output_path = output_base + ".gif"
            frames = []
            durations = []

            # 遍历每一帧
            for frame in ImageSequence.Iterator(im):
                p_frame = process_frame(BuildImage(frame.convert("RGBA")), icon)
                frames.append(p_frame)
                durations.append(im.info.get("duration", 100))

            # 使用原生 PIL 保存
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=im.info.get("loop", 0),
                disposal=2
            )
        else:
            output_path = output_base + ".png"
            final_img = process_frame(BuildImage(im.convert("RGBA")), icon)
            final_img.save(output_path, format="PNG")

    print(f"处理完成: {output_path}")


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