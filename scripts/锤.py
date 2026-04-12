#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "锤"

def generate_thump(image_path: str, output_path: str):
    """ 生成捶打动画GIF并直接保存 """
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载并处理用户图片：强制转换为正方形
        img = BuildImage.open(image_path).convert("RGBA").square()

        # 坐标和尺寸 (x, y, w, h)
        locs = [(65, 128, 77, 72), (67, 128, 73, 72), (54, 139, 94, 61), (57, 135, 86, 65)]

        # 动态检测可用帧数，以防素材不足报错
        frame_count = 0
        while (img_dir / f"{frame_count}.png").exists():
            frame_count += 1

        if frame_count == 0:
            raise FileNotFoundError(f"在 {img_dir} 里连一张图片都没找到！")

        limit = min(frame_count, len(locs))

        frames: List[IMG] = []
        for i in range(limit):
            frame = BuildImage.open(img_dir / f"{i}.png")

            x, y, w, h = locs[i]
            # 将用户头像按尺寸缩小，并垫在锤子和手(底层)的下方
            frame.paste(img.resize((w, h)), (x, y), below=True)
            frames.append(frame.image)

        # 💡 核心优化：直接利用原生方法保存为 GIF，抛弃外部依赖
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=40,  # 0.04秒 = 40毫秒，速度非常快，打击感很强
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