#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image


def resize_cover(img: Image.Image, target_size: tuple) -> Image.Image:
    """【修复】正确实现的保持比例并居中裁剪(Cover)"""
    img_width, img_height = img.size
    target_width, target_height = target_size

    img_ratio = img_width / img_height
    target_ratio = target_width / target_height

    if target_ratio > img_ratio:
        new_width = target_width
        new_height = int(target_width / img_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * img_ratio)

    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 【修复】强制转为 int，防止由于浮点数产生的亚像素异常报错
    left = int((new_width - target_width) / 2)
    top = int((new_height - target_height) / 2)
    right = left + target_width
    bottom = top + target_height

    return resized.crop((left, top, right, bottom))


def process_image(input_path: str, output_path: str):
    script_dir = Path(__file__).parent.resolve()
    frame_dir = script_dir.parent / "data" / "射"

    if not frame_dir.exists():
        raise FileNotFoundError(f"找不到文件夹: {frame_dir}")

    frame_files = [frame_dir / f"{i:02d}.png" for i in range(13)]

    try:
        with Image.open(input_path) as raw_user_img:
            user_img = raw_user_img.convert("RGB")
    except Exception as e:
        raise RuntimeError(f"图片加载失败: {e}") from e

    frames = []
    for frame_file in frame_files:
        with Image.open(frame_file) as raw_frame:
            frame = raw_frame.convert("RGBA")

        resized_user = resize_cover(user_img, frame.size)

        composite = Image.new("RGBA", frame.size)
        composite.paste(resized_user, (0, 0))
        composite.alpha_composite(frame)
        frames.append(composite.convert("RGB"))

    frames[0].save(
        output_path, format="GIF", save_all=True,
        append_images=frames[1:], duration=150, loop=0, disposal=2
    )


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 3:
            process_image(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)  # 暴露错误
        sys.exit(1)