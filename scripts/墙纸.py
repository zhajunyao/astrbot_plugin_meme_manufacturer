#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "墙纸"

def generate_wallpaper(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        user_img = BuildImage.open(image_path).convert("RGBA")
        user_img = user_img.resize((515, 383), keep_ratio=True)

        frames = []
        for i in range(8):
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失背景帧: {i}.png")
            frames.append(BuildImage.open(frame_path).image)

        for i in range(8, 20):
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失合成帧: {i}.png")

            frame = BuildImage.open(frame_path)
            frame.paste(user_img, (176, -9), below=True)
            frames.append(frame.image)

        frames[0].save(
            output_path, format="GIF", save_all=True,
            append_images=frames[1:], duration=70, loop=0, disposal=2
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
                sys.exit(1)
            generate_wallpaper(str(input_file), str(output_file))
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        sys.exit(1)