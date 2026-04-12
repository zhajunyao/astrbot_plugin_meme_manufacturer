#!/usr/bin/env python3
import sys
from pathlib import Path
from pil_utils import BuildImage

script_dir = Path(__file__).parent.resolve()
# 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
img_dir = script_dir.parent / "data" / "泉此方看"


def generate_konata_watch(image_path: str, output_path: str):
    """生成泉此方观看效果图并保存"""
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    try:
        # 加载背景模板
        frame_file = img_dir / "0.png"
        if not frame_file.exists():
            raise FileNotFoundError(f"缺失背景底图: {frame_file.name}")
        frame = BuildImage.open(frame_file)

        # 处理用户图片
        user_img = BuildImage.open(image_path).convert("RGBA")
        processed_img = user_img.resize((270, 200), keep_ratio=True)

        # 💡 保留原版精妙的透视变换坐标
        perspective_points = ((0, 1), (275, 0), (273, 202), (2, 216))
        transformed_img = processed_img.perspective(perspective_points)

        # 合成最终图片，置于底层
        final_img = frame.copy()
        final_img.paste(transformed_img, (50, 188), below=True)

        # 💡 核心修复：原生保存为 PNG，替代 BytesIO 方案
        final_img.image.save(output_path, format="PNG")
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