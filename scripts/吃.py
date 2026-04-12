#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "吃"


def generate_eat(image_path: str, output_path: str):
    """生成吃东西动画GIF"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 处理用户图片
        user_img = BuildImage.open(image_path)
        processed_img = user_img.convert("RGBA").square().resize((34, 34))

        # 生成动画帧
        frames = []
        for i in range(3):
            # 加载背景帧
            frame_path = img_dir / f"{i}.png"
            if not frame_path.exists():
                raise FileNotFoundError(f"缺失第{i}帧背景图: {frame_path}")

            frame = BuildImage.open(frame_path)
            # 合成图片（固定位置）
            frame.paste(processed_img, (2, 38), below=True)
            frames.append(frame.image)

        # 直接利用原生方法保存为 GIF
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
        # 💡 核心修改：加上 from e 保留报错堆栈
        raise RuntimeError(f"生成失败: {str(e)}") from e


if __name__ == "__main__":
    import traceback

    try:
        # 这里进行你的参数长度判断
        if len(sys.argv) >= 3:
            # 调用你的生成函数
            generate_eat(sys.argv[1], sys.argv[2])
            sys.exit(0)
        else:
            print("错误：传入参数不足，需要 input 和 output 路径。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 【关键】把包含代码行数的详细报错打到标准错误流中，主进程才好收集
        err_msg = f"图像处理崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)