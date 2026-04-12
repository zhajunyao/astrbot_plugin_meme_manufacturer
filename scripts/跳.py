#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "跳"


def generate_jump(image_path: str, output_path: str):
    """生成跳跃动画GIF并直接保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户图片为圆形
        user_img = BuildImage.open(image_path)
        processed_img = user_img.convert("RGBA").circle().resize((40, 40))

        # 跳跃轨迹坐标
        positions = [
            (15, 50), (13, 43), (15, 23), (14, 4),
            (16, -3), (16, -4), (14, 4), (15, 31)
        ]

        # 生成动画帧
        frames = []
        for i in range(8):
            # 加载背景帧
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失第{i}帧背景图: {frame_path}")

            frame = BuildImage.open(frame_path)
            x, y = positions[i]

            # 合成图片
            frame.paste(processed_img, (x, y), alpha=True)
            frames.append(frame.image)

        # 直接原生保存到指定路径，替代原先的 BytesIO
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=50,  # 0.05秒 = 50毫秒
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