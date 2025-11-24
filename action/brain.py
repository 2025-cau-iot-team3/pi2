import json
from pathlib import Path
import math

CONFIG_PATH = Path(__file__).resolve().parent.parent / "cfg" / "objectConfig.json"


def _load_preferences():
    prefs = {}
    if not CONFIG_PATH.exists():
        return prefs
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, dict) and "preference" in data and isinstance(data["preference"], dict):
            data = data["preference"]
        if isinstance(data, dict):
            for k, v in data.items():
                try:
                    prefs[str(k)] = float(v)
                except Exception:
                    continue
    except Exception:
        return {}
    return prefs


PREFERENCES = _load_preferences()


class Brain:
    """
    규칙 기반 + 선호도 기반의 단순 로직.
    - 입력: sensor dict {object, gyro(3), distances(2)}
    - 출력: (left, right, emotion)
    """

    def __init__(self):
        self.preferences = PREFERENCES

    def act(self, sensor):
        sensor = sensor or {}
        gyro = sensor.get("gyro") or (0.0, 0.0, 0.0)
        distances = sensor.get("distances") or [0.0, 0.0]
        if len(distances) == 0:
            distances = [0.0, 0.0]
        elif len(distances) == 1:
            distances = [distances[0], distances[0]]
        obj = sensor.get("object")

        # ============================
        # 1) 감정 판단 하드코딩 규칙
        # ============================

        # 자이로 값 중 하나라도 50 초과 → dizzy
        g_max = max(abs(g) for g in gyro)
        if g_max > 50:
            return 0.0, 0.0, "dizzy"

        # 거리 두 번째 값이 200 이상이면 → scary
        d2 = distances[1]
        if d2 >= 200:
            return -20.0, -20.0, "scary"

        # 위험 물체는 → scary
        bad_objs = {"fork", "knife", "spoon"}
        if obj in bad_objs:
            return -20.0, -20.0, "scary"

        # 좋아하는 물체는 → happy
        good_objs = {"person", "cat", "dog"}
        if obj in good_objs:
            return 10.0, 10.0, "happy"

        # 나머지는 → neutral
        # (모터 정지)
        return 0.0, 0.0, "neutral"
