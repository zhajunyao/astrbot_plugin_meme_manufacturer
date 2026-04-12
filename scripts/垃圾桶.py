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
    try:
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])
            if not input_file.exists():
                print(f"错误: 文件 {input_file} 不存在！", file=sys.stderr) # 【修复】暴露异常
                sys.exit(1)
            generate_trash(str(input_file), str(output_file))
            sys.exit(0)
        else:
            print("缺少参数！", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr) # 【修复】抛出异常给主进程
        sys.exit(1)