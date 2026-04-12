#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "垃圾桶"  # 【修复】改回正确的垃圾桶目录

def generate_trash(image_path: str, output_path: str): # 【修复】改名
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认路径: {img_dir}")

    try:
        user_img = BuildImage.open(image_path).convert("RGBA")
        processed_img = user_img.resize((75, 51), keep_ratio=True)

        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        frames = []
        for i in range(frame_count):
            frame_path = img_dir / f"{i}.png"
            frame = BuildImage.open(frame_path)
            frame.paste(processed_img, below=True)
            frames.append(frame.image)

        frames[0].save(
            output_path, format="GIF", save_all=True,
            append_images=frames[1:], duration=60, loop=0, disposal=2
        )
        return True

    except Exception as e:
        raise RuntimeError(f"生成失败: {str(e)}") from e


if __name__ == "__main__":
    import traceback

    try:
        # 这里进行你的参数长度判断
        if len(sys.argv) >= 3:
            # 调用你的生成函数
            generate_trash(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print("错误：传入参数不足，需要 input 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 【关键】把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)