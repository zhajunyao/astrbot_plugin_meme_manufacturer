#!/usr/bin/env python3
import sys
import io
from pathlib import Path
from PIL import Image
from pil_utils import BuildImage
from meme_generator.utils import FrameAlignPolicy, Maker, make_gif_or_combined_gif


def generate_shiroko_pero(image_path: str, output_path: str = "output.gif"):
    # 💡 核心修复：把路径获取和图片加载放到函数内部！避免 import 阶段报错
    script_dir = Path(__file__).parent.resolve()
    # 💡 这里的 "具体插件名" 必须和 data/ 下的文件夹名字一模一样
    img_dir = script_dir.parent / "data" / "白子舔"

    # 加个保险：如果连 images 文件夹都找不到，给出人类能看懂的报错
    if not img_dir.exists():
        raise FileNotFoundError(f"找不到 images 文件夹，请确认它必须放在这个路径下: {img_dir}")

    mask = BuildImage.open(img_dir / "mask.png").convert("RGBA")
    user_image = BuildImage.open(image_path).convert("RGBA")

    def maker(i) -> Maker:
        def make(img: BuildImage) -> BuildImage:
            suika = img.resize((245, 245), keep_ratio=True)
            frame = BuildImage.open(img_dir / f"{i}.png").convert("RGBA")
            suika_mask = BuildImage.new("RGBA", (245, 245), (0, 0, 0, 0))
            suika_mask.image.paste(suika.image, (0, 0), mask.image)
            frame.paste(suika_mask, (105, 178), below=True)
            return frame

        return make

    result = make_gif_or_combined_gif(
        user_image,
        maker,
        4,
        0.06,
        FrameAlignPolicy.extend_loop
    )

    if isinstance(result, BuildImage):
        result.save(output_path)
    else:
        gif_bytes = result.getvalue() if isinstance(result, io.BytesIO) else result
        with open(output_path, "wb") as f:
            f.write(gif_bytes)

    print(f"生成成功！文件已保存至: {Path(output_path).resolve()}")


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