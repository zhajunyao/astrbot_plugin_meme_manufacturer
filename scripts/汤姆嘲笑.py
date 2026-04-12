#!/usr/bin/env python3
import sys
from pathlib import Path
from io import BytesIO
from typing import Callable

from pil_utils import BuildImage
from meme_generator.utils import FrameAlignPolicy, make_gif_or_combined_gif

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "汤姆嘲笑"


def generate_tom_tease(image_path: str) -> BytesIO:
    """生成汤姆嘲笑动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    img = BuildImage.open(image_path)

    # 💡 核心修复：把 list[BuildImage] 改成单张 BuildImage，提前解决报错隐患
    def frame_maker(i: int):
        def make_frame(base_img: BuildImage) -> BuildImage:
            # 处理用户图片
            processed_img = base_img.convert("RGBA").resize((400, 350), keep_ratio=True)
            processed_img = processed_img.perspective(((0, 100), (290, 0), (290, 370), (0, 335)))

            # 加载当前帧背景
            bg = BuildImage.open(img_dir / f"{i}.png")

            # 合成帧
            frame = BuildImage.new("RGBA", bg.size, "white")
            frame.paste(bg).paste(processed_img, (258, -12), below=True)
            return frame

        return make_frame

    # 生成GIF数据
    return make_gif_or_combined_gif(
        img,  # 💡 核心修复：直接传 img 对象，而不是 [img] 列表
        frame_maker,
        11,
        0.2,
        FrameAlignPolicy.extend_first
    )


if __name__ == "__main__":
    import traceback

    try:
        # 这里进行你的参数长度判断
        if len(sys.argv) >= 3:
            # 调用你的生成函数
            generate_tom_tease(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print("错误：传入参数不足，需要 input 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 【关键】把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)