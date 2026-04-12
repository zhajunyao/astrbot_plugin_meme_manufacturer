import os
import sys
import tempfile
import uuid
import asyncio
import socket
import ipaddress
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
        self.semaphore = asyncio.Semaphore(5)

        # 【修复性能】插件级别复用 aiohttp Session
        self._session = None

    async def get_session(self):
        """获取或创建全局复用的 aiohttp Session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def download_image(self, url: str, path: str):
        """异步下载图片，内置严格的 SSRF 防御与 Content-Type 校验"""
        # 强制替换 QQ 头像明文协议为 HTTPS（解决安全提醒）
        if url.startswith("http://q1.qlogo.cn"):
            url = url.replace("http://", "https://")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("仅支持 HTTP/HTTPS 协议的图片地址。")

        # 【修复 SSRF】严格的 DNS 解析与真实 IP 拦截
        try:
            ip = socket.gethostbyname(parsed.hostname)
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                raise ValueError(f"拦截到非法内网/本地 IP: {ip}")
        except Exception as e:
            raise ValueError(f"域名解析失败或命中非法地址保护: {e}")

        session = await self.get_session()
        async with session.get(url, timeout=10) as resp:
            if resp.status != 200:
                raise RuntimeError(f"网络异常，HTTP状态码: {resp.status}")

            # 【修复安全性】验证响应头，确保下载的确实是图片而不是恶意脚本
            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"拦截到非法文件类型 ({content_type})，仅允许下载图片。")

            downloaded_size = 0
            with open(path, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    downloaded_size += len(chunk)
                    if downloaded_size > 5 * 1024 * 1024:  # 限制最大 5MB
                        raise ValueError("图片体积过大（超 5MB），已拦截。")
                    f.write(chunk)

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
                    target_url = f"https://q1.qlogo.cn/g?b=qq&nk={comp.qq}&s=640";
                    break

        if not target_url:
            target_url = f"https://q1.qlogo.cn/g?b=qq&nk={event.get_sender_id()}&s=640"

        yield event.plain_result(msg)

        temp_dir = tempfile.gettempdir()
        req_id = uuid.uuid4().hex
        in_p = os.path.join(temp_dir, f"{cmd}_in_{req_id}.png")
        out_base = os.path.join(temp_dir, f"{cmd}_out_{req_id}")
        sender_p = os.path.join(temp_dir, f"sender_{req_id}.png") if is_double else None

        files_to_cleanup = [in_p]

        try:
            async with self.semaphore:
                try:
                    await self.download_image(target_url, in_p)
                except Exception as e:
                    yield event.plain_result(f"❌ 目标头像下载失败: {e}")
                    return

                args = [sys.executable, os.path.join(self.scripts_dir, script)]

                if is_double:
                    sender_id = event.get_sender_id()
                    sender_url = f"https://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=640"
                    try:
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
                    await process.wait()
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


# ==========================================
# 【修复致命报错】必须放在 MemeArsenal 类定义完全结束之后的全局外部空间
# ==========================================
COMMAND_REGISTRY = {
    "泉此方看": {"ext": "png", "msg": "此方正在看..."},
    "吸": {"ext": "gif", "msg": "正在发动黑洞..."},
    "敲": {"ext": "gif", "msg": "当当当！"},
    "墙纸": {"ext": "gif", "msg": "正在粉刷墙壁..."},
    "抛": {"ext": "gif", "msg": "用力一扔！"},
    "拍": {"ext": "gif", "msg": "无影手准备中..."},
    "拿捏": {"ext": "gif", "msg": "尽在掌控..."},
    "膜拜": {"ext": "gif", "msg": "大佬受我一拜！"},
    "卖掉了": {"ext": "png", "msg": "成交！"},
    "啾啾": {"ext": "gif", "msg": "Mua~"},
    "紧贴": {"ext": "gif", "msg": "贴住了，贴得死死的！"},
    "胡桃啃": {"ext": "gif", "msg": "胡桃牙痒痒了..."},
    "搓": {"ext": "gif", "msg": "正在疯狂揉搓..."},
    "锤": {"ext": "gif", "msg": "吃我一锤！"},
    "舔屏": {"ext": "gif", "msg": "嘿嘿嘿..."},
    "贴贴": {"ext": "gif", "msg": "飞扑贴贴！", "is_double": True},
    "伽波贴": {"ext": "gif", "msg": "伽波！"},
    "催眠": {"ext": "gif", "msg": "注入暗示中..."},
    "打拳": {"ext": "gif", "msg": "欧拉欧拉欧拉！"},
    "可莉吃": {"ext": "gif", "msg": "可莉开饭啦！"},
    "跳": {"ext": "gif", "msg": "跳一跳！"},
    "撸": {"ext": "gif", "msg": "正在加速...", "extra_args": ["1"]},
    "双手撸": {"script": "撸.py", "ext": "gif", "msg": "双手加速...", "extra_args": ["1"]},
    "单手撸": {"script": "撸.py", "ext": "gif", "msg": "单手加速...", "extra_args": ["2"]},
    "射": {"ext": "gif", "msg": "准备击中..."},
    "垃圾桶": {"ext": "gif", "msg": "回收废品中..."},
    "顶": {"ext": "gif", "msg": "顶上去！"},
    "科目三": {"ext": "gif", "msg": "社会摇准备..."},
    "砸": {"ext": "gif", "msg": "大锤搞定！"},
    "摸头": {"ext": "gif", "msg": "乖乖，摸摸头..."},
    "吃": {"ext": "gif", "msg": "阿姆阿姆..."},
    "草神啃": {"ext": "gif", "msg": "纳西妲也想啃..."},
    "抱大腿": {"ext": "gif", "msg": "求带飞！"},
    "飞机杯": {"ext": "gif", "msg": "正在起飞！"},
    "汤姆嘲笑": {"ext": "gif", "msg": "汤姆正在大笑..."},
    "字符画": {"ext": "png", "msg": "正在转码..."},
    "抱抱": {"ext": "gif", "msg": "抱一个~", "is_double": True},
    "白子舔": {"ext": "gif", "msg": "白子忍不住了..."},
    "撅": {"ext": "gif", "msg": "小心后面！", "is_double": True}
}

for cmd_name, config in COMMAND_REGISTRY.items():
    def create_handler(name, cfg):
        @filter.command(name)
        async def wrapper(self, event: AstrMessageEvent):
            script_name = cfg.get("script", f"{name}.py")
            async for r in self._handle(
                    event, name, script_name,
                    cfg.get("ext", "gif"), cfg.get("msg", "正在生成..."),
                    cfg.get("is_double", False), cfg.get("extra_args")
            ):
                yield r

        wrapper.__name__ = f"cmd_{uuid.uuid4().hex[:8]}"
        return wrapper


    # 因为这一段写在类定义的外面，此时 MemeArsenal 类已经建好了，就不会报错了
    setattr(MemeArsenal, f"dynamic_cmd_{cmd_name}", create_handler(cmd_name, config))