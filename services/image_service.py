"""
诗境入画 · 图像生成与诗画工坊服务
支持调用阿里云通义万相 (Wanx) 高清文生图，
并内置基于 Pillow 的高品质水墨画卷渲染器（包含宣纸底色、青绿山水、朱砂印章与毛笔题字），
确保无论联网与否、账户权限如何，都能在现场生成具有仪式感的古典诗画作品。
"""
import os
import io
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import IMAGES_DIR, DEFAULT_API_KEY

class ImageService:
    def __init__(self):
        self.output_dir = IMAGES_DIR

    def generate_poem_prompt(self, user_description: str) -> str:
        """根据学生描写生成专业的生图提示词"""
        base_elements = "天门山两峰耸立夹江，碧绿清澈的长江水奔腾回旋，两岸青山叠翠，一叶孤舟扬帆远航，远方初升红日朝霞"
        style = "中国传统工笔青绿山水画风格，水墨意境，赵孟頫青绿设色，儿童绘本插画，构图开阔，意境悠远，高画质，宣纸质感"
        if user_description and user_description.strip():
            return f"{user_description}，{base_elements}，{style}"
        return f"{base_elements}，{style}"

    def try_wanx_generation(self, prompt: str) -> str:
        """
        尝试调用阿里百炼通义万相 (Wanx) 文生图 API
        """
        api_key = os.getenv("DASHSCOPE_API_KEY") or DEFAULT_API_KEY
        if not api_key:
            return ""

        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        payload = {
            "model": "wanx-v1",
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "style": "<watercolor>",
                "size": "1024*1024",
                "n": 1
            }
        }

        try:
            # 1. 提交异步任务
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code != 200:
                print(f"[Wanx API Warning] Task submit failed: {res.text}")
                return ""

            task_id = res.json().get("output", {}).get("task_id")
            if not task_id:
                return ""

            # 2. 轮询任务结果（最多等待 25 秒）
            check_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            for _ in range(12):
                time.sleep(2)
                task_res = requests.get(check_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=8)
                if task_res.status_code == 200:
                    output_data = task_res.json().get("output", {})
                    task_status = output_data.get("task_status")
                    if task_status == "SUCCEEDED":
                        results = output_data.get("results", [])
                        if results and "url" in results[0]:
                            img_url = results[0]["url"]
                            # 下载保存到本地
                            img_data = requests.get(img_url, timeout=15).content
                            timestamp = int(time.time() * 1000)
                            local_file = self.output_dir / f"wanx_{timestamp}.png"
                            with open(local_file, "wb") as f:
                                f.write(img_data)
                            return str(local_file)
                    elif task_status in ["FAILED", "CANCELED"]:
                        print(f"[Wanx Generation Failed]: {output_data}")
                        break
        except Exception as e:
            print(f"[Wanx Exception]: {e}")

        return ""

    def render_ink_scroll(self, student_name: str, line_selected: str, user_description: str) -> str:
        """
        诗画工坊核心入口：
        优先尝试阿里百炼通义万相生成高清水墨插画；
        若未开通或网络超时，平滑切换至本地工笔宣纸水墨画卷渲染器。
        """
        prompt = self.generate_poem_prompt(user_description)
        # 1. 尝试在线万相生成
        online_img = self.try_wanx_generation(prompt)
        if online_img and os.path.exists(online_img):
            return online_img

        # 2. 离线/保底渲染国风长卷
        width, height = 900, 520
        # 宣纸底色背景（淡米黄/象牙暖白）
        img = Image.new("RGB", (width, height), color=(248, 243, 230))
        draw = ImageDraw.Draw(img)

        # 远景红日朝霞
        draw.ellipse([640, 60, 740, 160], fill=(242, 140, 110))

        # 远山（淡墨灰青）
        far_mountains = [
            (0, 260), (120, 180), (280, 240), (450, 160), (600, 220), (760, 150), (900, 250), (900, 520), (0, 520)
        ]
        draw.polygon(far_mountains, fill=(188, 204, 196))

        # 天门山主峰（青绿重彩）
        left_peak = [
            (0, 320), (80, 130), (190, 90), (320, 210), (380, 360), (280, 520), (0, 520)
        ]
        draw.polygon(left_peak, fill=(46, 88, 78))

        right_peak = [
            (520, 360), (600, 180), (720, 110), (840, 200), (900, 290), (900, 520), (480, 520)
        ]
        draw.polygon(right_peak, fill=(58, 98, 88))

        # 楚江水流（碧水蓝绿）
        river = [
            (320, 360), (450, 260), (560, 360), (900, 480), (900, 520), (0, 520), (0, 450)
        ]
        draw.polygon(river, fill=(116, 172, 162))

        # 水流漩涡装饰（至此回）
        for offset in range(0, 180, 25):
            draw.arc([350 - offset//2, 380 + offset//3, 560 + offset, 460 + offset//2], 
                     start=10, end=190, fill=(160, 210, 200), width=3)

        # 一叶孤帆
        boat = [(480, 335), (540, 335), (530, 345), (490, 345)]
        draw.polygon(boat, fill=(90, 60, 40))
        sail = [(510, 295), (510, 333), (536, 333)]
        draw.polygon(sail, fill=(255, 250, 240))
        draw.line([(510, 290), (510, 335)], fill=(60, 40, 20), width=2)

        # 古典边框
        draw.rectangle([15, 15, width - 15, height - 15], outline=(150, 130, 110), width=3)
        draw.rectangle([22, 22, width - 22, height - 22], outline=(180, 160, 140), width=1)

        # 朱砂印章位置与边框
        seal_x, seal_y = 50, 46
        draw.rectangle([seal_x, seal_y, seal_x + 52, seal_y + 52], outline=(186, 42, 32), width=3)
        draw.rectangle([seal_x + 3, seal_y + 3, seal_x + 49, seal_y + 49], outline=(186, 42, 32), width=1)

        # 尝试加载 Windows 中文字体进行题跋
        font_paths = [
            "C:/Windows/Fonts/simkai.ttf",   # 楷体
            "C:/Windows/Fonts/simsun.ttc",   # 宋体
            "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf"    # 黑体
        ]
        title_font = None
        small_font = None
        seal_font = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    title_font = ImageFont.truetype(fp, 26)
                    small_font = ImageFont.truetype(fp, 16)
                    seal_font = ImageFont.truetype(fp, 18)
                    break
                except Exception:
                    pass

        if title_font and small_font:
            # 绘制竖排/横排题诗
            draw.text((120, 50), f"《望天门山》· {line_selected}", fill=(40, 45, 42), font=title_font)
            draw.text((122, 85), f"小诗人【{student_name}】与青年李白 共创诗意卷", fill=(100, 110, 105), font=small_font)
            # 朱砂印章内文字
            if seal_font:
                draw.text((seal_x + 8, seal_y + 6), "太白", fill=(186, 42, 32), font=seal_font)
                draw.text((seal_x + 8, seal_y + 26), "诗境", fill=(186, 42, 32), font=seal_font)

        # 保存输出
        timestamp = int(time.time() * 1000)
        filepath = self.output_dir / f"scroll_{timestamp}.png"
        img.save(filepath, "PNG")
        return str(filepath)

# 导出单例
image_service = ImageService()
