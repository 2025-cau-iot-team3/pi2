# brain.py
import json
from pathlib import Path
import numpy as np
from rnn.tiny_rnn import TinyRNN

CONFIG_PATH = Path(__file__).resolve().parent.parent / "cfg" / "objectConfig.json"
EMO_CONFIG_PATH = Path(__file__).resolve().parent.parent / "cfg" / "emoConfig.json"
PREF_MIN = -100.0
PREF_MAX = 100.0

def _load_preferences():
    """
    선호도 스코어를 {-100,100} 범위로 읽어 dict[str,float] 반환.
    지원 포맷:
    - {"preference": {"cat": 80, "dog": -50}}
    - {"cat": 80, "dog": -50}
    """
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
                    val = float(v)
                    prefs[str(k)] = max(PREF_MIN, min(PREF_MAX, val))
                except Exception:
                    continue
        return prefs
    except Exception:
        return {}

PREFERENCES = _load_preferences()

def _load_emotions():
    if not EMO_CONFIG_PATH.exists():
        return []
    try:
        with open(EMO_CONFIG_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("emotions"), list):
            return [str(e) for e in data["emotions"] if isinstance(e, (str, int, float))]
        if isinstance(data, list):
            return [str(e) for e in data if isinstance(e, (str, int, float))]
    except Exception:
        return []
    return []

EMOTIONS = _load_emotions()
EMO_COUNT = max(len(EMOTIONS), 0)

class Brain:
    def __init__(self):
        # 입력 6차원: object score + gyro(x,y,z) + ultra2
        output_size = 2 + (EMO_COUNT if EMO_COUNT > 0 else 0)
        self.rnn = TinyRNN(input_size=6, hidden_size=8, output_size=output_size)

    def act(self, sensor_data):
        x = self.build_input(sensor_data)
        y = self.rnn.step(x)

        # 출력 분리: [left_raw, right_raw, emotion_logits...]
        motor_raw = y[:2]
        # tanh → [-1,1] 범위로 제한 후 100 스케일
        speeds = np.tanh(motor_raw) * 100.0
        left, right = np.clip(speeds, -100.0, 100.0)

        emotion = None
        if EMO_COUNT > 0 and len(y) >= 2 + EMO_COUNT:
            logits = y[2:2 + EMO_COUNT]
            emo_idx = int(np.argmax(logits))
            if 0 <= emo_idx < EMO_COUNT:
                emotion = EMOTIONS[emo_idx]

        return float(left), float(right), emotion

    def build_input(self, s):
        obj_score = self._encode_object(s.get("object"))
        distances = self._distances2(s)
        return [
            obj_score,
            s["gyro"][0],
            s["gyro"][1],
            s["gyro"][2],
            distances[0],
            distances[1],
        ]

    def _encode_object(self, obj):
        if isinstance(obj, (int, float)):
            return float(np.clip(obj, PREF_MIN, PREF_MAX) / PREF_MAX)
        if not obj:
            return 0.0

        score = PREFERENCES.get(str(obj))
        if score is None:
            return 0.0
        return float(np.clip(score, PREF_MIN, PREF_MAX) / PREF_MAX)

    def _distances2(self, s):
        dists = s.get("distances") or []
        vals = []
        for d in dists:
            vals.append(0.0 if d is None else float(min(d / 200.0, 1.0)))
        while len(vals) < 2:
            fallback = s.get("dist") or 0.0
            vals.append(float(min(fallback / 200.0, 1.0)))
        return vals[:2]

    def get_weights(self):
        return self.rnn.get_weights()

    def set_weights(self, w):
        self.rnn.set_weights(w)
