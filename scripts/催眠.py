#!/usr/bin/env python3
import sys
from pathlib import Path
from PIL import Image
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
img_dir = script_dir.parent / "data" / "催眠"


def generate_saimin(image_path: str, output_path: str):
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到素材文件夹，请确认路径: {img_dir}")

    # 1. 加载输入图片
    try:
        input_img = BuildImage.open(image_path)
    except Exception as e:
        raise RuntimeError(f"无法读取用户头像: {e}") from e

    # 2. 动态获取帧数
    frame_count = 0
    while (img_dir / f"{frame_count}.png").exists():
        frame_count += 1

    if frame_count == 0:
        raise FileNotFoundError(f"素材文件夹 {img_dir} 中缺失帧图片（如 0.png）")

    frame_files = [img_dir / f"{i}.png" for i in range(frame_count)]

    # 3. 准备尺寸参数
    app_w, app_h = BuildImage.open(frame_files[0]).size
    img_w, img_h = input_img.size

    # 计算自适应缩放后的尺寸
    if img_w > img_h:
        frame_h = app_h
        frame_w = round(frame_h * img_w / img_h)
    else:
        frame_w = app_w
        frame_h = round(frame_w * img_h / img_w)

    try:
        # 🚀 【核心性能优化】：将缩放操作移出循环，仅执行一次
        resized_user_img = input_img.resize((frame_w, frame_h), keep_ratio=True).convert("RGBA")

        frames = []
        for frame_file in frame_files:
            # 创建画布
            frame = Image.new("RGBA", (app_w, app_h))

            # 叠放用户头像（靠底部居中）
            frame.paste(resized_user_img.image, (0, app_h - frame_h), resized_user_img.image)

            # 叠放催眠螺旋特效层
            overlay = BuildImage.open(frame_file).convert("RGBA")
            frame.paste(overlay.image, (0, 0), overlay.image)

            frames.append(frame)

        # 4. 保存 GIF
        frames[0].save(
            output_path,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=30,
            loop=0,
            disposal=2
        )
        return True
    except Exception as e:
        raise RuntimeError(f"GIF合成失败: {e}") from e


if __name__ == "__main__":
    import traceback

    try:
        # 参数校验：输入路径, 输出路径
        if len(sys.argv) >= 3:
            input_file = Path(sys.argv[1])
            output_file = Path(sys.argv[2])

            if not input_file.exists():
                print(f"错误: 输入文件 {input_file} 不存在！", file=sys.stderr)
                sys.exit(1)

            # 调用真正的处理函数
            generate_saimin(str(input_file), str(output_file))
            sys.exit(0)
        else:
            print("错误：缺少必要的命令行参数。", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # 打印详细错误到 stderr，供插件主程序捕获
        err_msg = f"催眠脚本崩溃: {str(e)}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        sys.exit(1)