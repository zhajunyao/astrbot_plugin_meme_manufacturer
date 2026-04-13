import base64
import logging
import os
import requests
import shutil
import subprocess
import sys
import tempfile
import time
from astrbot.api.all import * # type: ignore

logger = logging.getLogger("astrbot")
TEMP_ROOT_NAME = "astrbot_plugin_meme_manufacturer"
STALE_JOB_MAX_AGE_SECONDS = 6 * 60 * 60
DOWNLOAD_TIMEOUT = (5, 15)
SCRIPT_TIMEOUT = 120

@register("表情包制造厂", "神秘嘉宾", "将QQ群友头像做成表情包的工具。可以做成gif，也可以做成静态表情，内置多种表情包，水群利器", "1.0")
class MemeArsenal(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config  # 把 AstrBot 喂给你的面板配置接住！
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = os.path.join(self.plugin_dir, "scripts")
        self.temp_root = os.path.join(tempfile.gettempdir(), TEMP_ROOT_NAME)
        os.makedirs(self.temp_root, exist_ok=True)
        self._cleanup_stale_jobs()

    def _cleanup_stale_jobs(self):
        now = time.time()
        for name in os.listdir(self.temp_root):
            path = os.path.join(self.temp_root, name)
            try:
                modified_at = os.path.getmtime(path)
            except OSError:
                continue

            if now - modified_at <= STALE_JOB_MAX_AGE_SECONDS:
                continue

            self._remove_path(path)

    def _remove_path(self, path):
        if not path:
            return

        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except FileNotFoundError:
            return
        except Exception as exc:
            logger.warning("清理临时文件失败: %s", exc)

    def _make_job_dir(self, cmd: str) -> str:
        safe_cmd = "".join(ch if ch.isalnum() else "_" for ch in cmd).strip("_") or "meme"
        return tempfile.mkdtemp(prefix=f"{safe_cmd}_", dir=self.temp_root)

    def _normalize_local_path(self, source: str) -> str:
        path = source
        if path.startswith("file://"):
            path = path[7:]
            if os.name == "nt" and len(path) > 2 and path[0] == "/" and path[2] == ":":
                path = path[1:]
        return path

    def _save_image_source(self, source: str, destination: str):
        if source.startswith(("http://", "https://")):
            response = requests.get(source, timeout=DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            with open(destination, "wb") as file:
                file.write(response.content)
            return

        if source.startswith("base64://"):
            payload = source.removeprefix("base64://")
            with open(destination, "wb") as file:
                file.write(base64.b64decode(payload))
            return

        local_path = self._normalize_local_path(source)
        if os.path.exists(local_path):
            shutil.copyfile(local_path, destination)
            return

        raise FileNotFoundError(f"无法读取图片源：{source}")

    def _pick_target_source(self, event):
        for comp in event.message_obj.message:
            if isinstance(comp, Image):
                if comp.url:
                    return comp.url
                if comp.file:
                    return comp.file

        for comp in event.message_obj.message:
            if isinstance(comp, At) and str(comp.qq) != str(event.get_self_id()):
                return f"http://q1.qlogo.cn/g?b=qq&nk={comp.qq}&s=640"

        return None

    def _find_output_file(self, out_base: str, preferred_ext: str) -> str:
        checked = set()
        for ext in [preferred_ext, "gif", "png"]:
            if ext in checked:
                continue
            checked.add(ext)

            candidate = f"{out_base}.{ext}"
            if os.path.exists(candidate):
                return candidate

        return ""

    def _build_image_result(self, event, output_path: str):
        with open(output_path, "rb") as file:
            image_bytes = file.read()

        result = event.make_result()
        result.chain = [Image.fromBytes(image_bytes)]
        return result

    async def _handle(self, event, cmd, script, ext="gif", msg="正在生成...", is_double=False, extra_args=None):
        """通用表情包处理逻辑"""

        # 🛠️ --- 核心升级：极简配置读取 --- 🛠️
        # 直接从注入的 config 字典中拿，默认值为 True
        is_enabled = self.config.get(cmd, True)

        # 严格判断关闭状态
        if is_enabled is False or str(is_enabled).lower() == "false" or is_enabled == 0:
            yield event.plain_result(f"❌ 提示：管理员已在后台禁用了「{cmd}」功能哦~")
            return
        # 🛠️ ------------------------------------ 🛠️

        extra_args = extra_args or []
        target_source = self._pick_target_source(event)

        if not target_source:
            yield event.plain_result(f"提示：/{cmd} 指令需要带图发送，或者 @你要处理的人 哦！")
            return

        yield event.plain_result(msg)
        job_dir = self._make_job_dir(cmd)
        in_p = os.path.join(job_dir, "target.png")
        out_base = os.path.join(job_dir, "result")

        try:
            # 下载目标图
            self._save_image_source(target_source, in_p)

            # 基础运行参数
            args = [sys.executable, os.path.join(self.scripts_dir, script)]

            if is_double:  # 处理双人逻辑（例如贴贴）
                sender_p = os.path.join(job_dir, "sender.png")
                sender_id = event.get_sender_id()
                self._save_image_source(f"http://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=640", sender_p)
                args += [sender_p, in_p, out_base + "." + ext]
            else:
                args += [in_p, out_base + "." + ext]
            if extra_args:
                args.extend(extra_args)
            # 启动子进程处理
            res = subprocess.run(
                args,
                cwd=self.plugin_dir,
                capture_output=True,
                text=True,
                timeout=SCRIPT_TIMEOUT,
            )

            # 自动探测文件后缀（解决 卖掉了 等脚本生成 gif 或 png 的不确定性）
            final_out = self._find_output_file(out_base, ext)

            if res.returncode != 0:
                err = res.stderr.strip() or res.stdout.strip()
                yield event.plain_result(f"生成失败：\n{err}")
            elif final_out:
                yield self._build_image_result(event, final_out)
            else:
                yield event.plain_result("错误：脚本未生成任何文件。")
        except subprocess.TimeoutExpired:
            yield event.plain_result("生成超时了，请换张图再试，或者稍后重试。")
        except requests.RequestException as exc:
            logger.warning("下载图片失败: %s", exc)
            yield event.plain_result("图片下载失败了，请稍后再试。")
        except Exception as e:
            logger.exception("插件逻辑出错")
            yield event.plain_result(f"插件逻辑出错：{str(e)}")
        finally:
            self._remove_path(job_dir)


    @command("泉此方看")
    async def cmd_1(self, event: AstrMessageEvent):
        async for r in self._handle(event, "泉此方看", "泉此方看.py", "png", "此方正在看..."): yield r

    @command("吸")
    async def cmd_2(self, event: AstrMessageEvent):
        async for r in self._handle(event, "吸", "吸.py", "gif", "正在发动黑洞..."): yield r

    @command("敲")
    async def cmd_3(self, event: AstrMessageEvent):
        async for r in self._handle(event, "敲", "敲.py", "gif", "当当当！"): yield r

    @command("墙纸")
    async def cmd_4(self, event: AstrMessageEvent):
        async for r in self._handle(event, "墙纸", "墙纸.py", "gif", "正在粉刷墙壁..."): yield r

    @command("抛")
    async def cmd_5(self, event: AstrMessageEvent):
        async for r in self._handle(event, "抛", "抛.py", "gif", "用力一扔！"): yield r

    @command("拍")
    async def cmd_6(self, event: AstrMessageEvent):
        async for r in self._handle(event, "拍", "拍.py", "gif", "无影手准备中..."): yield r

    @command("拿捏")
    async def cmd_7(self, event: AstrMessageEvent):
        async for r in self._handle(event, "拿捏", "拿捏.py", "gif", "尽在掌控..."): yield r

    @command("膜拜")
    async def cmd_8(self, event: AstrMessageEvent):
        async for r in self._handle(event, "膜拜", "膜拜.py", "gif", "大佬受我一拜！"): yield r

    @command("卖掉了")
    async def cmd_9(self, event: AstrMessageEvent):
        async for r in self._handle(event, "卖掉了", "卖掉了.py", "png", "成交！"): yield r

    @command("啾啾")
    async def cmd_10(self, event: AstrMessageEvent):
        async for r in self._handle(event, "啾啾", "啾啾.py", "gif", "Mua~"): yield r

    @command("紧贴")
    async def cmd_11(self, event: AstrMessageEvent):
        async for r in self._handle(event, "紧贴", "紧贴.py", "gif", "贴住了，贴得死死的！"): yield r

    @command("胡桃啃")
    async def cmd_12(self, event: AstrMessageEvent):
        async for r in self._handle(event, "胡桃啃", "胡桃啃.py", "gif", "胡桃牙痒痒了..."): yield r

    @command("搓")
    async def cmd_13(self, event: AstrMessageEvent):
        async for r in self._handle(event, "搓", "搓.py", "gif", "正在疯狂揉搓..."): yield r

    @command("锤")
    async def cmd_14(self, event: AstrMessageEvent):
        async for r in self._handle(event, "锤", "锤.py", "gif", "吃我一锤！"): yield r

    @command("舔屏")
    async def cmd_15(self, event: AstrMessageEvent):
        async for r in self._handle(event, "舔屏", "舔屏.py", "gif", "嘿嘿嘿..."): yield r

    @command("贴贴")
    async def cmd_16(self, event: AstrMessageEvent):
        async for r in self._handle(event, "贴贴", "贴贴.py", "gif", "飞扑贴贴！", is_double=True): yield r

    @command("伽波贴")
    async def cmd_17(self, event: AstrMessageEvent):
        async for r in self._handle(event, "伽波贴", "伽波贴.py", "gif", "伽波！"): yield r

    @command("催眠")
    async def cmd_18(self, event: AstrMessageEvent):
        async for r in self._handle(event, "催眠", "催眠.py", "gif", "注入暗示中..."): yield r

    @command("打拳")
    async def cmd_19(self, event: AstrMessageEvent):
        async for r in self._handle(event, "打拳", "打拳.py", "gif", "欧拉欧拉欧拉！"): yield r

    @command("可莉吃")
    async def cmd_20(self, event: AstrMessageEvent):
        async for r in self._handle(event, "可莉吃", "可莉吃.py", "gif", "可莉开饭啦！"): yield r

    @command("跳")
    async def cmd_21(self, event: AstrMessageEvent):
        async for r in self._handle(event, "跳", "跳.py", "gif", "跳一跳！"): yield r

    @command("撸")
    async def cmd_22(self, event: AstrMessageEvent):
        # 默认模式，额外传个 "1"
        async for r in self._handle(event, "撸", "撸.py", "gif", "正在加速...", extra_args=["1"]): yield r

    @command("双手撸")
    async def cmd_22_1(self, event: AstrMessageEvent):
        # 强制双手，传 "1"
        async for r in self._handle(event, "双手撸", "撸.py", "gif", "双手加速...", extra_args=["1"]): yield r

    @command("单手撸")
    async def cmd_22_2(self, event: AstrMessageEvent):
        # 强制单手，传 "2"
        async for r in self._handle(event, "单手撸", "撸.py", "gif", "单手加速...", extra_args=["2"]): yield r

    @command("射")
    async def cmd_23(self, event: AstrMessageEvent):
        async for r in self._handle(event, "射", "射.py", "gif", "准备击中..."): yield r

    @command("垃圾桶")
    async def cmd_24(self, event: AstrMessageEvent):
        async for r in self._handle(event, "垃圾桶", "垃圾桶.py", "gif", "回收废品中..."): yield r

    @command("顶")
    async def cmd_25(self, event: AstrMessageEvent):
        async for r in self._handle(event, "顶", "顶.py", "gif", "顶上去！"): yield r

    @command("科目三")
    async def cmd_26(self, event: AstrMessageEvent):
        async for r in self._handle(event, "科目三", "科目三.py", "gif", "社会摇准备..."): yield r

    @command("砸")
    async def cmd_27(self, event: AstrMessageEvent):
        async for r in self._handle(event, "砸", "砸.py", "gif", "大锤搞定！"): yield r

    @command("摸头")
    async def cmd_28(self, event: AstrMessageEvent):
        async for r in self._handle(event, "摸头", "摸头.py", "gif", "乖乖，摸摸头..."): yield r

    @command("吃")
    async def cmd_29(self, event: AstrMessageEvent):
        async for r in self._handle(event, "吃", "吃.py", "gif", "阿姆阿姆..."): yield r

    @command("草神啃")
    async def cmd_30(self, event: AstrMessageEvent):
        async for r in self._handle(event, "草神啃", "草神啃.py", "gif", "纳西妲也想啃..."): yield r

    @command("抱大腿")
    async def cmd_31(self, event: AstrMessageEvent):
        async for r in self._handle(event, "抱大腿", "抱大腿.py", "gif", "求带飞！"): yield r

    @command("飞机杯")
    async def cmd_32(self, event: AstrMessageEvent):
        async for r in self._handle(event, "飞机杯", "飞机杯.py", "gif", "正在起飞！"): yield r

    @command("汤姆嘲笑")
    async def cmd_33(self, event: AstrMessageEvent):
        async for r in self._handle(event, "汤姆嘲笑", "汤姆嘲笑.py", "gif", "汤姆正在大笑..."): yield r

    @command("字符画")
    async def cmd_34(self, event: AstrMessageEvent):
        async for r in self._handle(event, "字符画", "字符画.py", "png", "正在转码..."): yield r

    @command("抱抱")
    async def cmd_35(self, event: AstrMessageEvent):
        async for r in self._handle(event, "抱抱", "抱抱.py", "gif", "抱一个~", is_double=True): yield r

    @command("白子舔")
    async def cmd_36(self, event: AstrMessageEvent):
        async for r in self._handle(event, "白子舔", "白子舔.py", "gif", "白子忍不住了..."): yield r

    @command("撅")
    async def cmd_37(self, event: AstrMessageEvent):
        async for r in self._handle(event, "撅", "撅.py", "gif", "小心后面！", is_double=True): yield r
