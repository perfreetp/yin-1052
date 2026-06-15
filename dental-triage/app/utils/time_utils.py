import re
from datetime import datetime
from typing import Optional

WEEKDAY_MAP = {
    "周一": 0,
    "周二": 1,
    "周三": 2,
    "周四": 3,
    "周五": 4,
    "周六": 5,
    "周日": 6,
    "星期日": 6,
    "礼拜一": 0,
    "礼拜二": 1,
    "礼拜三": 2,
    "礼拜四": 3,
    "礼拜五": 4,
    "礼拜六": 5,
    "礼拜天": 6,
}


def parse_business_hours(business_hours: str) -> list[bool]:
    """
    解析营业时段字符串，返回长度为7的布尔数组，索引0=周一...6=周日
    支持格式：
      "周一至周日 09:00-18:00"
      "周一至周六 09:00-17:30"
      "周二,周四,周六 10:00-20:00"
    """
    if not business_hours:
        return [True] * 7

    weekday_flags = [False] * 7
    text = business_hours.strip()

    range_match = re.search(r"(周[一二三四五六日])\s*至\s*(周[一二三四五六日])", text)
    if range_match:
        start_kw = range_match.group(1)
        end_kw = range_match.group(2)
        start_idx = WEEKDAY_MAP.get(start_kw, 0)
        end_idx = WEEKDAY_MAP.get(end_kw, 6)
        if start_idx <= end_idx:
            for i in range(start_idx, end_idx + 1):
                weekday_flags[i] = True
        else:
            for i in range(start_idx, 7):
                weekday_flags[i] = True
            for i in range(0, end_idx + 1):
                weekday_flags[i] = True
        return weekday_flags

    for kw, idx in WEEKDAY_MAP.items():
        if kw in text:
            weekday_flags[idx] = True

    if not any(weekday_flags):
        return [True] * 7

    return weekday_flags


def infer_target_weekday(preferred_time: Optional[str]) -> Optional[int]:
    """
    从期望时间文本推断目标星期几（0=周一, 6=周日）
    无法推断时返回 None
    """
    if not preferred_time:
        return None

    for kw, idx in WEEKDAY_MAP.items():
        if kw in preferred_time:
            return idx

    if "今天" in preferred_time:
        return datetime.now().weekday()
    if "明天" in preferred_time:
        return (datetime.now().weekday() + 1) % 7
    if "后天" in preferred_time:
        return (datetime.now().weekday() + 2) % 7

    return None


def is_clinic_open_on(clinic_business_hours: str, target_weekday: Optional[int]) -> bool:
    """
    判断院区在目标星期几是否营业
    target_weekday 为 None 时默认返回 True
    """
    if target_weekday is None:
        return True
    open_days = parse_business_hours(clinic_business_hours)
    return open_days[target_weekday]
