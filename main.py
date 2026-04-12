import os
import sys
import tempfile
import uuid
import asyncio
import aiohttp
from urllib.parse import urlparse
from astrbot.api.all import *  # type: ignore
from astrbot.api.event import filter
from astrbot.api import logger


@register("表情包制造厂", "神秘嘉宾",
          "将QQ群友头像做成表情包的工具。可以做成gif，也可以做成静态表情，内置多种表情包，方便互动", "1.0")
class MemeArsenal(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = os.path.join(self.plugin_dir, "scripts")
        self.semaphore = asyncio.Semaphore(5)  # 限制最高并发数为5

    async def download_image(self, url: str, path: str):
        """异步下载图片的辅助方法，加入基础防SSRF检查"""
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("非法的图片地址，仅支持 HTTP/HTTPS 协议。")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    with open(path, "wb") as f:
                        f.write(await resp.read())
                else:
                    raise RuntimeError(f"状态码: {resp.status}")

    async def delayed_remove(self, filepath: str, delay: int = 15):
        await asyncio.sleep(delay)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

    async def _handle(self, event, cmd, script, ext="gif", msg="正在生成...", is_double=False, extra_args=None):
        is_enabled = self.config.get(cmd, True)

        if is_enabled is False or str(is_enabled).lower() == "false" or is_enabled == 0:
            yield event.plain_result(f"❌ 提示：管理员已在后台禁用了「{cmd}」功能哦~")
            return

        target_url = None

        for comp in event.message_obj.message:
            if isinstance(comp, Image):
                target_url = comp.url;
                break

        if not target_url and getattr(event.message_obj, 'quote', None):
            for comp in event.message_obj.quote.message:
                if isinstance(comp, Image):
                    target_url = comp.url;
                    break

        if not target_url:
            for comp in event.message_obj.message:
                if isinstance(comp, At) and str(comp.qq) != str(event.get_self_id()):
                    target_url = f"http://q1.qlogo.cn/g?b=qq&nk={comp.qq}&s=640";
                    break

        if not target_url:
            target_url = f"http://q1.qlogo.cn/g?b=qq&nk={event.get_sender_id()}&s=640"

        yield event.plain_result(msg)

        temp_dir = tempfile.gettempdir()
        req_id = uuid.uuid4().hex
        in_p = os.path.join(temp_dir, f"{cmd}_in_{req_id}.png")
        out_base = os.path.join(temp_dir, f"{cmd}_out_{req_id}")
        sender_p = os.path.join(temp_dir, f"sender_{req_id}.png") if is_double else None

        files_to_cleanup = [in_p]

        try:
            # 【修复】将网络下载阶段也纳入并发控制，防止请求洪峰
            async with self.semaphore:
                try:
                    await self.download_image(target_url, in_p)
                except Exception as e:
                    yield event.plain_result(f"❌ 目标头像下载失败: {e}")
                    return

                args = [sys.executable, os.path.join(self.scripts_dir, script)]

                if is_double:
                    sender_id = event.get_sender_id()
                    sender_url = f"http://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=640"
                    try:
                        # 【修复】如果发送者头像失败，拦截而不是带错执行
                        await self.download_image(sender_url, sender_p)
                        files_to_cleanup.append(sender_p)
                    except Exception as e:
                        yield event.plain_result(f"❌ 发送者头像下载失败: {e}")
                        return
                    args += [sender_p, in_p, out_base + "." + ext]
                else:
                    args += [in_p, out_base + "." + ext]

                if extra_args:
                    args.extend(extra_args)

                process = await asyncio.create_subprocess_exec(
                    *args, cwd=self.plugin_dir,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()  # 【修复】彻底回收僵尸进程
                    yield event.plain_result("❌ 错误：图片处理超时。")
                    return

                final_out = ""
                for e in [ext, "gif", "png"]:
                    possible_out = out_base + "." + e
                    if os.path.exists(possible_out):
                        final_out = possible_out
                        files_to_cleanup.append(final_out)
                        break

                if process.returncode != 0:
                    err = stderr.decode('utf-8', errors='ignore').strip() or stdout.decode('utf-8',
                                                                                           errors='ignore').strip()
                    yield event.plain_result(f"❌ 生成失败：\n{err}")
                elif final_out:
                    r = event.make_result()
                    r.chain = [Image.fromFileSystem(final_out)]
                    yield r
                else:
                    yield event.plain_result("❌ 错误：脚本未生成任何文件。请检查对应素材是否存在。")

        except Exception as e:
            logger.error(f"插件逻辑出错: {str(e)}")
            yield event.plain_result(f"❌ 插件内部逻辑错误：{str(e)}")

        finally:
            for f_path in files_to_cleanup:
                if f_path:
                    asyncio.create_task(self.delayed_remove(f_path))

    # ---------------- 注册的命令列表 ---------------- #

    @filter.command("泉此方看")
    async def cmd_1(self, event: AstrMessageEvent):
        async for r in self._handle(event, "泉此方看", "泉此方看.py", "png", "此方正在看..."): yield r

    @filter.command("吸")
    async def cmd_2(self, event: AstrMessageEvent):
        async for r in self._handle(event, "吸", "吸.py", "gif", "正在发动黑洞..."): yield r

    @filter.command("敲")
    async def cmd_3(self, event: AstrMessageEvent):
        async for r in self._handle(event, "敲", "敲.py", "gif", "当当当！"): yield r

    @filter.command("墙纸")
    async def cmd_4(self, event: AstrMessageEvent):
        async for r in self._handle(event, "墙纸", "墙纸.py", "gif", "正在粉刷墙壁..."): yield r

    @filter.command("抛")
    async def cmd_5(self, event: AstrMessageEvent):
        async for r in self._handle(event, "抛", "抛.py", "gif", "用力一扔！"): yield r

    @filter.command("拍")
    async def cmd_6(self, event: AstrMessageEvent):
        async for r in self._handle(event, "拍", "拍.py", "gif", "无影手准备中..."): yield r

    @filter.command("拿捏")
    async def cmd_7(self, event: AstrMessageEvent):
        async for r in self._handle(event, "拿捏", "拿捏.py", "gif", "尽在掌控..."): yield r

    @filter.command("膜拜")
    async def cmd_8(self, event: AstrMessageEvent):
        async for r in self._handle(event, "膜拜", "膜拜.py", "gif", "大佬受我一拜！"): yield r

    @filter.command("卖掉了")
    async def cmd_9(self, event: AstrMessageEvent):
        async for r in self._handle(event, "卖掉了", "卖掉了.py", "png", "成交！"): yield r

    @filter.command("啾啾")
    async def cmd_10(self, event: AstrMessageEvent):
        async for r in self._handle(event, "啾啾", "啾啾.py", "gif", "Mua~"): yield r

    @filter.command("紧贴")
    async def cmd_11(self, event: AstrMessageEvent):
        async for r in self._handle(event, "紧贴", "紧贴.py", "gif", "贴住了，贴得死死的！"): yield r

    @filter.command("胡桃啃")
    async def cmd_12(self, event: AstrMessageEvent):
        async for r in self._handle(event, "胡桃啃", "胡桃啃.py", "gif", "胡桃牙痒痒了..."): yield r

    @filter.command("搓")
    async def cmd_13(self, event: AstrMessageEvent):
        async for r in self._handle(event, "搓", "搓.py", "gif", "正在疯狂揉搓..."): yield r

    @filter.command("锤")
    async def cmd_14(self, event: AstrMessageEvent):
        async for r in self._handle(event, "锤", "锤.py", "gif", "吃我一锤！"): yield r

    @filter.command("舔屏")
    async def cmd_15(self, event: AstrMessageEvent):
        async for r in self._handle(event, "舔屏", "舔屏.py", "gif", "嘿嘿嘿..."): yield r

    @filter.command("贴贴")
    async def cmd_16(self, event: AstrMessageEvent):
        async for r in self._handle(event, "贴贴", "贴贴.py", "gif", "飞扑贴贴！", is_double=True): yield r

    @filter.command("伽波贴")
    async def cmd_17(self, event: AstrMessageEvent):
        async for r in self._handle(event, "伽波贴", "伽波贴.py", "gif", "伽波！"): yield r

    @filter.command("催眠")
    async def cmd_18(self, event: AstrMessageEvent):
        async for r in self._handle(event, "催眠", "催眠.py", "gif", "注入暗示中..."): yield r

    @filter.command("打拳")
    async def cmd_19(self, event: AstrMessageEvent):
        async for r in self._handle(event, "打拳", "打拳.py", "gif", "欧拉欧拉欧拉！"): yield r

    @filter.command("可莉吃")
    async def cmd_20(self, event: AstrMessageEvent):
        async for r in self._handle(event, "可莉吃", "可莉吃.py", "gif", "可莉开饭啦！"): yield r

    @filter.command("跳")
    async def cmd_21(self, event: AstrMessageEvent):
        async for r in self._handle(event, "跳", "跳.py", "gif", "跳一跳！"): yield r

    @filter.command("撸")
    async def cmd_22(self, event: AstrMessageEvent):
        async for r in self._handle(event, "撸", "撸.py", "gif", "正在加速...", extra_args=["1"]): yield r

    @filter.command("双手撸")
    async def cmd_22_1(self, event: AstrMessageEvent):
        async for r in self._handle(event, "双手撸", "撸.py", "gif", "双手加速...", extra_args=["1"]): yield r

    @filter.command("单手撸")
    async def cmd_22_2(self, event: AstrMessageEvent):
        async for r in self._handle(event, "单手撸", "撸.py", "gif", "单手加速...", extra_args=["2"]): yield r

    @filter.command("射")
    async def cmd_23(self, event: AstrMessageEvent):
        async for r in self._handle(event, "射", "射.py", "gif", "准备击中..."): yield r

    @filter.command("垃圾桶")
    async def cmd_24(self, event: AstrMessageEvent):
        async for r in self._handle(event, "垃圾桶", "垃圾桶.py", "gif", "回收废品中..."): yield r

    @filter.command("顶")
    async def cmd_25(self, event: AstrMessageEvent):
        async for r in self._handle(event, "顶", "顶.py", "gif", "顶上去！"): yield r

    @filter.command("科目三")
    async def cmd_26(self, event: AstrMessageEvent):
        async for r in self._handle(event, "科目三", "科目三.py", "gif", "社会摇准备..."): yield r

    @filter.command("砸")
    async def cmd_27(self, event: AstrMessageEvent):
        async for r in self._handle(event, "砸", "砸.py", "gif", "大锤搞定！"): yield r

    @filter.command("摸头")
    async def cmd_28(self, event: AstrMessageEvent):
        async for r in self._handle(event, "摸头", "摸头.py", "gif", "乖乖，摸摸头..."): yield r

    @filter.command("吃")
    async def cmd_29(self, event: AstrMessageEvent):
        async for r in self._handle(event, "吃", "吃.py", "gif", "阿姆阿姆..."): yield r

    @filter.command("草神啃")
    async def cmd_30(self, event: AstrMessageEvent):
        async for r in self._handle(event, "草神啃", "草神啃.py", "gif", "纳西妲也想啃..."): yield r

    @filter.command("抱大腿")
    async def cmd_31(self, event: AstrMessageEvent):
        async for r in self._handle(event, "抱大腿", "抱大腿.py", "gif", "求带飞！"): yield r

    @filter.command("飞机杯")
    async def cmd_32(self, event: AstrMessageEvent):
        async for r in self._handle(event, "飞机杯", "飞机杯.py", "gif", "正在起飞！"): yield r

    @filter.command("汤姆嘲笑")
    async def cmd_33(self, event: AstrMessageEvent):
        async for r in self._handle(event, "汤姆嘲笑", "汤姆嘲笑.py", "gif", "汤姆正在大笑..."): yield r

    @filter.command("字符画")
    async def cmd_34(self, event: AstrMessageEvent):
        async for r in self._handle(event, "字符画", "字符画.py", "png", "正在转码..."): yield r

    @filter.command("抱抱")
    async def cmd_35(self, event: AstrMessageEvent):
        async for r in self._handle(event, "抱抱", "抱抱.py", "gif", "抱一个~", is_double=True): yield r

    @filter.command("白子舔")
    async def cmd_36(self, event: AstrMessageEvent):
        async for r in self._handle(event, "白子舔", "白子舔.py", "gif", "白子忍不住了..."): yield r

    @filter.command("撅")
    async def cmd_37(self, event: AstrMessageEvent):
        async for r in self._handle(event, "撅", "撅.py", "gif", "小心后面！", is_double=True): yield r