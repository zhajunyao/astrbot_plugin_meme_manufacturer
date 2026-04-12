#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "打拳"

def generate_punch(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        user_img = BuildImage.open(image_path).convert("RGBA")
        user_img = user_img.square().resize((260, 260))

        position_offsets = [
            (-50, 20), (-40, 10), (-30, 0), (-20, -10), (-10, -10), (0, 0),
            (10, 10), (20, 20), (10, 10), (0, 0), (-10, -10), (10, 0), (-30, 10)
        ]

        frames = []
        for frame_index in range(13):
            fist_path = img_dir / f"{frame_index}.png"
            if not fist_path.exists():
                raise FileNotFoundError(f"缺失第{frame_index}帧拳头素材: {fist_path}")

            fist_img = BuildImage.open(fist_path)
            frame = BuildImage.new("RGBA", fist_img.size, "white")

            x_offset, y_offset = position_offsets[frame_index]
            final_y = y_offset - 15

            frame.paste(user_img, (x_offset, final_y), alpha=True)
            frame.paste(fist_img, alpha=True)
            frames.append(frame.image)

        frames[0].save(
            output_path, format="GIF", save_all=True,
            append_images=frames[1:], duration=30, loop=0, disposal=2
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