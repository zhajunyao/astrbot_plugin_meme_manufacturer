#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "搓"


def generate_twist(image_path: str, output_path: str):
    """生成搓动动画GIF并直接保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理图片：转为正方形并缩放至 78x78
        img = BuildImage.open(image_path).convert("RGBA")
        img = img.square().resize((78, 78))

        # 帧位置及旋转参数 (x, y, 旋转角度)
        locs = [
            (25, 66, 0), (25, 66, 60), (23, 68, 120),
            (20, 69, 180), (22, 68, 240)
        ]

        frames: List[IMG] = []
        for i in range(5):
            frame_file = img_dir / f"{i}.png"
            if not frame_file.exists():
                raise FileNotFoundError(f"缺失帧图片: {frame_file.name}")

            frame = BuildImage.open(frame_file)
            x, y, angle = locs[i]

            # 旋转并粘贴图片，below=True 表示垫在手部素材下方
            rotated_img = img.rotate(angle)
            frame.paste(rotated_img, (x, y), below=True)
            frames.append(frame.image)

        # 💡 核心优化：直接利用原生方法保存为 GIF，抛弃外部依赖
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
            generate_twist(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print("错误：传入参数不足，需要 input 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 【关键】把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)