#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "催眠"

def generate_saimin(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到文件夹: {img_dir}")

    try:
        input_img = BuildImage.open(image_path)
    except Exception as e:
        raise RuntimeError(f"无法读取图片: {e}") from e

    frame_count = 0
    while (img_dir / f"{frame_count}.png").exists():
        frame_count += 1

    if frame_count == 0:
        raise FileNotFoundError(f"在 {img_dir} 缺少帧文件！")

    frame_files = [img_dir / f"{i}.png" for i in range(frame_count)]
    app_w, app_h = BuildImage.open(frame_files[0]).size
    img_w, img_h = input_img.size

    # 计算调整尺寸
    if img_w > img_h:
        frame_h = app_h
        frame_w = round(frame_h * img_w / img_h)
    else:
        frame_w = app_w
        frame_h = round(frame_w * img_h / img_w)

    try:
        frames = []
        # 【修复】将尺寸调整移出循环，防止无意义重复渲染
        resized = input_img.resize((frame_w, frame_h), keep_ratio=True).convert("RGBA")

        for frame_file in frame_files:
            frame = Image.new("RGBA", (app_w, app_h))
            frame.paste(resized.image, (0, app_h - frame_h), resized.image)
            overlay = BuildImage.open(frame_file).convert("RGBA")
            frame.paste(overlay.image, (0, 0), overlay.image)
            frames.append(frame)

        frames[0].save(
            output_path, format="GIF", save_all=True,
            append_images=frames[1:], duration=30, loop=0, disposal=2
        )
        return True
    except Exception as e:
        raise RuntimeError(f"动图生成出错: {e}") from e


if __name__ == "__main__":
    import traceback

    try:
        # 这里进行你的参数长度判断
        if len(sys.argv) >= 3:
            # 调用你的生成函数
            generate_saimin(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print("错误：传入参数不足，需要 input 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 【关键】把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)