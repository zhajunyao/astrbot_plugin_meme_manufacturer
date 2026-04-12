#!/usr/bin/env python3
import sys
from pathlib import Path
from io import BytesIO
from typing import List
from PIL.Image import Image as IMG
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "抱抱"


def generate_hug(user_path: str, self_path: str, output_path: str):
    """生成拥抱动画GIF并直接保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户头像 (对方)
        user_head = BuildImage.open(user_path).convert("RGBA").circle().resize((105, 105))
        # 处理自己头像 (发送者)
        self_head = BuildImage.open(self_path).convert("RGBA").circle().resize((120, 120))

        # 位置和旋转参数
        user_locs = [
            (108, 15), (107, 14), (104, 16), (102, 14), (104, 15),
            (108, 15), (108, 15), (103, 16), (102, 15), (104, 14)
        ]
        self_locs = [
            (78, 120), (115, 130), (0, 0), (110, 100), (80, 100),
            (75, 115), (105, 127), (0, 0), (110, 98), (80, 105)
        ]
        rotate_num = [-48, -18, 0, 38, 31, -43, -22, 0, 34, 35]

        # 生成动画帧
        frames: List[IMG] = []
        for i in range(10):
            frame = BuildImage.open(img_dir / f"{i}.png")

            # 合成对方头像
            frame.paste(user_head, user_locs[i], below=True)

            # 处理并合成自己头像
            rotated_self = self_head.rotate(rotate_num[i], expand=True)
            frame.paste(rotated_self, self_locs[i], below=True)

            frames.append(frame.image)

        # 直接保存到指定路径
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=50,
            loop=0,
            disposal=2
        )
        return True

    except Exception as e:
        raise RuntimeError(f"生成失败: {str(e)}")


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 4:
            # 修改参数映射顺序，确保“你”是主动方
            sender_p = sys.argv[1]  # 发送者头像
            target_p = sys.argv[2]  # 对方头像
            out_p = sys.argv[3]     # 输出路径

            generate_hug(user_path=target_p, self_path=sender_p, output_path=out_p)
            sys.exit(0)
        else:
            print("错误：传入参数不足，双人表情包需要 sender_img, target_img 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)