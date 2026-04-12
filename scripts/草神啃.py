#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "草神啃"


def generate_nahida_bite(image_path: str, output_path: str):
    """生成纳西妲啃咬动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片
        user_img = BuildImage.open(image_path).convert("RGBA")
        user_img = user_img.resize((160, 140), keep_ratio=True)

        # 位置参数 (x, y, w, h)
        locs = [
            (123, 356, 158, 124), (123, 356, 158, 124), (123, 355, 158, 125),
            (122, 352, 159, 128), (122, 350, 159, 130), (122, 348, 159, 132),
            (122, 345, 159, 135), (121, 343, 160, 137), (121, 342, 160, 138),
            (121, 341, 160, 139), (121, 341, 160, 139), (121, 342, 160, 138),
            (121, 344, 160, 136), (121, 346, 160, 134), (122, 349, 159, 131),
            (122, 351, 159, 129), (122, 353, 159, 127), (123, 355, 158, 125),
        ]

        # 生成动画帧
        frames: List[IMG] = []
        for i in range(38):
            # 加载背景帧
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失素材图片: {frame_path.name}")

            frame = BuildImage.open(frame_path)

            # 应用位置参数（循环使用18个位置参数）
            x, y, w, h = locs[i % len(locs)]

            # 处理并合成用户图片
            resized_img = user_img.resize((w, h))
            frame.paste(resized_img, (x, y), below=True)

            frames.append(frame.image)

        # 直接保存到指定路径
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
            generate_nahida_bite(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print("错误：传入参数不足，需要 input 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 【关键】把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)