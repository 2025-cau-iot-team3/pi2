# brain.py
import json
from pathlib import Path
import numpy as np
from rnn.tiny_rnn import TinyRNN

CONFIG_PATH = Path(__file__).resolve().parent.parent / "cfg" / "objectConfig.json"

def _load_object_config():
    if not CONFIG_PATH.exists():
        return {"like": {}, "dislike": {}}
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        like = data.get("like", {}) or {}
        dislike = data.get("dislike", {}) or {}
        return {"like": like, "dislike": dislike}
    except Exception:
        return {"like": {}, "dislike": {}}

OBJECT_CONFIG = _load_object_config()

class Brain:
    def __init__(self):
        # 2개 출력: 좌/우 트랙 속도
        self.rnn = TinyRNN(input_size=6, hidden_size=8, output_size=2)

    def act(self, sensor_data):
        x = self.build_input(sensor_data)
        y = self.rnn.step(x)
        # tanh → [-1,1] 범위로 제한 후 100 스케일
        speeds = np.tanh(y) * 100.0
        left, right = np.clip(speeds, -100.0, 100.0)
        return float(left), float(right)

    def build_input(self, s):
        obj_score = self._encode_object(s.get("object"))
        return [
            min(s["dist"] / 200.0, 1.0),  # normalize
            obj_score,
            s["gyro"][0],
            s["gyro"][1],
            s["gyro"][2],
            s["brightness"]
        ]

    def _encode_object(self, obj):
        if isinstance(obj, (int, float)):
            return float(obj)
        if not obj:
            return 0.0
        obj_str = str(obj)
        if obj_str in OBJECT_CONFIG.get("like", {}):
            return 1.0
        if obj_str in OBJECT_CONFIG.get("dislike", {}):
            return -1.0
        return 0.0

    def get_weights(self):
        return self.rnn.get_weights()

    def set_weights(self, w):
        self.rnn.set_weights(w)
