#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "敲"


def generate_knock(image_path: str, output_path: str):
    """生成敲击动画GIF并保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载用户图片并处理为正方形
        user_img = BuildImage.open(image_path).convert("RGBA").square()

        # 💡 保留原版精妙的 8 帧位置参数 (x, y, w, h)
        locs = [
            (60, 308, 210, 195), (60, 308, 210, 198), (45, 330, 250, 172), (58, 320, 218, 180),
            (60, 310, 215, 193), (40, 320, 250, 285), (48, 308, 226, 192), (51, 301, 223, 200)
        ]

        frames: List[IMG] = []
        for i in range(8):
            # 加载背景帧
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失第 {i} 帧背景图")

            frame = BuildImage.open(frame_path)
            x, y, w, h = locs[i]

            # 处理并合成用户图片，垫在素材下方
            resized_img = user_img.resize((w, h))
            frame.paste(resized_img, (x, y), below=True)

            frames.append(frame.image)

        # 💡 核心修复：原生保存为 GIF，替代 io 流方案
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=40,  # 0.04秒 = 40毫秒
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