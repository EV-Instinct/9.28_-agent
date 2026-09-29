"""
金石之声 · 朗读测评引擎

面向小学三年级，对《望天门山》朗读做准确的评判与激励性反馈。

评分核心：把学生朗读（麦克风识别文本或手动输入）与标准诗句做 **序列比对**
（编辑距离 + 差异定位），能真正判出漏字、多字与语序颠倒。

注意：旧版用「字符是否在输入中出现过」计算命中率，导致乱序、甚至整首诗
都能拿满分；现已改为编辑距离相似度，乱序会明显扣分。
"""
import re
import difflib
from typing import Dict, Any, Tuple

from knowledge.tianmenshan_data import READING_GUIDE, POEM_INFO

# 只保留汉字与字母数字，去掉空格与全部标点
_CLEAN_RE = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9]")


class ReaderEvaluator:
    def __init__(self):
        self.guide = {item["line"]: item for item in READING_GUIDE}
        self.standard_poem = POEM_INFO["lines"]

    # ---------------- 文本比对工具 ----------------
    @staticmethod
    def _clean(text: str) -> str:
        return _CLEAN_RE.sub("", text or "")

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        """编辑距离（短句场景，纯 Python 实现足够快）"""
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
            prev = cur
        return prev[-1]

    @classmethod
    def _similarity(cls, student: str, target: str) -> float:
        """相似度 = 1 - 编辑距离 / 较长串长度"""
        if not student or not target:
            return 0.0
        dist = cls._levenshtein(student, target)
        return max(0.0, 1.0 - dist / max(len(student), len(target)))

    @classmethod
    def _diff_detail(cls, student: str, target: str) -> Tuple[str, str]:
        """定位差异，返回（漏读的字, 多读或读错的字）"""
        matcher = difflib.SequenceMatcher(None, student, target)
        missing, extra = [], []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ("insert", "replace"):
                missing.append(target[j1:j2])   # 标准里有、学生没读到
            if tag in ("delete", "replace"):
                extra.append(student[i1:i2])    # 学生读了、标准里没有
        return "".join(missing), "".join(extra)

    # ---------------- 单句测评 ----------------
    def evaluate_line(self, line_text: str, student_input: str) -> Dict[str, Any]:
        """单句朗读分析与评星"""
        guide_item = self.guide.get(line_text, {})
        clean_target = self._clean(line_text)
        clean_input = self._clean(student_input)

        if not clean_input:
            return {
                "score": 1,
                "stars": "⭐",
                "similarity": 0.0,
                "feedback": "小诗人，李白哥哥还没听清你的朗读呢，再来一次吧！",
                "tips": guide_item.get("tips", ""),
            }

        similarity = self._similarity(clean_input, clean_target)

        if similarity >= 0.95:
            score, stars = 5, "⭐⭐⭐⭐⭐"
            feedback = f"太精彩了，字正腔圆！{guide_item.get('tips', '')}"
        elif similarity >= 0.8:
            score, stars = 4, "⭐⭐⭐⭐"
            feedback = f"读得很有气势，就差一点点啦！{guide_item.get('tips', '')}"
        elif similarity >= 0.6:
            score, stars = 3, "⭐⭐⭐"
            feedback = f"基本读对啦！我们按这个节奏再来一遍：【{guide_item.get('rhythm', '')}】"
        else:
            score, stars = 2, "⭐⭐"
            feedback = f"别着急，跟着李白哥哥慢慢念一遍：‘{line_text}’，注意每个字的顺序哦！"

        # 差异诊断：给出具体的漏读/多读位置，而不是笼统鼓励
        if similarity < 0.95:
            missing, extra = self._diff_detail(clean_input, clean_target)
            details = []
            if missing:
                details.append(f"漏读了「{missing}」")
            if extra:
                details.append(f"多读或读错了「{extra}」")
            if details:
                feedback += "　（" + "，".join(details) + "）"

        return {
            "score": score,
            "stars": stars,
            "similarity": round(similarity, 3),
            "feedback": feedback,
            "rhythm": guide_item.get("rhythm", ""),
            "stresses": guide_item.get("stresses", []),
            "emotion": guide_item.get("emotion", ""),
            "tips": guide_item.get("tips", ""),
        }

    # ---------------- 全诗测评 ----------------
    def evaluate_full_poem(self, student_input: str) -> Dict[str, Any]:
        """全诗朗读测评与综合评定"""
        clean_input = self._clean(student_input)
        clean_target = "".join(self.standard_poem)

        # 逐句结果：按句长顺序截取对应片段
        cursor = 0
        line_results = []
        for line in self.standard_poem:
            segment = clean_input[cursor: cursor + len(line)]
            cursor += len(line)
            line_results.append({"line": line, "eval": self.evaluate_line(line, segment)})

        overall_ratio = self._similarity(clean_input, clean_target)

        if overall_ratio >= 0.9:
            total_stars, badge = 5, "天门山金牌朗诵家"
            overall_comment = "天籁之声！小诗人，你把长江波澜壮阔的气势完全读出来了！"
        elif overall_ratio >= 0.75:
            total_stars, badge = 4, "江上行舟小百灵"
            overall_comment = "字句流畅，节奏分明！再把后两句读得更有画面感，就完美啦！"
        elif overall_ratio >= 0.55:
            total_stars, badge = 3, "勤学好问小书童"
            overall_comment = "读得挺完整！注意每句中间的小停顿，别太心急，感受江水回旋的韵味。"
        else:
            total_stars, badge = 2, "蓄力小雏鹰"
            overall_comment = "多读两遍，诗句的音乐美就会流淌出来哦，李白哥哥陪你一起练！"

        return {
            "total_stars": "⭐" * total_stars,
            "score_numeric": total_stars * 20,
            "similarity": round(overall_ratio, 3),
            "badge": badge,
            "overall_comment": overall_comment,
            "line_results": line_results,
        }


# 导出评测实例
reader_evaluator = ReaderEvaluator()
