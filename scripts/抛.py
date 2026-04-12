#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "抛"


def generate_throw(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        user_img = BuildImage.open(image_path).convert("RGBA").circle()

        locs_config = [
            [(32, 32, 108, 36)],
            [(32, 32, 122, 36)],
            [],
            [(123, 123, 19, 129)],
            [(185, 185, -50, 200), (33, 33, 289, 70)],
            [(32, 32, 280, 73)],
            [(35, 35, 259, 31)],
            [(175, 175, -50, 220)],
        ]

        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        if frame_count > len(locs_config):
            print("注意：素材帧数多于配置，可能被截断", file=sys.stderr)  # 💡 修复：静默截断增加警告提示

        limit = min(frame_count, len(locs_config))

        frames = []
        for frame_index in range(limit):
            frame_path = img_dir / f"{frame_index}.png"
            frame = BuildImage.open(frame_path)

            for (w, h, x, y) in locs_config[frame_index]:
                resized_img = user_img.resize((w, h))
                frame.paste(resized_img, (x, y), alpha=True)

            frames.append(frame.image)

        frames[0].save(
            output_path, format="GIF", save_all=True,
            append_images=frames[1:], duration=100, loop=0, disposal=2
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
            generate_throw(str(input_file), str(output_file))
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        sys.exit(1)