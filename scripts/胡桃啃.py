#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "胡桃啃"


def generate_hutao_bite(image_path: str, output_path: str):
    """生成胡桃啃咬动画GIF并保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片
        user_img = BuildImage.open(image_path)
        # 原逻辑：转为正方形并缩放为 100x100
        processed_img = user_img.convert("RGBA").square().resize((100, 100))

        # 位置参数 (w, h, x, y)
        locs = [(108, 234, 98, 101), (108, 237, 96, 100)]

        # 动态检测帧数保护
        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        limit = min(frame_count, len(locs))

        # 生成动画帧
        frames: List[IMG] = []
        for i in range(limit):
            # 加载背景帧
            frame_file = img_dir / f"{i}.png"
            frame = BuildImage.open(frame_file)
            w, h, x, y = locs[i]

            # 调整并合成图片，垫在胡桃立绘下方
            resized_img = processed_img.resize((w, h))
            frame.paste(resized_img, (x, y), below=True)
            frames.append(frame.image)

        # 原生保存为 GIF
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=100,  # 0.1秒 = 100毫秒
            loop=0,
            disposal=2
        )
        return True

    except Exception as e:
        raise RuntimeError(f"生成失败: {str(e)}")


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