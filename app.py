"""
AI李白 · 望天门山研学助手
小学语文三年级（部编版）专属数字化教学终端
包含：行舟伴学、金石朗诵、诗境入画、分层闯关四大研学舱
"""
import streamlit as st
import os
import time
from pathlib import Path
from core.libai_agent import libai_agent, LiBaiAgent
from knowledge.tianmenshan_data import POEM_INFO, WORD_GLOSSARY, READING_GUIDE, TIER_TASKS
from services.tts_service import tts_service
from services.image_service import image_service
from services.asr_service import asr_service
from modules.reader_evaluator import reader_evaluator
import base64
from config import DEFAULT_TTS_VOICE

LIBAI_AVATAR_PATH = str(Path(__file__).resolve().parent / "assets" / "libai_avatar.png")

@st.cache_data
def load_libai_avatar_b64() -> str:
    p = Path(LIBAI_AVATAR_PATH)
    if p.exists():
        with open(p, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    return ""

LIBAI_AVATAR_URI = load_libai_avatar_b64()

# 1. 页面基本配置
st.set_page_config(
    page_title="AI李白·望天门山研学助手",
    page_icon=LIBAI_AVATAR_PATH if os.path.exists(LIBAI_AVATAR_PATH) else "⛵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 定制【新中式青绿山水 · 宣纸典雅风】视觉系统
st.markdown("""
<style>
    /* 引入思源古典宋体与楷体字体族 */
    @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;600;700;900&display=swap');

    /* 全局背景与字体基准 */
    .stApp {
        background-color: #FAF6EF;
        background-image: radial-gradient(#E8DFC9 0.75px, transparent 0.75px), radial-gradient(#E8DFC9 0.75px, #FAF6EF 0.75px);
        background-size: 30px 30px;
        background-position: 0 0, 15px 15px;
        color: #243830;
        font-family: "Noto Serif SC", "PingFang SC", "STKaiti", "KaiTi", "SimSun", serif;
    }

    /* 顶部青绿山水金镶长卷 */
    .hero-scroll-banner {
        background: linear-gradient(135deg, #13392E 0%, #1D5344 55%, #2B6B58 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: #FAF7F0;
        box-shadow: 0 10px 28px rgba(19, 57, 46, 0.22);
        margin-bottom: 20px;
        border: 2px solid #C5A465;
        position: relative;
        overflow: hidden;
    }
    .hero-scroll-banner::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(235, 140, 95, 0.18) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-header-flex {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    .hero-title {
        font-size: 32px;
        font-weight: 900;
        margin: 0;
        letter-spacing: 3px;
        color: #FFF9ED;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-badge-tag {
        background: rgba(197, 164, 101, 0.25);
        border: 1px solid #E5C88F;
        color: #F8E7C5;
        font-size: 13px;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 1px;
    }
    .hero-subtitle {
        font-size: 15px;
        margin-top: 8px;
        color: #D3E8E0;
        letter-spacing: 1.5px;
    }
    .hero-persona-pill {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(229, 200, 143, 0.5);
        border-radius: 30px;
        padding: 6px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 14px;
        color: #FFF6E5;
    }

    /* 宋代折页宣纸长碑（古诗展示） */
    .poem-scroll-card {
        background: #FDFBF7;
        border: 2px solid #D8CBB6;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 6px 18px rgba(90, 75, 55, 0.06);
        margin: 15px 0 25px 0;
        position: relative;
        text-align: center;
    }
    .poem-scroll-card::after {
        content: "";
        position: absolute;
        top: 6px; left: 6px; right: 6px; bottom: 6px;
        border: 1px solid #ECE3D4;
        border-radius: 8px;
        pointer-events: none;
    }
    .poem-author {
        font-size: 15px;
        color: #8C7853;
        letter-spacing: 3px;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .poem-lines-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 10px;
    }
    @media (max-width: 768px) {
        .poem-lines-grid { grid-template-columns: 1fr; }
    }
    .poem-line-chunk {
        background: #F8F3E9;
        border: 1px solid #E6DCB8;
        border-radius: 8px;
        padding: 12px 6px;
        font-size: 19px;
        font-weight: 700;
        color: #1A3E33;
        letter-spacing: 2px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.02);
    }
    .poem-seal {
        display: inline-block;
        border: 1px solid #C0392B;
        color: #C0392B;
        font-size: 11px;
        padding: 1px 4px;
        border-radius: 3px;
        vertical-align: middle;
        margin-left: 6px;
        font-weight: normal;
    }

    /* 古典国风 Tab 导航栏重塑 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #D8CBB6 !important;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #F3EDE2 !important;
        border: 1px solid #D8CBB6 !important;
        border-bottom: none !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 10px 20px !important;
        color: #4A5D54 !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #EAE0D0 !important;
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #1B4E40 0%, #296856 100%) !important;
        color: #FFF8E7 !important;
        border-color: #1B4E40 !important;
        box-shadow: 0 -3px 12px rgba(27, 78, 64, 0.18) !important;
    }

    /* 宣纸卡片容器通用类 */
    .ink-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 22px;
        border: 1px solid #E8DFCE;
        box-shadow: 0 4px 16px rgba(60, 50, 35, 0.05);
        margin-bottom: 20px;
        position: relative;
    }

    /* 诗仙研学令 · 侧边栏整体美化 */
    [data-testid="stSidebar"] {
        background-color: #F7F1E5 !important;
        border-right: 1px solid #E2D5BE !important;
    }
    .sidebar-jade-card {
        background: linear-gradient(135deg, #FAF7F0 0%, #F4ECE0 100%);
        border: 2px solid #C8AC75;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(100, 80, 50, 0.06);
        margin-bottom: 16px;
    }
    .sidebar-avatar-circle {
        width: 60px;
        height: 60px;
        margin: 0 auto 8px auto;
        background: #256150;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        border: 2px solid #E8CA8A;
        box-shadow: 0 3px 8px rgba(37, 97, 80, 0.3);
    }

    /* 荣誉博古架（成就指标卡） */
    .honor-shelf-metric {
        background: #FFFBF2;
        border: 1px solid #E2D3B8;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
    .honor-shelf-num {
        font-size: 22px;
        font-weight: 800;
        color: #C0392B;
        font-family: 'Noto Serif SC', serif;
    }
    .honor-badge-item {
        background: linear-gradient(135deg, #FFFDF8 0%, #FFF5E0 100%);
        border: 1px solid #E0C17E;
        color: #8C6424;
        padding: 7px 12px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 6px rgba(180, 140, 60, 0.08);
    }

    /* 温润玉质按钮覆写 */
    .stButton > button {
        background: linear-gradient(135deg, #2A6856 0%, #1A493C 100%) !important;
        color: #FFFDF8 !important;
        border: 1px solid #C8A86B !important;
        border-radius: 10px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 9px 24px !important;
        box-shadow: 0 4px 14px rgba(26, 73, 60, 0.18) !important;
        transition: all 0.25s ease !important;
        letter-spacing: 1px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #357F6B 0%, #225C4C 100%) !important;
        box-shadow: 0 6px 18px rgba(26, 73, 60, 0.28) !important;
        border-color: #F0D598 !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# 3. 初始化会话状态 (Session State)
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": libai_agent.get_welcome_message()}
    ]
if "student_name" not in st.session_state:
    st.session_state.student_name = "小诗人"
if "stars_earned" not in st.session_state:
    st.session_state.stars_earned = 0
if "unlocked_badges" not in st.session_state:
    st.session_state.unlocked_badges = set()
if "last_generated_scroll" not in st.session_state:
    st.session_state.last_generated_scroll = None
if "tts_voice" not in st.session_state:
    st.session_state.tts_voice = DEFAULT_TTS_VOICE
tts_service.set_voice(st.session_state.tts_voice)


def award_badge(badge_name: str, stars: int) -> bool:
    """颁发勋章并计研学星。同一枚勋章只计一次，避免重复打卡刷星。"""
    if badge_name in st.session_state.unlocked_badges:
        return False
    st.session_state.unlocked_badges.add(badge_name)
    st.session_state.stars_earned += stars
    return True


# 4. 侧边栏：【诗仙研学令 · 书童伴学台】
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-jade-card">
        <img src="{LIBAI_AVATAR_URI}" style="width: 72px; height: 72px; border-radius: 50%; border: 2.5px solid #C8A86B; box-shadow: 0 4px 14px rgba(29, 74, 61, 0.2); object-fit: cover; margin-bottom: 8px;" alt="青年李白">
        <div style="font-size: 13px; color: #8A7650; letter-spacing: 2px; margin-bottom: 2px;">诗仙李白 · 青年伴学</div>
        <div style="font-size: 18px; font-weight: 800; color: #1D4A3D; letter-spacing: 1px;">小诗人学籍簿</div>
    </div>
    """, unsafe_allow_html=True)

    student_name_input = st.text_input("小诗人姓名 / 雅号：", value=st.session_state.student_name)
    if student_name_input != st.session_state.student_name:
        st.session_state.student_name = student_name_input

    st.markdown("---")
    st.markdown("<div style='font-size:15px; font-weight:700; color:#1D4A3D; margin-bottom:8px;'>🏛️ 荣誉博古架</div>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        star_metric_ph = st.empty()
    with col_s2:
        badge_metric_ph = st.empty()
    
    badge_list_ph = st.empty()

    st.markdown("---")
    with st.expander("⚙️ 教师公开课设置（模型与音色）", expanded=False):
        teacher_api_key = st.text_input("大模型 API Key（可选，为空则使用智能容灾）：", type="password")
        model_options = list(dict.fromkeys(
            [libai_agent.model, "qwen-plus", "qwen-max", "deepseek-chat", "glm-4", "gpt-4o-mini"]
        ))
        teacher_model = st.selectbox("模型引擎：", model_options, index=0)
        
        # 阿里百炼 CosyVoice 云端大模型纯正男声音色（100%男声，纯云端大模型，无本地音色）
        voice_options = [
            ("longfei", "🌟 阿里百炼·龙飞（激情豪迈·古诗吟诵专长男声，推荐）"),
            ("longcheng", "☀️ 阿里百炼·龙橙（阳光洒脱·青年李白男声）"),
            ("longshuo", "🏔️ 阿里百炼·龙硕（沉稳英挺·名家风范男声）"),
            ("longze", "🍃 阿里百炼·龙泽（温润清朗·热忱少年男声）"),
        ]
        voice_codes = [v[0] for v in voice_options]
        current_v = st.session_state.get("tts_voice", DEFAULT_TTS_VOICE)
        default_v_idx = voice_codes.index(current_v) if current_v in voice_codes else 0

        selected_voice_tuple = st.selectbox(
            "李白声音音色：",
            voice_options,
            index=default_v_idx,
            format_func=lambda x: x[1],
            key="tts_voice_selector"
        )
        selected_code = selected_voice_tuple[0]

        # 只要用户切换选择，立即同步至 session_state 与 tts_service 单例
        if selected_code != st.session_state.tts_voice:
            st.session_state.tts_voice = selected_code
            tts_service.set_voice(selected_code)
            st.toast(f"🎙️ 李白音色已实时切换为：{selected_voice_tuple[1].split('（')[0]}")
            st.rerun()
        else:
            tts_service.set_voice(selected_code)

        # 实时试听当前音色按钮
        if st.button("🎧 试听当前李白音色", key="preview_voice_btn", use_container_width=True):
            with st.spinner("李白正在开嗓试音..."):
                preview_text = "两岸青山相对出，孤帆一片日边来！小朋友，我是李白，愿与你同游天门山！"
                preview_file = tts_service.generate_speech(preview_text, voice_override=selected_code)
                if preview_file and os.path.exists(preview_file):
                    st.audio(preview_file, format="audio/mp3", autoplay=True)
                    st.caption(f"✨ 试听播报中（当前生效音色：{selected_voice_tuple[1].split('（')[0]}）")
                else:
                    st.warning("试听音频生成暂不可用，请检查百炼配置或网络。")

        if teacher_api_key:
            libai_agent.api_key = teacher_api_key
            libai_agent.model = teacher_model
            libai_agent.client = None
            os.environ["DASHSCOPE_API_KEY"] = teacher_api_key
            import dashscope
            dashscope.api_key = teacher_api_key
            try:
                from openai import OpenAI
                libai_agent.client = OpenAI(base_url=libai_agent.api_base, api_key=teacher_api_key)
                st.success("✅ 已切换为在线智能大模型与百炼语音！")
            except Exception as e:
                st.error(f"连接失败: {e}")
        elif libai_agent.is_online():
            st.success(f"✅ 在线智能大模型已就绪（{libai_agent.model}）")
            st.caption("已通过 .env 配置文件接入；如需临时更换密钥，在上方填入即可。")
        else:
            st.info("💡 当前为【教学比赛容灾模式】，免外网 Key 也能高质量应答！")

    st.markdown("---")
    with st.expander("📖 部编教材《望天门山》字词速查"):
        for word, val in WORD_GLOSSARY.items():
            st.markdown(f"**【{word}】**")
            st.caption(val["child_friendly"])

# 5. 页面顶部横幅：青绿水墨金镶长卷
st.markdown(f"""
<div class="hero-scroll-banner">
    <div class="hero-header-flex">
        <div style="display: flex; align-items: center; gap: 18px;">
            <img src="{LIBAI_AVATAR_URI}" style="width: 70px; height: 70px; border-radius: 50%; border: 2.5px solid #F0D598; box-shadow: 0 4px 16px rgba(0,0,0,0.35); object-fit: cover; flex-shrink: 0;" alt="青年李白">
            <div>
                <div class="hero-title" style="margin-bottom: 2px;">
                    AI李白 · 望天门山研学助手
                    <span class="hero-badge-tag">统编三年级上册</span>
                </div>
                <div class="hero-subtitle" style="margin-top: 4px;">
                    青绿水墨交互课堂 · 诗画互译沉浸式研学 | 伴读小诗人：<b>{st.session_state.student_name}</b>
                </div>
            </div>
        </div>
        <div class="hero-persona-pill">
            <img src="{LIBAI_AVATAR_URI}" style="width: 34px; height: 34px; border-radius: 50%; border: 1.5px solid #F0D598; object-fit: cover; flex-shrink: 0;" alt="李白">
            <div>
                <div style="font-weight:700; color:#FFE6AC;">青年李白 (25岁)</div>
                <div style="font-size:12px; opacity:0.85;">轻舟过楚江 · 诗兴正浓</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 宋代折页宣纸长碑（古诗品读）
st.markdown(f"""
<div class="poem-scroll-card">
    <div class="poem-author">
        《望天门山》· [唐] 李白 
        <span class="poem-seal">太白手泽</span>
    </div>
    <div class="poem-lines-grid">
        <div class="poem-line-chunk">天门中断楚江开</div>
        <div class="poem-line-chunk">碧水东流至此回</div>
        <div class="poem-line-chunk">两岸青山相对出</div>
        <div class="poem-line-chunk">孤帆一片日边来</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. 四大研学舱切换
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 舱一：行舟伴学·情境答疑",
    "🎙️ 舱二：金石之声·朗读测评",
    "🎨 舱三：诗境入画·诗画工坊",
    "🏆 舱四：层楼更上·分层闯关"
])

# ==================== 舱一：行舟伴学·情境答疑 ====================
with tab1:
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.markdown("""
        <div style="margin-bottom:12px;">
            <div style="font-size:21px; font-weight:800; color:#174638; letter-spacing:1px; display:flex; align-items:center; gap:8px;">
                <span>🌊</span> 江上行舟 · 与李白隔空畅谈
            </div>
            <div style="font-size:14px; color:#6D7B74; margin-top:4px;">
                “李白哥哥正乘着小木船顺流而下，迎着江风，有什么好奇的尽管问我哦！”
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 快速提问建议锦囊签
        st.markdown("<div style='font-size:13px; font-weight:700; color:#8C7247; margin-bottom:6px;'>💡 点击抽取引导锦囊签：</div>", unsafe_allow_html=True)
        q_cols = st.columns(3)
        sample_q = ""
        if q_cols[0].button("🏷️ 为什么青山相对出？"):
            sample_q = "李白哥哥，为什么大山会‘相对出’呀？山怎么会动呢？"
        if q_cols[1].button("🏷️ ‘至此回’是什么意思？"):
            sample_q = "‘碧水东流至此回’里的‘回’是什么意思？"
        if q_cols[2].button("🏷️ 为什么长江叫楚江？"):
            sample_q = "李白哥哥，长江为什么在诗里叫楚江呀？"

        # 聊天记录容器
        chat_container = st.container(height=390)
        with chat_container:
            for msg in st.session_state.chat_messages:
                is_assistant = msg["role"] == "assistant"
                chat_avatar = LIBAI_AVATAR_PATH if (is_assistant and os.path.exists(LIBAI_AVATAR_PATH)) else ("🍶" if is_assistant else "🧒")
                with st.chat_message(msg["role"], avatar=chat_avatar):
                    if is_assistant:
                        st.markdown("<span style='color:#C0392B; font-size:12px; font-weight:bold; margin-bottom:4px; display:inline-block;'>【青年李白】</span>", unsafe_allow_html=True)
                    st.write(msg["content"])
                    if msg.get("audio_path") and os.path.exists(msg["audio_path"]):
                        st.audio(msg["audio_path"])

        # 问答输入框
        user_input = st.chat_input("向李白哥哥提问吧（比如字词、心情、当时的景色）...")
        if sample_q:
            user_input = sample_q

        # 语音转文字功能区（阿里百炼 Paraformer 中文语音识别服务）
        st.markdown("<div style='margin-top: 10px; margin-bottom: 4px; font-size: 13px; font-weight: 700; color: #1C493C;'>🎙️ 语音提问（免打字 · 阿里百炼中文语音识别）：</div>", unsafe_allow_html=True)
        v_col1, v_col2 = st.columns([3, 1])
        with v_col1:
            chat_voice_audio = st.audio_input(
                "点击麦克风说话",
                key="chat_voice_input",
                label_visibility="collapsed"
            )
        with v_col2:
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            transcribe_btn = st.button("🎙️ 语音转文字", key="btn_transcribe_chat", use_container_width=True)

        if transcribe_btn:
            if chat_voice_audio is not None:
                with st.spinner("李白哥哥正在倾听，正在通过阿里百炼转写语音..."):
                    spoken_q = asr_service.transcribe_bytes(chat_voice_audio.getvalue())
                if spoken_q and spoken_q.strip():
                    user_input = spoken_q.strip()
                    st.toast(f"🎙️ 识别到问题：{user_input}")
                else:
                    st.warning("未能识别出清晰语音，请对着麦克风清晰说出您的问题～")
            else:
                st.info("💡 请先点击左侧麦克风录音，录完后再点击「语音转文字」即可向李白提问！")

        if user_input:
            # 1. 记录并立即展示用户提问
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            st.session_state.stars_earned += 1
            with chat_container:
                with st.chat_message("user", avatar="🧒"):
                    st.write(user_input)

                # 2. 李白角色打字机流式输出 (Streaming Output)
                with st.chat_message("assistant", avatar=LIBAI_AVATAR_PATH if os.path.exists(LIBAI_AVATAR_PATH) else "🍶"):
                    st.markdown("<span style='color:#C0392B; font-size:12px; font-weight:bold; margin-bottom:4px; display:inline-block;'>【青年李白】</span>", unsafe_allow_html=True)
                    stream_generator = libai_agent.chat_stream(st.session_state.chat_messages)
                    full_response = st.write_stream(stream_generator)

                    # 3. 流式结束后异步合成真人语音
                    audio_file = tts_service.generate_speech(full_response)
                    if audio_file and os.path.exists(audio_file):
                        st.audio(audio_file)

            # 4. 存入历史会话状态
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": full_response,
                "audio_path": audio_file
            })
            st.rerun()

    with col_c2:
        st.markdown("""
        <div style="background:#FFFDF9; border:2px solid #D6C8B2; border-radius:14px; padding:20px; box-shadow:0 4px 14px rgba(70,55,40,0.06); position:relative;">
            <div style="position:absolute; top:12px; right:14px; border:1px solid #C0392B; color:#C0392B; font-size:11px; padding:1px 6px; border-radius:3px;">
                开元盛世
            </div>
            <div style="font-size:17px; font-weight:800; color:#1C493C; margin-bottom:12px; display:flex; align-items:center; gap:6px;">
                <span>📜</span> 太白行舟小札
            </div>
            <div style="font-size:14px; line-height:1.9; color:#42524A;">
                <b>客舟行踪</b>：唐玄宗开元十三年，25岁的李白乘一叶扁舟出蜀游洞庭、下长江，船至当涂，仰望天门山。<br>
                <b>少年心境</b>：初出峡门，胸中充溢着少年游侠的豪气与对大好河山的深情眷恋！<br>
            </div>
            <hr style="border:none; border-top:1px dashed #D6C8B2; margin:12px 0;">
            <div style="font-size:13px; color:#7A6E5A; font-style:italic; line-height:1.6;">
                “天门两阙，长江劈山。李白伫立船头，江风猎猎，提笔写下千古名篇。”
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 一键播放迎客原声
        voice_desc = "阿里百炼 CosyVoice 云端大模型男声"
        if st.button("🔊 听李白哥哥亲口迎客", use_container_width=True):
            welcome_text = libai_agent.get_welcome_message()
            w_audio = tts_service.generate_speech(welcome_text)
            if w_audio and os.path.exists(w_audio):
                st.audio(w_audio, format="audio/mp3", autoplay=True)
        st.caption(f"🎙️ 当前李白声线：`{st.session_state.tts_voice}`（{voice_desc}，可随时在左侧边栏切换）")

# ==================== 舱二：金石之声·朗读测评 ====================
with tab2:
    st.markdown("""
    <div style="margin-bottom:12px;">
        <div style="font-size:21px; font-weight:800; color:#174638; letter-spacing:1px; display:flex; align-items:center; gap:8px;">
            <span>🎙️</span> 金石之声 · 诵读节律台
        </div>
        <div style="font-size:14px; color:#6D7B74; margin-top:4px;">
            “读古诗不能平淡‘唱读’，须注意节拍停顿、动词重音与江水激荡的豪迈情感！”
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_r1, col_r2 = st.columns([1, 1])

    with col_r1:
        st.markdown('<div class="ink-card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:16px; font-weight:700; color:#1C493C; margin-bottom:8px;'>📌 选择诗句研磨诵读节律：</div>", unsafe_allow_html=True)
        selected_line = st.selectbox("诗句选择：", POEM_INFO["lines"], index=0, label_visibility="collapsed")
        
        # 对应诗句标准音律节拍板
        guide_item = next(item for item in READING_GUIDE if item["line"] == selected_line)
        st.markdown(f"""
        <div style="background:#F6F2E9; border:1px solid #DFD5C2; border-radius:10px; padding:14px 16px; margin:12px 0;">
            <div style="font-size:13px; color:#8C7247; font-weight:600; margin-bottom:4px;">🎼 推荐停顿节奏：</div>
            <div style="font-size:18px; font-weight:800; color:#1B4E40; letter-spacing:2px; margin-bottom:8px;">
                {guide_item['rhythm']}
            </div>
            <div style="display:flex; gap:16px; flex-wrap:wrap; font-size:13px; color:#4E5D56;">
                <div><b>🎯 核心重读</b>：<span style="color:#C0392B; font-weight:bold;">{'、'.join(guide_item['stresses'])}</span></div>
                <div><b>💫 情感意境</b>：{guide_item['emotion']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size:14px; font-weight:600; color:#2C4E42; margin-top:10px;'>🎙️ 点击麦克风录音（直接朗读此句）：</div>", unsafe_allow_html=True)
        line_audio = st.audio_input(
            "点击录音",
            key=f"rec_line_{selected_line}",
            label_visibility="collapsed",
        )
        with st.expander("⌨️ 设备无麦克风？可展开手动输入内容"):
            manual_text = st.text_input(
                "手动输入朗读内容：",
                key=f"manual_line_{selected_line}",
                placeholder=f"例如：{selected_line}",
            )

        if st.button("🚀 开始 AI 朗读测评", type="primary", use_container_width=True):
            spoken_text, source = "", ""
            if line_audio is not None:
                with st.spinner("李白哥哥正竖起耳朵听你朗读..."):
                    spoken_text = asr_service.transcribe_bytes(line_audio.getvalue())
                source = "语音识别"
            if not spoken_text and manual_text.strip():
                spoken_text = manual_text.strip()
                source = "手动输入"

            if not spoken_text:
                st.warning("李白哥哥没听清呢～请先点上面麦克风录音，或展开「手动输入」填写。")
            else:
                result = reader_evaluator.evaluate_line(selected_line, spoken_text)
                st.session_state.stars_earned += result["score"]
                st.caption(f"李白哥哥听到的是：【{spoken_text}】（{source}）")
                st.markdown(f"<div style='font-size:24px; font-weight:bold; color:#E67E22; margin:8px 0;'>测评星级：{result['stars']}</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background:#EEF7F2; border-left:4px solid #2B6B58; border-radius:8px; padding:12px 16px; margin:8px 0;">
                    <div style="font-weight:700; color:#1C493C; font-size:14px;">💡 李白哥哥的朗读锦囊：</div>
                    <div style="color:#2C4E42; font-size:14px; margin-top:4px; line-height:1.6;">{result['feedback']}</div>
                </div>
                """, unsafe_allow_html=True)

                # 李白语音点评
                eval_voice = tts_service.generate_speech(result["feedback"])
                if eval_voice:
                    st.audio(eval_voice)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r2:
        st.markdown('<div class="ink-card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:16px; font-weight:700; color:#1C493C; margin-bottom:4px;'>🌟 全诗流利诵读大挑战</div>", unsafe_allow_html=True)
        st.caption("把整首《望天门山》一口气背诵出来，接受李白的综合检阅！")
        
        st.markdown("<div style='font-size:14px; font-weight:600; color:#2C4E42; margin-top:8px;'>🎙️ 对着麦克风一口气背完全诗：</div>", unsafe_allow_html=True)
        full_audio = st.audio_input(
            "全诗背诵录音",
            key="rec_full_poem",
            label_visibility="collapsed"
        )
        with st.expander("⌨️ 没有麦克风？可手动输入全诗文本"):
            full_manual = st.text_area(
                "手动输入全诗背诵内容：",
                placeholder="天门中断楚江开，碧水东流至此回。两岸青山相对出，孤帆一片日边来。"
            )

        if st.button("🏆 提交全诗诵读大比拼", type="primary", use_container_width=True):
            full_spoken, full_source = "", ""
            if full_audio is not None:
                with st.spinner("李白哥哥正凝神聆听你的全诗朗诵..."):
                    full_spoken = asr_service.transcribe_bytes(full_audio.getvalue())
                full_source = "语音识别"
            if not full_spoken and full_manual.strip():
                full_spoken = full_manual.strip()
                full_source = "手动输入"

            if not full_spoken:
                st.warning("李白哥哥还没听到你的背诵呢！请先点上方麦克风录音，或展开「手动输入」填写。")
            else:
                full_res = reader_evaluator.evaluate_full_poem(full_spoken)
                award_badge(full_res["badge"], 5)
                st.balloons()
                st.caption(f"李白哥哥听到的背诵是：【{full_spoken}】（{full_source}）")
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #FFF9EB 0%, #FFF1D6 100%); border:2px solid #E5C378; border-radius:12px; padding:18px; text-align:center; margin:12px 0;">
                    <div style="font-size:30px; letter-spacing:4px; margin-bottom:6px;">{full_res['total_stars']}</div>
                    <div style="font-size:18px; font-weight:800; color:#8C6424;">恭获雅称：【{full_res['badge']}】</div>
                    <p style="font-size:15px; color:#2B6B58; margin-top:8px; line-height:1.7;">{full_res['overall_comment']}</p>
                </div>
                """, unsafe_allow_html=True)
                full_voice = tts_service.generate_speech(full_res['overall_comment'])
                if full_voice:
                    st.audio(full_voice)
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== 舱三：诗境入画·诗画工坊 ====================
with tab3:
    st.markdown("""
    <div style="margin-bottom:12px;">
        <div style="font-size:21px; font-weight:800; color:#174638; letter-spacing:1px; display:flex; align-items:center; gap:8px;">
            <span>🎨</span> 诗境入画 · 青绿水墨工坊
        </div>
        <div style="font-size:14px; color:#6D7B74; margin-top:4px;">
            “以诗入画，画中有诗。展开想象的翅膀，把大自然的神奇造化绘于青绿长卷之上！”
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.markdown('<div class="ink-card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:16px; font-weight:700; color:#1C493C; margin-bottom:6px;'>📜 选一句最动人的诗句入画：</div>", unsafe_allow_html=True)
        paint_line = st.selectbox("挑选诗句：", POEM_INFO["lines"], index=2, label_visibility="collapsed")
        
        st.markdown("<div style='font-size:14px; font-weight:600; color:#2C4E42; margin:10px 0 4px 0;'>✍️ 用你的话写 2~3 句山水描写（B 提高层任务）：</div>", unsafe_allow_html=True)
        user_desc = st.text_area(
            "描写文本：",
            value="江水绿得像一块翡翠，两岸的大山青翠挺拔，像两位巨人一样从江水两边走出来迎接过往的小船！",
            height=95,
            label_visibility="collapsed"
        )
        gen_img_btn = st.button("🖌️ 召唤 AI 挥毫绘制青绿水墨长卷", type="primary", use_container_width=True)
        
        # 提示词透传预览
        prompt_preview = image_service.generate_poem_prompt(user_desc)
        with st.expander("🔍 探秘：AI 绘画提示词（Prompt 架构）"):
            st.code(prompt_preview, language="text")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_p2:
        st.markdown('<div class="ink-card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:16px; font-weight:700; color:#1C493C; margin-bottom:8px;'>🖼️ 传统立轴装裱 · 诗意画卷</div>", unsafe_allow_html=True)
        if gen_img_btn:
            with st.spinner("李白哥哥正在调和石青石绿，在宣纸上挥毫泼墨..."):
                scroll_path = image_service.render_ink_scroll(
                    student_name=st.session_state.student_name,
                    line_selected=paint_line,
                    user_description=user_desc
                )
                st.session_state.last_generated_scroll = scroll_path
                award_badge("诗情画意小能手", 3)
                
                # 李白题画点评
                paint_cheer = f"太绝妙了！{st.session_state.student_name}小诗人的想象力真丰富！这幅水墨天门山正是当年李白哥哥眼中的奇景！"
                st.success(paint_cheer)
                p_audio = tts_service.generate_speech(paint_cheer)
                if p_audio:
                    st.audio(p_audio)

        if st.session_state.last_generated_scroll and os.path.exists(st.session_state.last_generated_scroll):
            # 传统书画装裱画框容器
            st.markdown("""
            <div style="background:#5C4033; padding:6px 16px; border-radius:8px 8px 0 0; text-align:center; color:#E5C88F; font-size:12px; letter-spacing:2px; font-weight:bold;">
                ▲ 中国传统书画装裱轴 · 宣纸真迹 ▲
            </div>
            """, unsafe_allow_html=True)
            st.image(st.session_state.last_generated_scroll, caption=f"小诗人【{st.session_state.student_name}】与青年李白 共创《天门诗画长卷》", use_container_width=True)
            st.markdown("""
            <div style="background:#5C4033; height:8px; border-radius:0 0 8px 8px; margin-bottom:12px;"></div>
            """, unsafe_allow_html=True)
            
            # 画作下载按钮
            with open(st.session_state.last_generated_scroll, "rb") as f_img:
                img_bytes = f_img.read()
            st.download_button(
                label="📥 保存我的天门诗画长卷（高清）",
                data=img_bytes,
                file_name=f"天门诗画卷_{st.session_state.student_name}.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.markdown("""
            <div style="background:#FAF7F0; border:2px dashed #D6C8B2; border-radius:10px; padding:45px 20px; text-align:center; color:#8C7B65;">
                <div style="font-size:36px; margin-bottom:8px;">🎨</div>
                <div style="font-size:15px; font-weight:700;">画卷虚位以待</div>
                <div style="font-size:13px; margin-top:4px;">在左侧写好山水诗意，点击按钮即可现场渲染装裱大作！</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ==================== 诗画对比 · 意象联动探究卷轴 ====================
    st.markdown("---")
    st.markdown("""
    <div style="margin-bottom:10px;">
        <div style="font-size:18px; font-weight:800; color:#174638; display:flex; align-items:center; gap:6px;">
            <span>📜</span> 诗中有画 · 意象联动对照台
        </div>
        <div style="font-size:13px; color:#6D7B74; margin-top:2px;">
            拨动下方游标，探究古诗词句与画面意象如何“字字化境、步步生景”：
        </div>
    </div>
    """, unsafe_allow_html=True)

    image_elements = [
        {"id": 0, "name": "1. 劈山巨门 (天门中断楚江开)", "line": "天门中断楚江开", "keyword": "中断、楚江开", "visual": "天门双峰一左一右立于江岸，如同一柄巨斧将大山从中劈开，江水夺门而出！", "poem_styled": "<span style='color:#C0392B; font-weight:bold; font-size:23px; background:rgba(192,57,43,0.08); padding:2px 8px; border-radius:4px;'>天门中断楚江开</span><br><span style='color:#777; line-height:2.2;'>碧水东流至此回<br>两岸青山相对出<br>孤帆一片日边来</span>"},
        {"id": 1, "name": "2. 碧浪回旋 (碧水东流至此回)", "line": "碧水东流至此回", "keyword": "碧水、至此回", "visual": "浩浩荡荡的长江水奔腾至天门山狭窄处，撞击峭壁，形成回旋澎湃的巨大水涡！", "poem_styled": "<span style='color:#777; line-height:2.2;'>天门中断楚江开</span><br><span style='color:#256150; font-weight:bold; font-size:23px; background:rgba(37,97,80,0.08); padding:2px 8px; border-radius:4px;'>碧水东流至此回</span><br><span style='color:#777; line-height:2.2;'>两岸青山相对出<br>孤帆一片日边来</span>"},
        {"id": 2, "name": "3. 舟行山迎 (两岸青山相对出)", "line": "两岸青山相对出", "keyword": "青山、相对出", "visual": "轻舟顺流如箭，原本静止的两岸青山仿佛生出双脚，从水里迈步迎面扑来！", "poem_styled": "<span style='color:#777; line-height:2.2;'>天门中断楚江开<br>碧水东流至此回</span><br><span style='color:#16A085; font-weight:bold; font-size:23px; background:rgba(22,160,133,0.08); padding:2px 8px; border-radius:4px;'>两岸青山相对出</span><br><span style='color:#777; line-height:2.2;'>孤帆一片日边来</span>"},
        {"id": 3, "name": "4. 日边孤舟 (孤帆一片日边来)", "line": "孤帆一片日边来", "keyword": "孤帆、日边来", "visual": "红日东升朝霞绚烂，天水交接处，一叶白帆乘风破浪缓缓驶来，豪情万丈！", "poem_styled": "<span style='color:#777; line-height:2.2;'>天门中断楚江开<br>碧水东流至此回<br>两岸青山相对出</span><br><span style='color:#D35400; font-weight:bold; font-size:23px; background:rgba(211,84,0,0.08); padding:2px 8px; border-radius:4px;'>孤帆一片日边来</span>"}
    ]

    selected_slider_idx = st.slider(
        "🎚️ 意象对照游标：",
        min_value=0,
        max_value=3,
        value=2,
        format="%d"
    )
    current_elem = image_elements[selected_slider_idx]

    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        st.markdown(f"""
        <div style="background:#FFFDF9; border:2px solid #E2D5BE; border-left:6px solid #C0392B; padding:18px 20px; border-radius:12px; box-shadow:0 3px 10px rgba(0,0,0,0.04); text-align:center;">
            <div style="font-size:12px; color:#A4947C; letter-spacing:2px; margin-bottom:4px;">【墨韵诗碑对照】</div>
            {current_elem['poem_styled']}
        </div>
        """, unsafe_allow_html=True)

    with col_v2:
        st.markdown(f"""
        <div style="background:#F4F8F6; border:1px solid #C9DFD6; border-left:6px solid #2B6B58; padding:18px 20px; border-radius:12px; box-shadow:0 3px 10px rgba(0,0,0,0.04);">
            <div style="font-size:16px; font-weight:800; color:#1C493C; margin-bottom:8px;">🔍 意象精微剖析：{current_elem['name']}</div>
            <div style="font-size:14px; margin-bottom:6px;"><b>核心动词</b>：<mark style='background:#FFE699; padding:2px 8px; border-radius:4px; font-weight:bold; color:#7A4F00;'>{current_elem['keyword']}</mark></div>
            <div style='color:#31443B; font-size:14px; line-height:1.7;'><b>画中美感</b>：{current_elem['visual']}</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== 舱四：层楼更上·分层闯关 ====================
with tab4:
    st.markdown("""
    <div style="margin-bottom:14px;">
        <div style="font-size:21px; font-weight:800; color:#174638; letter-spacing:1px; display:flex; align-items:center; gap:8px;">
            <span>🏔️</span> 登高望远 · 三年级分层研学阁
        </div>
        <div style="font-size:14px; color:#6D7B74; margin-top:4px;">
            “因材施教，步步登高。根据自身掌握情况自由闯关，全部挑战成功即可荣登翰林金榜！”
        </div>
    </div>
    """, unsafe_allow_html=True)

    t_cols = st.columns(3)

    # 关卡 A
    with t_cols[0]:
        st.markdown("""
        <div style="background:#F6FAF8; border:2px solid #C8DDD4; border-radius:12px; padding:18px; position:relative; min-height:180px;">
            <div style="font-size:17px; font-weight:800; color:#1B4E40; margin-bottom:6px;">🥉 A 基础层 · 书童关</div>
            <div style="font-size:12px; color:#7D683A; background:#FFF4DB; padding:2px 8px; border-radius:4px; display:inline-block; font-weight:bold; margin-bottom:8px;">熟读成诵勋章</div>
            <ul style="font-size:13px; color:#3E534A; padding-left:18px; line-height:1.8; margin-bottom:0;">
                <li>读准生字字音，节奏停顿正确</li>
                <li>流利背诵全诗，说出山水大意</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("完成 A 层打卡", use_container_width=True):
            if award_badge(TIER_TASKS["A"]["badge"], 2):
                st.success("🎉 已获得：熟读成诵勋章！")
            else:
                st.info("这枚勋章你已经拿到啦，去挑战下一关吧！")

    # 关卡 B
    with t_cols[1]:
        st.markdown("""
        <div style="background:#FFFDF7; border:2px solid #E8DCB8; border-radius:12px; padding:18px; position:relative; min-height:180px;">
            <div style="font-size:17px; font-weight:800; color:#8C6424; margin-bottom:6px;">🥈 B 提高层 · 画家关</div>
            <div style="font-size:12px; color:#7D683A; background:#FFF4DB; padding:2px 8px; border-radius:4px; display:inline-block; font-weight:bold; margin-bottom:8px;">诗情画意勋章</div>
            <ul style="font-size:13px; color:#4E4738; padding-left:18px; line-height:1.8; margin-bottom:0;">
                <li>闭眼想象天门山动态奇景</li>
                <li>写 2~3 句生动描写，合成诗画图卷</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("完成 B 层打卡", use_container_width=True):
            if award_badge(TIER_TASKS["B"]["badge"], 3):
                st.success("🎨 已获得：诗情画意勋章！")
            else:
                st.info("这枚勋章你已经拿到啦，去挑战下一关吧！")

    # 关卡 C
    with t_cols[2]:
        st.markdown("""
        <div style="background:#FFF9F2; border:2px solid #ECCBA5; border-radius:12px; padding:18px; position:relative; min-height:180px;">
            <div style="font-size:17px; font-weight:800; color:#B03A2E; margin-bottom:6px;">🥇 C 拓展层 · 诗人关</div>
            <div style="font-size:12px; color:#8C2415; background:#FFE8E3; padding:2px 8px; border-radius:4px; display:inline-block; font-weight:bold; margin-bottom:8px;">青莲逸兴勋章</div>
            <ul style="font-size:13px; color:#543834; padding-left:18px; line-height:1.8; margin-bottom:0;">
                <li>换位体验：与李白同坐在江船上</li>
                <li>写 2 句短诗或赞美山河的小语</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        poem_reply = st.text_input("小诗人在船头写的小诗：", placeholder="孤舟顺水过天门，碧浪青山迎客来。", label_visibility="collapsed")
        if st.button("送给李白哥哥审阅", use_container_width=True):
            if poem_reply.strip():
                award_badge(TIER_TASKS["C"]["badge"], 5)
                st.balloons()
                cheer_c = f"妙极了！‘{poem_reply}’，好一个小才子！李白哥哥要举杯为你喝彩！"
                st.success(cheer_c)
                c_voice = tts_service.generate_speech(cheer_c)
                if c_voice:
                    st.audio(c_voice)

    st.markdown("---")
    st.markdown("<div style='font-size:18px; font-weight:800; color:#174638; margin-bottom:8px;'>📜 翰林金榜 · 天门山研学结业证书</div>", unsafe_allow_html=True)
    if len(st.session_state.unlocked_badges) >= 1:
        cert_id = f"TMS-{int(time.time()) % 1000000:06d}"
        badge_str = "、".join(st.session_state.unlocked_badges)
        cert_html = f"""<div style="background:#FFFDF5; border:3px solid #C0392B; outline:1px solid #D4AF37; outline-offset:-6px; border-radius:16px; padding:32px 36px; box-shadow:0 8px 30px rgba(120,40,30,0.12); position:relative; margin:16px 0; text-align:center;">
<div style="position:absolute; top:12px; left:16px; font-size:24px; opacity:0.6;">🏮</div>
<div style="position:absolute; top:12px; right:16px; font-size:24px; opacity:0.6;">🏮</div>
<div style="font-size:14px; color:#A48650; letter-spacing:4px; margin-bottom:6px; font-weight:700;">★ 统编小学语文三年级研学认证 ★</div>
<div style="font-size:32px; font-weight:900; color:#C0392B; letter-spacing:5px; margin-bottom:16px; font-family:'Noto Serif SC', serif;">天门山研学结业金榜</div>
<div style="font-size:18px; font-weight:700; color:#224438; margin-bottom:12px; text-align:left; text-indent:2em;">兹证明 <span style="color:#C0392B; border-bottom:2px solid #C0392B; padding:0 8px; font-size:20px;">{st.session_state.student_name}</span> 小诗人：</div>
<div style="font-size:16px; color:#3A4D45; line-height:2.2; text-align:left; text-indent:2em; margin-bottom:20px;">在《望天门山》诗画互译沉浸式数字化研学课堂中，与青年李白探讨楚江劈山之奇，共研金石声律，泼墨同绘青绿山水卷，累计荣获 <b style="color:#E67E22; font-size:18px;">{st.session_state.stars_earned}</b> 颗研学星，荣膺 <b>{badge_str}</b>！成绩卓著，特颁此榜！</div>
<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:20px; padding:0 20px;">
<div style="text-align:left; font-size:13px; color:#8C7E6A;">研学档案编号：{cert_id}<br>授课科目：部编版语文三年级上册</div>
<div style="text-align:right;">
<div style="font-size:16px; font-weight:800; color:#1C493C; letter-spacing:2px;">唐 · 青年李白 亲笔题赠</div>
<div style="font-size:13px; color:#8C7E6A; margin-top:2px;">天门山江上客舟中</div>
<div style="display:inline-block; border:2px solid #C0392B; color:#C0392B; font-weight:bold; font-size:12px; padding:2px 8px; border-radius:4px; margin-top:6px; letter-spacing:1px;">太白翰林之印</div>
</div>
</div>
</div>"""
        st.markdown(cert_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#FAF7F0; border:2px dashed #D6C8B2; border-radius:12px; padding:35px 20px; text-align:center; color:#8C7B65;">
            <div style="font-size:32px; margin-bottom:6px;">📜</div>
            <div style="font-size:16px; font-weight:700;">金榜暂未题名</div>
            <div style="font-size:13px; margin-top:4px;">请先在上方完成任意一项闯关打卡，即可解锁你的专属研学证书！</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== 脚本末尾回填侧边栏成就榜 ====================
with star_metric_ph.container():
    st.markdown(f"""
    <div class="honor-shelf-metric">
        <div style="font-size:12px; color:#8C734B; letter-spacing:1px;">⭐ 研学星</div>
        <div class="honor-shelf-num">{st.session_state.stars_earned} <span style="font-size:13px; font-weight:normal;">颗</span></div>
    </div>
    """, unsafe_allow_html=True)

with badge_metric_ph.container():
    st.markdown(f"""
    <div class="honor-shelf-metric">
        <div style="font-size:12px; color:#8C734B; letter-spacing:1px;">🎖️ 荣获勋章</div>
        <div class="honor-shelf-num" style="color:#256150;">{len(st.session_state.unlocked_badges)} <span style="font-size:13px; font-weight:normal;">枚</span></div>
    </div>
    """, unsafe_allow_html=True)

with badge_list_ph.container():
    if st.session_state.unlocked_badges:
        for b in st.session_state.unlocked_badges:
            st.markdown(f'<div class="honor-badge-item"><span>🏅</span><span>{b}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:12px; color:#A49B88; text-align:center; padding:8px 0; letter-spacing:1px;">尚未斩获勋章，快去闯关吧！</div>', unsafe_allow_html=True)
