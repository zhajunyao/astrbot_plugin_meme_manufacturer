#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "吸"

def generate_suck(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        user_img = BuildImage.open(image_path).convert("RGBA").square()
        locs = [
            (82, 100, 130, 119), (82, 94, 126, 125), (82, 120, 128, 99), (81, 164, 132, 55),
            (79, 163, 132, 55), (82, 140, 127, 79), (83, 152, 125, 67), (75, 157, 140, 62),
            (72, 165, 144, 54), (80, 132, 128, 87), (81, 127, 127, 92), (79, 111, 132, 108)
        ]

        frames = []
        for i in range(12):
            bg_path = img_dir / f"{i}.png"
            if not bg_path.exists():
                raise FileNotFoundError(f"缺失素材图片: {bg_path.name}")
            bg = BuildImage.open(bg_path)
            frame = BuildImage.new("RGBA", bg.size, "white")
            x, y, w, h = locs[i]

            frame.paste(user_img.resize((w, h)), (x, y), alpha=True)
            frame.paste(bg, alpha=True)
            frames.append(frame.image)

        frames[0].save(
            output_path, format="GIF", save_all=True,
            append_images=frames[1:], duration=80, loop=0, disposal=2
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
            generate_suck(str(input_file), str(output_file))
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)