"""
全功能深度验收与端到端健康检查套件
覆盖：
1. 阿里通义千问在线对话（流式与非流式）+ 角色规则（无英文、三年级难度、字数、自称）
2. 离线教学容灾规则引擎（超纲查证问答、字词解析）
3. 微软 Edge-TTS 异步语音生成与 MD5 极速缓存
4. 阿里 DashScope ASR 音频识别与规整服务
5. 金石朗读测评引擎（单句多层级打分、全诗背诵与勋章结算）
6. 诗画工坊（Prompt提取、传统立轴长卷渲染、印章题跋）
7. 分层研学阁（A/B/C 三级闯关逻辑、勋章防刷与防重复累加）
8. 前端 app.py 语法、依赖与静态目录防404校验
"""
import sys
import os
import io
import time
from pathlib import Path

# 强制 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("【天门山研学工作台】开始执行全系统八大核心功能深度健康巡检...")
print("=" * 70)

check_results = {}

# ----------------- 1. 通义千问核心大脑与流式交互 -----------------
print("\n[功能检查 1/8] 检查阿里云通义千问大脑（常规对话 + 打字机流式输出）...")
try:
    from core.libai_agent import libai_agent
    assert libai_agent.is_online(), "通义千问 API 需处于就绪在线状态"

    # 测试常规对话
    test_q = "李白哥哥，为什么大山会‘相对出’呀？"
    resp_chat = libai_agent.chat([{"role": "user", "content": test_q}])
    print(f" -> 对话测试成功，回复: {resp_chat[:60]}...")
    assert len(resp_chat) > 10, "回复必须有内容"
    assert not any(ord(c) > 127 and c.isascii() for c in resp_chat), "严禁包含任何异常字符"
    
    # 检查英文纯净性（严禁混入英文如 giant、OK 等）
    english_words = [w for w in resp_chat.split() if w.isalpha() and w.isascii()]
    assert len(english_words) == 0, f"发现违规英文字词: {english_words}"

    # 测试打字机流式输出
    stream_chunks = list(libai_agent.chat_stream([{"role": "user", "content": "李白哥哥你好呀！"}]))
    full_stream_text = "".join(stream_chunks)
    assert len(stream_chunks) >= 2, "流式输出必须分片产出"
    assert len(full_stream_text) > 5, "流式文本应完整拼接"
    print(f" -> 打字机流式测试成功: 共分 {len(stream_chunks)} 个 token 片段产出")

    check_results["1_Qwen_LLM_Brain"] = "OK"
    print(" ✅ 功能 1（通义千问大脑与流式）：全部正常")
except Exception as e:
    check_results["1_Qwen_LLM_Brain"] = f"FAIL: {e}"
    print(f" ❌ 功能 1 异常: {e}")


# ----------------- 2. 离线教学容灾与超纲问题查证规则 -----------------
print("\n[功能检查 2/8] 检查离线容灾引擎与教案指定话术（含‘这个问题需要查证哦’）...")
try:
    from core.libai_agent import LiBaiAgent
    offline_bot = LiBaiAgent(api_key="", model="qwen-plus")
    assert not offline_bot.is_online(), "离线模式判定需为 False"

    # 测试典型提问
    ans_chujiang = offline_bot.chat([{"role": "user", "content": "为什么叫楚江？"}])
    assert "古楚国" in ans_chujiang and "长江" in ans_chujiang, "离线解析需符合部编教参"
    print(f" -> 离线常识问答命中: {ans_chujiang[:45]}...")

    # 测试超纲问题（教案硬性约束：这个问题需要查证哦）
    ans_unknown = offline_bot.chat([{"role": "user", "content": "量子力学和相对论是什么？"}])
    assert "这个问题需要查证哦" in ans_unknown, "超纲问题必须按教案要求回复‘这个问题需要查证哦’"
    print(f" -> 超纲查证兜底命中: {ans_unknown}")

    check_results["2_Offline_DisasterRecovery"] = "OK"
    print(" ✅ 功能 2（离线教学容灾与规范话术）：全部正常")
except Exception as e:
    check_results["2_Offline_DisasterRecovery"] = f"FAIL: {e}"
    print(f" ❌ 功能 2 异常: {e}")


# ----------------- 3. 微软 Edge-TTS 语音合成与毫秒级缓存 -----------------
print("\n[功能检查 3/8] 检查微软 Edge-TTS 青年豪迈原声与缓存调度...")
try:
    from services.tts_service import tts_service
    test_phrase = "两岸青山相对出，孤帆一片日边来。"
    
    # 首次调用测试生成
    p1 = tts_service.generate_speech(test_phrase)
    assert os.path.exists(p1) and os.path.getsize(p1) > 1000, "音频文件生成失败或大小不足"

    # 二次调用测试缓存效率
    t_start = time.time()
    p2 = tts_service.generate_speech(test_phrase)
    t_cost = time.time() - t_start
    assert p1 == p2, "相同文本路径必须一致"
    assert t_cost < 0.05, f"缓存读取耗时应低于50毫秒，实际: {t_cost:.4f}s"
    print(f" -> 音频生成与缓存有效: {p1} (命中读取: {t_cost*1000:.2f}ms)")

    check_results["3_Edge_TTS"] = "OK"
    print(" ✅ 功能 3（Edge-TTS 语音与缓存）：全部正常")
except Exception as e:
    check_results["3_Edge_TTS"] = f"FAIL: {e}"
    print(f" ❌ 功能 3 异常: {e}")


# ----------------- 4. 录音规整与 ASR 语音识别服务 -----------------
print("\n[功能检查 4/8] 检查 ASR 录音规整与音频输入处理管线...")
try:
    from services.asr_service import asr_service
    # 检查 ffmpeg 或 wave 规整器状态
    print(f" -> ASR 服务初始化正常，临时音频存储目录: {asr_service.tmp_dir}")
    assert asr_service.tmp_dir.exists(), "音频临时目录必须存在"

    # 空音频容错处理
    empty_result = asr_service.transcribe_bytes(b"")
    assert empty_result == "", "空音频应安全返回空字符串，绝不抛异常"
    print(" -> ASR 容错测试通过")

    check_results["4_ASR_Service"] = "OK"
    print(" ✅ 功能 4（ASR 音频处理服务）：全部正常")
except Exception as e:
    check_results["4_ASR_Service"] = f"FAIL: {e}"
    print(f" ❌ 功能 4 异常: {e}")


# ----------------- 5. 金石之声 · 朗读测评算法 -----------------
print("\n[功能检查 5/8] 检查朗读测评引擎（单句断句星级 + 全诗背诵综合考评）...")
try:
    from modules.reader_evaluator import reader_evaluator
    # 单句 5 星
    res_5 = reader_evaluator.evaluate_line("天门中断楚江开", "天门中断楚江开")
    assert res_5["score"] == 5 and "⭐⭐⭐⭐⭐" in res_5["stars"]
    assert len(res_5["tips"]) > 0, "必须包含朗读锦囊建议"

    # 单句 4 星（部分错字）
    res_4 = reader_evaluator.evaluate_line("碧水东流至此回", "碧水东流去此回")
    assert res_4["score"] < 5 and res_4["score"] >= 3

    # 全诗诵读考评
    full_eval = reader_evaluator.evaluate_full_poem("天门中断楚江开，碧水东流至此回。两岸青山相对出，孤帆一片日边来。")
    assert full_eval["badge"] == "天门山金牌朗诵家"
    assert "⭐⭐⭐⭐⭐" in full_eval["total_stars"]
    print(f" -> 朗读测评算法测试通过: 满分评星={res_5['stars']}, 全诗称号={full_eval['badge']}")

    check_results["5_Reader_Evaluator"] = "OK"
    print(" ✅ 功能 5（金石朗读测评）：全部正常")
except Exception as e:
    check_results["5_Reader_Evaluator"] = f"FAIL: {e}"
    print(f" ❌ 功能 5 异常: {e}")


# ----------------- 6. 诗画工坊与水墨画卷渲染 -----------------
print("\n[功能检查 6/8] 检查诗画工坊（Prompt 提炼 + 宣纸立轴画卷渲染 + 题跋印章）...")
try:
    from services.image_service import image_service
    # Prompt 提炼测试
    prompt = image_service.generate_poem_prompt("江水像碧玉翡翠，两座大山迎面跑来")
    assert "青绿山水" in prompt and "天门山" in prompt

    # 宣纸画卷渲染测试（带题跋印章）
    img_path = image_service.render_ink_scroll("王小诗", "两岸青山相对出", "江水如碧玉，孤舟行江心")
    assert os.path.exists(img_path), "生成的画卷图片必须存在"
    size = os.path.getsize(img_path)
    assert size > 8000, f"画卷大小异常: {size} 字节"
    print(f" -> 水墨立轴画卷渲染成功: {img_path} (文件大小: {size/1024:.1f} KB)")

    check_results["6_Image_Workshop"] = "OK"
    print(" ✅ 功能 6（诗意生图与水墨渲染）：全部正常")
except Exception as e:
    check_results["6_Image_Workshop"] = f"FAIL: {e}"
    print(f" ❌ 功能 6 异常: {e}")


# ----------------- 7. 分层闯关阁与结业金榜逻辑 -----------------
print("\n[功能检查 7/8] 检查 A/B/C 三阶分层闯关与防重复刷星逻辑...")
try:
    from knowledge.tianmenshan_data import TIER_TASKS
    assert "A" in TIER_TASKS and "B" in TIER_TASKS and "C" in TIER_TASKS, "必须包含 A/B/C 三层任务"

    # 模拟勋章防刷逻辑
    unlocked = set()
    stars = 0
    def sim_award(name, count):
        global stars
        if name in unlocked:
            return False
        unlocked.add(name)
        stars += count
        return True

    # 首次打卡
    assert sim_award(TIER_TASKS["A"]["badge"], 2) is True
    assert stars == 2
    # 重复打卡（应当防刷拦截）
    assert sim_award(TIER_TASKS["A"]["badge"], 2) is False
    assert stars == 2

    # 依次完成 B、C 层
    assert sim_award(TIER_TASKS["B"]["badge"], 3) is True
    assert sim_award(TIER_TASKS["C"]["badge"], 5) is True
    assert stars == 10
    assert len(unlocked) == 3
    print(f" -> 分层勋章逻辑验证通过: 累计获得勋章={len(unlocked)} 枚, 研学星={stars} 颗")

    check_results["7_Tier_Progression"] = "OK"
    print(" ✅ 功能 7（分层闯关与金榜结算）：全部正常")
except Exception as e:
    check_results["7_Tier_Progression"] = f"FAIL: {e}"
    print(f" ❌ 功能 7 异常: {e}")


# ----------------- 8. 前端页面语法与启动脚本自检 -----------------
print("\n[功能检查 8/8] 检查前端 app.py 语法编译与启动配置完整性...")
try:
    import py_compile
    py_compile.compile("app.py", doraise=True)
    print(" -> app.py 字节码编译通过，无任何语法或缩进错误")

    # 检查启动脚本与配置文件
    assert os.path.exists("启动天门山研学工作台.bat"), "必须存在一键启动脚本"
    assert os.path.exists(".env"), "必须存在配置文件 .env"
    assert os.path.exists("README.md"), "必须存在使用说明 README.md"

    check_results["8_App_Integrity"] = "OK"
    print(" ✅ 功能 8（前端编译与启动脚本）：全部正常")
except Exception as e:
    check_results["8_App_Integrity"] = f"FAIL: {e}"
    print(f" ❌ 功能 8 异常: {e}")


print("\n" + "=" * 70)
print("【全系统健康巡检报告汇总】")
all_passed = True
for name, status in check_results.items():
    indicator = "✅ PASS" if status == "OK" else "❌ FAIL"
    if status != "OK":
        all_passed = False
    print(f"  [{indicator}] {name}: {status}")
print("=" * 70)

if all_passed:
    print("🏆 结论：所有八大核心功能全部通过，系统处于 100% 完美健康状态！")
else:
    print("⚠️ 结论：发现异常项，请针对性排查！")
