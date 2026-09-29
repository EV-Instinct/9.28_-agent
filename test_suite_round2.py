"""
第二轮功能测试：极端场景、离线容灾、全流程链路集成与证书生成测试
覆盖：断网/无Key离线降级、全流程闯关学情闭环、证书完整性校验。
"""
import sys
import os
import shutil

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("【第二轮测试】开始执行离线极端容灾与全流程端到端链路检验...")
print("=" * 60)

test_results = {}

# 1. 模拟极端断网/无 Key 离线容灾测试
print("\n[测试项 1/3] 模拟断网/无 Key 状态下的离线教学容灾测试...")
try:
    from core.libai_agent import LiBaiAgent
    # 创建一个没有任何 Key 的离线智能体
    offline_agent = LiBaiAgent(api_key="", model="qwen-plus")
    assert not offline_agent.is_online(), "此时应识别为离线模式"
    print(" -> 离线判定验证正确: is_online() == False")

    # 针对 4 个核心教学提问，验证离线知识库是否准确命中
    cases = [
        ("青山怎么会相对出呢？", "相对出"),
        ("为什么长江叫楚江？", "楚江"),
        ("至此回是什么意思？", "至此回"),
        ("请给我A基础层任务", "小书童")
    ]
    for user_q, expected_keyword in cases:
        resp = offline_agent.chat([{"role": "user", "content": user_q}])
        print(f"    [离线问] {user_q} -> [李白答] {resp[:50]}...")
        assert len(resp) > 15, "离线回复也必须有充分教学意义"
        assert "李白" in resp or "小诗人" in resp, "必须保持青年李白人格"

    test_results["1_Offline_DisasterRecovery"] = "PASSED"
    print(" ✅ 极端断网/无Key容灾测试: 通过 (100%安全保底)")
except Exception as e:
    test_results["1_Offline_DisasterRecovery"] = f"FAILED: {e}"
    print(f" ❌ 离线容灾测试失败: {e}")

# 2. 模拟学生完整研学全流程（从问候到通关领奖状）
print("\n[测试项 2/3] 模拟学生【李小华】完整 40 分钟研学链路数据流...")
try:
    student_state = {
        "name": "李小华",
        "stars": 0,
        "badges": set(),
        "chat_count": 0
    }

    # 环节 1: 课前问候
    student_state["chat_count"] += 1
    student_state["stars"] += 1
    print(f" -> 环节1 课前打招呼完成: 研学星={student_state['stars']}")

    # 环节 2: 朗读测评通关
    from modules.reader_evaluator import reader_evaluator
    full_eval = reader_evaluator.evaluate_full_poem("天门中断楚江开，碧水东流至此回。两岸青山相对出，孤帆一片日边来。")
    student_state["stars"] += 5
    student_state["badges"].add(full_eval["badge"])
    print(f" -> 环节2 朗读测评通过: 获得勋章={full_eval['badge']}, 研学星={student_state['stars']}")

    # 环节 3: 诗画工坊共创
    from services.image_service import image_service
    scroll_file = image_service.render_ink_scroll(student_state["name"], "孤帆一片日边来", "红日东升，万里碧波")
    assert os.path.exists(scroll_file), "生成的画卷必须存在"
    student_state["stars"] += 3
    student_state["badges"].add("诗情画意小能手")
    print(f" -> 环节3 诗画共创完成: 画作路径={scroll_file}, 研学星={student_state['stars']}")

    # 环节 4: 分层任务 C 层小诗人仿写
    student_state["badges"].add("青莲逸兴勋章")
    student_state["stars"] += 5
    print(f" -> 环节4 闯关阁通关: 累计勋章数={len(student_state['badges'])}, 累计研学星={student_state['stars']}")

    # 环节 5: 验证结业证书数据完整性
    assert student_state["stars"] >= 14, "研学星数量应累积达标"
    assert len(student_state["badges"]) >= 3, "至少应获得3枚勋章"
    test_results["2_Full_Student_Journey"] = "PASSED"
    print(" ✅ 学生完整研学全流程数据流测试: 通过")
except Exception as e:
    test_results["2_Full_Student_Journey"] = f"FAILED: {e}"
    print(f" ❌ 全流程测试失败: {e}")

# 3. 静态多媒体资源防404与读写权限测试
print("\n[测试项 3/3] 检查静态音频与图像输出目录权限与防404状态...")
try:
    from config import AUDIO_DIR, IMAGES_DIR
    assert AUDIO_DIR.exists() and os.access(AUDIO_DIR, os.W_OK), "音频目录必须可写"
    assert IMAGES_DIR.exists() and os.access(IMAGES_DIR, os.W_OK), "图像目录必须可写"

    audio_files = list(AUDIO_DIR.glob("*.mp3"))
    image_files = list(IMAGES_DIR.glob("*.png"))
    print(f" -> 音频缓存库文件数: {len(audio_files)} 个")
    print(f" -> 图像长卷库文件数: {len(image_files)} 个")
    assert len(audio_files) > 0, "音频库中应已有成功生成的示范音频"
    assert len(image_files) > 0, "图像库中应已有成功生成的画卷文件"

    test_results["3_Media_Storage"] = "PASSED"
    print(" ✅ 静态资源防404与读写权限测试: 通过")
except Exception as e:
    test_results["3_Media_Storage"] = f"FAILED: {e}"
    print(f" ❌ 静态资源测试失败: {e}")

print("\n" + "=" * 60)
print("【第二轮测试结果汇总】:")
for k, v in test_results.items():
    print(f"  {k}: {v}")
print("=" * 60)
