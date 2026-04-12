#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "可莉吃"

def generate_klee_eat(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        user_img = BuildImage.open(image_path)
        processed_img = user_img.convert("RGBA").square().resize((83, 83))

        locs = [
            (0, 174), (0, 174), (0, 174), (0, 174), (0, 174),
            (12, 160), (19, 152), (23, 148), (26, 145), (32, 140),
            (37, 136), (42, 131), (49, 127), (70, 126), (88, 128),
            (-30, 210), (-19, 207), (-14, 200), (-10, 188), (-7, 179),
            (-3, 170), (-3, 175), (-1, 174), (0, 174), (0, 174),
            (0, 174), (0, 174), (0, 174), (0, 174), (0, 174), (0, 174)
        ]

        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        frames = []
        for i in range(frame_count):
            frame = BuildImage.open(img_dir / f"{i}.png")
            coord = locs[i] if i < len(locs) else locs[-1]
            frame.paste(processed_img, coord, below=True)
            frames.append(frame.image)

        frames[0].save(
            output_path, format="GIF", save_all=True,
            append_images=frames[1:], duration=100, loop=0, disposal=2
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