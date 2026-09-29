"""
第一轮功能测试：全模块白盒与核心业务逻辑自动化测试套件
覆盖：Qwen大模型通义千问对话、Edge-TTS语音与缓存、朗读评测算法、图像生成、分层任务数据。
"""
import sys
import os
from pathlib import Path

# 强制 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("【第一轮测试】开始执行全模块白盒与业务逻辑检验...")
print("=" * 60)

test_results = {}

# 1. 测试通义千问在线李白对话
print("\n[测试项 1/5] 测试通义千问 LLM 对话能力与青年李白人设...")
try:
    from core.libai_agent import libai_agent
    is_online = libai_agent.is_online()
    print(f" -> 检查模型在线连接状态: {is_online}")
    assert is_online, "通义千问 API 应该处于在线连接状态"

    # 模拟三年级典型问题
    test_questions = [
        "李白哥哥，为什么长江水流到天门山会‘至此回’？",
        "李白哥哥你几岁了？你当时乘的船长什么样？"
    ]
    for q in test_questions:
        reply = libai_agent.chat([{"role": "user", "content": q}])
        print(f"    Q: {q}")
        print(f"    A (李白): {reply[:80]}...")
        assert len(reply) > 10, "回复长度应大于10字"
        assert any(k in reply for k in ["李白", "我", "小诗人", "哥哥"]), "应体现李白与学生的互动身份"
    test_results["1_LLM_Qwen"] = "PASSED"
    print(" ✅ 通义千问对话与人设测试: 通过")
except Exception as e:
    test_results["1_LLM_Qwen"] = f"FAILED: {e}"
    print(f" ❌ 通义千问测试失败: {e}")

# 2. 测试 Edge-TTS 语音合成与缓存机制
print("\n[测试项 2/5] 测试微软 Edge-TTS 语音合成与文件生成...")
try:
    from services.tts_service import tts_service
    test_text = "小朋友你好，我是青年李白，欢迎来到天门山！"
    # 第一次生成
    audio_path1 = tts_service.generate_speech(test_text)
    print(f" -> 首次音频生成路径: {audio_path1}")
    assert os.path.exists(audio_path1), "生成的音频文件必须真实存在"
    assert os.path.getsize(audio_path1) > 1000, "音频文件大小应大于1KB"

    # 第二次生成（测试缓存命中速度）
    import time
    t0 = time.time()
    audio_path2 = tts_service.generate_speech(test_text)
    t_diff = time.time() - t0
    assert audio_path1 == audio_path2, "相同文本应命中同一缓存文件"
    assert t_diff < 0.1, f"缓存命中应在0.1秒内完成，实际耗时: {t_diff:.3f}s"
    print(f" -> 缓存命中耗时: {t_diff:.4f}s")
    test_results["2_EdgeTTS"] = "PASSED"
    print(" ✅ Edge-TTS 语音合成与缓存机制: 通过")
except Exception as e:
    test_results["2_EdgeTTS"] = f"FAILED: {e}"
    print(f" ❌ TTS 测试失败: {e}")

# 3. 测试朗读测评引擎
print("\n[测试项 3/5] 测试金石之声朗读测评算法（单句与全诗）...")
try:
    from modules.reader_evaluator import reader_evaluator
    # 满分测试
    line_eval_full = reader_evaluator.evaluate_line("两岸青山相对出", "两岸青山相对出")
    print(f" -> 满分单句测评: 得分={line_eval_full['score']}, 星级={line_eval_full['stars']}")
    assert line_eval_full["score"] == 5, "完全正确朗读应为5星"

    # 错误/漏字测试
    line_eval_partial = reader_evaluator.evaluate_line("两岸青山相对出", "两岸大山相对")
    print(f" -> 漏字单句测评: 得分={line_eval_partial['score']}, 星级={line_eval_partial['stars']}")
    assert line_eval_partial["score"] < 5, "部分匹配不应得5星"
    assert len(line_eval_partial["tips"]) > 0, "应包含教学锦囊指导"

    # 全诗流利度测试
    full_eval = reader_evaluator.evaluate_full_poem("天门中断楚江开，碧水东流至此回。两岸青山相对出，孤帆一片日边来。")
    print(f" -> 全诗测评评定: 称号={full_eval['badge']}, 评价={full_eval['overall_comment'][:35]}...")
    assert "金牌朗诵家" in full_eval["badge"], "全对朗诵应解锁金牌朗诵家"
    test_results["3_ReaderEvaluator"] = "PASSED"
    print(" ✅ 朗读测评引擎测试: 通过")
except Exception as e:
    test_results["3_ReaderEvaluator"] = f"FAILED: {e}"
    print(f" ❌ 朗读测评失败: {e}")

# 4. 测试诗画工坊与画卷渲染
print("\n[测试项 4/5] 测试诗画工坊与双轨画卷渲染...")
try:
    from services.image_service import image_service
    # 测试 Prompt 提取
    prompt = image_service.generate_poem_prompt("江水像碧玉一样流淌，远处的白帆迎着太阳")
    assert "青绿山水" in prompt and "天门山" in prompt, "Prompt 中应包含中国山水与核心意象"
    print(f" -> 自动提取生图 Prompt: {prompt[:60]}...")

    # 测试本地水墨渲染
    img_path = image_service.render_ink_scroll("张小乐同学", "孤帆一片日边来", "江水碧绿，孤舟远航")
    assert os.path.exists(img_path), "生成的画卷图片必须真实存在"
    assert os.path.getsize(img_path) > 5000, "画卷文件大小应正常"
    print(f" -> 画卷生成成功: {img_path} (大小: {os.path.getsize(img_path)} 字节)")
    test_results["4_ImageService"] = "PASSED"
    print(" ✅ 诗画工坊与水墨画卷渲染测试: 通过")
except Exception as e:
    test_results["4_ImageService"] = f"FAILED: {e}"
    print(f" ❌ 图像生成测试失败: {e}")

# 5. 测试教材知识库数据结构完整性
print("\n[测试项 5/5] 测试统编版知识库完整性与分层任务定义...")
try:
    from knowledge.tianmenshan_data import POEM_INFO, WORD_GLOSSARY, READING_GUIDE, TIER_TASKS
    assert len(POEM_INFO["lines"]) == 4, "全诗必须正好4句"
    assert len(WORD_GLOSSARY) >= 6, "至少包含6个部编重点字词"
    assert set(TIER_TASKS.keys()) == {"A", "B", "C"}, "分层任务必须包含A、B、C三阶"
    print(f" -> 知识库验证通过: 覆盖字词={len(WORD_GLOSSARY)}个, 分层阶段={list(TIER_TASKS.keys())}")
    test_results["5_KnowledgeBase"] = "PASSED"
    print(" ✅ 知识库数据结构测试: 通过")
except Exception as e:
    test_results["5_KnowledgeBase"] = f"FAILED: {e}"
    print(f" ❌ 知识库数据测试失败: {e}")

print("\n" + "=" * 60)
print("【第一轮测试结果汇总】:")
for k, v in test_results.items():
    print(f"  {k}: {v}")
print("=" * 60)
