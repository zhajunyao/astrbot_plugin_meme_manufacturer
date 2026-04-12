#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "拍"

def generate_pat(image_path: str, output_path: str):
    """生成拍打动画GIF并保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户图片为正方形
        user_img = BuildImage.open(image_path).convert("RGBA").square()

        # 位置参数 (x, y, w, h)
        locs = [(11, 73, 106, 100), (8, 79, 112, 96)]

        # 生成基础帧缓存
        img_frames: List[IMG] = []
        for i in range(10):
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失素材图片: {frame_path.name}")

            frame = BuildImage.open(frame_path)
            # 根据帧索引选择不同的位置参数
            x, y, w, h = locs[1] if i == 2 else locs[0]
            # 合成图片，置于底层
            frame.paste(user_img.resize((w, h)), (x, y), below=True)
            img_frames.append(frame.image)

        # 💡 保留原版精妙的帧序列逻辑
        seq = [0, 1, 2, 3, 1, 2, 3, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0, 0, 0, 4, 5, 5, 5, 6, 7, 8, 9]

        # 组合最终帧
        final_frames = [img_frames[n] for n in seq]

        # 💡 核心修复：原生保存为 GIF，替代 save_gif
        final_frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=final_frames[1:],
            duration=85,  # 0.085秒 = 85毫秒
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