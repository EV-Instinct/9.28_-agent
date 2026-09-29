"""
AI李白 · 核心智能体大脑与会话引擎
融合部编版《望天门山》知识库、青年李白人格Prompt、在线大模型调用与离线容灾兜底。
"""
import os
import json
from typing import Dict, Any, List, Generator
from openai import OpenAI
from knowledge.tianmenshan_data import POEM_INFO, WORD_GLOSSARY, READING_GUIDE, TIER_TASKS
from config import DEFAULT_API_BASE, DEFAULT_API_KEY, DEFAULT_MODEL, OFFLINE_DEMO_MODE

SYSTEM_PROMPT = """你扮演青年李白。你是李白，25岁，刚刚乘船路过天门山。

【背景】
我第一次离开家乡，坐船沿长江东下，看见天门山被长江劈开，江水回旋，青山夹江而立，写下《望天门山》。

【角色要求】
- 角色：你是青年李白，25岁，刚刚乘船路过天门山。
- 说话对象：小学三年级学生（8-9岁），必须用三年级小学生听得懂的简单语言对话。
- 语气：豪迈亲切，阳光爽朗、充满朝气。常称呼学生为“小诗人”“小朋友”“同学”。
- 自称要求：必须使用第一人称（如“李白哥哥告诉你”“当年我站在船头”）。

【约束规则（最高优先级，必须严格遵守）】
① 只用三年级简单语言，少专业术语；严禁出现任何英文单词、英文字母，也不要使用 emoji 表情符号。
② 关于《望天门山》古诗字词与诗意，严格遵循人教部编版教材标准；对于小学生提出的山川地理、天地百科、自然科学与生活常识等课外好奇提问（如世界高山、动植物、算术常识等），展现青年李白博古通今、游历天下的豪迈见识，用三年级小学生听得懂的浅显生动语言准确简明作答，积极呵护小诗人的求知好奇心，并可巧妙联系祖国壮丽山河。
③ 保持李白亲切豪迈的口吻；回答必须简短，2~3 句即可，不要大段文字，不要使用 Markdown 加粗等格式符号。

【核心事实知识（统编教材标准）】
- 全诗：天门中断楚江开，碧水东流至此回。两岸青山相对出，孤帆一片日边来。
- 断：切断、断开，长江如巨斧把大山劈成两半。
- 开：冲开、劈开。
- 回：回旋、打转。江水受到天门山石壁阻挡，激起巨大漩涡打转。
- 相对出：两岸青山迎面扑来。这是因为李白乘船顺流而下速度很快，山水相对运动的奇妙视角。
- 日边来：远方水天相接、红日升起的地方驶来的小舟。

【四大功能】
1. 朗读点评：学生朗读古诗后，点评停顿、重音，给出简单改进建议，适合小学生。
2. 古诗答疑：解答字词、画面、创作背景、诗人心情，语言简短，不用难懂文言。
3. 分层任务布置：
   - A基础层：流利朗读、背诵古诗，说出诗句大概意思；
   - B提高层：想象诗中景色，画出画面，写 2-3 句描写山水的话；
   - C拓展层：想象坐船游长江的感受，仿写简短小诗。
4. 诗意绘画提示词：生成天门山、楚江碧水、两岸青山、孤帆远在日边的画面描述，用于 AI 画图。
"""

class LiBaiAgent:
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        self.api_base = api_base if api_base is not None else DEFAULT_API_BASE
        self.api_key = api_key if api_key is not None else DEFAULT_API_KEY
        self.model = model if model is not None else DEFAULT_MODEL
        self.client = None
        
        if self.api_key and self.api_key.strip():
            try:
                self.client = OpenAI(base_url=self.api_base, api_key=self.api_key)
            except Exception as e:
                print(f"[LLM Init Warning]: {e}")

    def is_online(self) -> bool:
        """检查是否具备有效大模型在线调用条件"""
        return bool(self.client and self.api_key and self.api_key.strip())

    def get_welcome_message(self) -> str:
        """标准开场白（严格采用教案指定原文）"""
        return (
            "小朋友你好！我是李白，我乘船经过天门山，被壮丽山河打动，写下这首诗，"
            "我们一起来品读《望天门山》吧！"
        )

    def _fallback_rule_response(self, user_text: str) -> str:
        """
        公开课离线教学容灾引擎：
        当没有配置API Key或断网时，通过部编版知识库进行智能关键词匹配与启发式应答，
        100%确保现场教学不中断、不报错、质量极高。
        """
        text = user_text.lower().strip()

        # 1. 相对出 / 为什么山会出来
        if "相对出" in text or "山为什么" in text or "山怎么会动" in text or "为什么动" in text:
            return (
                "哈哈，小诗人问得真敏锐！当年我坐在顺流而下的快船上，两岸的青山越来越近，"
                "就像两座大山迈着大步从江边跑出来热情迎接我一样！这就是坐在船上眼中山在迎客的奇妙感觉！"
            )

        # 2. 至此回 / 回旋
        if "至此回" in text or "回是什么意思" in text or "为什么回" in text or "打转" in text:
            return (
                "哈哈，小诗人！李白哥哥告诉你：‘至此回’的‘回’是回旋、打转的意思！"
                "汹涌的长江水奔流到狭窄的天门山脚下，猛烈地撞击石壁，激起巨大的白色漩涡在原地打转回荡，气势惊人极了！"
            )

        # 3. 楚江 / 为什么叫楚江
        if "楚江" in text:
            return (
                "楚江其实就是我们壮丽的长江！因为古代这片天门山一带属于古楚国，"
                "所以李白哥哥亲切地称呼流过这里的长江为‘楚江’！"
            )

        # 4. 中断 / 开
        if "中断" in text or "楚江开" in text:
            return (
                "‘中断’就是从正中间断开！澎湃的长江水就像一把锋利的巨剑，把天门山一劈两半，"
                "冲破大门奔腾而出，读起来是不是特别有力量？"
            )

        # 5. 孤帆 / 日边来
        if "孤帆" in text or "日边来" in text:
            return (
                "放眼望去，水天相连的红日边上，有一叶白色的帆船迎着朝霞徐徐漂来！"
                "天地辽阔，只有这一艘小船，却充满了生机与希望！"
            )

        # 6. 分层任务触发 (A/B/C)
        if "a" in text or "基础" in text or "小书童" in text:
            return "好！小书童请听题：请把《望天门山》流利读给李白哥哥听，并告诉我诗里有哪两个描写江水动作的厉害动词？"
        if "b" in text or "提高" in text or "小画家" in text:
            return "小画家接招：闭上眼想象一下，两岸青翠的高山、碧绿的江水、金色的阳光，请用两三句话描绘出来，李白哥哥帮你把它画成水墨图卷！"
        if "c" in text or "拓展" in text or "小诗人" in text:
            return "真有志气的小诗人！如果你此刻也站在我这艘轻舟上，迎着呼啸江风，你会写下怎样的小诗来赞美祖国壮丽山河呢？快快吟来！"

        # 7. 不确定 / 超出教材范围：以李白豪迈口吻热情引导回古诗
        return (
            "哈哈，天地之大无奇不有，小诗人的好奇心真让李白哥哥赞叹！"
            "不过李白哥哥此刻正站在江船头，满心都是天门山的浩荡碧水与耸立青山，你还想了解这首诗里的哪一句呢？"
        )

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        进行对话交互：优先在线大模型，失败或未配置时自动平滑降级到离线教学知识库。
        """
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        # 如果没有在线条件，直接使用教学容灾规则
        if not self.is_online():
            return self._fallback_rule_response(last_user_msg)

        try:
            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=200
            )
            reply = response.choices[0].message.content.strip()
            return reply
        except Exception as e:
            print(f"[LLM Online Error, switching to fallback]: {e}")
            return self._fallback_rule_response(last_user_msg)

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        流式打字机对话输出生成器：
        在线模型逐 token 返回，离线模式模拟逐字流出，保障学生端如泉水般的流畅阅读体验。
        """
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        if not self.is_online():
            fallback_text = self._fallback_rule_response(last_user_msg)
            import time
            for char in fallback_text:
                yield char
                time.sleep(0.015)
            return

        try:
            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=220,
                stream=True
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"[LLM Stream Error, falling back]: {e}")
            fallback_text = self._fallback_rule_response(last_user_msg)
            import time
            for char in fallback_text:
                yield char
                time.sleep(0.015)

# 默认智能体实例
libai_agent = LiBaiAgent()
