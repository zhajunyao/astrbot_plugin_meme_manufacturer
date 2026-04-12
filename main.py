import os, requests, subprocess, tempfile, logging, sys, time, json
from astrbot.api.all import * # type: ignore

logger = logging.getLogger("astrbot")

@register("表情包制造厂", "神秘嘉宾", "将QQ群友头像做成表情包的工具。可以做成gif，也可以做成静态表情，内置多种表情包，方便互动", "1.0")
class MemeArsenal(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config  # 把 AstrBot 喂给你的面板配置接住！
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = os.path.join(self.plugin_dir, "scripts")

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

        target_url = None
        # 1. 抓取目标图片或头像
        for comp in event.message_obj.message:
            if isinstance(comp, Image):
                target_url = comp.url
                break
        if not target_url:
            for comp in event.message_obj.message:
                if isinstance(comp, At) and str(comp.qq) != str(event.get_self_id()):
                    target_url = f"http://q1.qlogo.cn/g?b=qq&nk={comp.qq}&s=640"
                    break

        if not target_url:
            yield event.plain_result(f"提示：/{cmd} 指令需要带图发送，或者 @你要处理的人 哦！")
            return

        yield event.plain_result(msg)
        temp_dir = tempfile.gettempdir()
        ts = int(time.time())
        in_p = os.path.join(temp_dir, f"{cmd}_in_{ts}.png")
        out_base = os.path.join(temp_dir, f"{cmd}_out_{ts}")

        try:
            # 下载目标图
            with open(in_p, "wb") as f:
                f.write(requests.get(target_url, timeout=10).content)

            # 基础运行参数
            args = [sys.executable, os.path.join(self.scripts_dir, script)]

            if is_double:  # 处理双人逻辑（例如贴贴）
                sender_p = os.path.join(temp_dir, f"sender_{ts}.png")
                sender_id = event.get_sender_id()
                with open(sender_p, "wb") as f:
                    f.write(requests.get(f"http://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=640").content)
                args += [sender_p, in_p, out_base + "." + ext]
            else:
                args += [in_p, out_base + "." + ext]
            if extra_args:
                args.extend(extra_args)
            # 启动子进程处理
            res = subprocess.run(args, cwd=self.plugin_dir, capture_output=True, text=True)

            # 自动探测文件后缀（解决 卖掉了 等脚本生成 gif 或 png 的不确定性）
            final_out = ""
            for e in [ext, "gif", "png"]:
                if os.path.exists(out_base + "." + e):
                    final_out = out_base + "." + e
                    break

            if res.returncode != 0:
                err = res.stderr.strip() or res.stdout.strip()
                yield event.plain_result(f"生成失败：\n{err}")
            elif final_out:
                r = event.make_result()
                r.chain = [Image.fromFileSystem(final_out)]
                yield r
            else:
                yield event.plain_result("错误：脚本未生成任何文件。")
        except Exception as e:
            yield event.plain_result(f"插件逻辑出错：{str(e)}")


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