# llm_brain.py
import json
import requests

LLM_ENDPOINT = "http://127.0.0.1:8080/v1/chat/completions"
LLM_MODEL = "tiny-robot-llm"

SYSTEM_PROMPT = (
    "너는 소형 로봇의 감정 및 모터 제어를 담당하는 컨트롤러다. "
    "주어지는 센서 입력(object, gyro, distances)에 대해 아래 규칙을 반드시 지켜서 "
    'JSON 형식 {"emotion": ..., "left": ..., "right": ...} 만 반환하라.\n\n'
    "규칙:\n"
    "1) gyro 값 셋 중 하나라도 50을 초과하면 emotion=\"dizzy\" 이고 left=0, right=0 이다.\n"
    "2) distances[1] (두 번째 거리 값)이 200 이상이면 emotion=\"scary\" 이고 left=-20, right=-20 이다.\n"
    "3) object 가 fork, knife, spoon 중 하나이면 emotion=\"scary\" 이고 left=-20, right=-20 이다.\n"
    "4) object 가 person, cat, dog 중 하나이면 emotion=\"happy\" 이고 left=10, right=10 이다.\n"
    "5) 위에 해당하지 않으면 emotion=\"neutral\" 이고 left=0, right=0 이다.\n"
    "항상 위 규칙을 우선하며 임의로 규칙을 바꾸지 마라."
)

class LLMBrain:
    def __init__(self, endpoint: str = LLM_ENDPOINT, model: str = LLM_MODEL):
        self.endpoint = endpoint
        self.model = model

    def _build_messages(self, sensor: dict):
        obj = sensor.get("object")
        gyro = sensor.get("gyro") or (0.0, 0.0, 0.0)
        distances = sensor.get("distances") or [0.0, 0.0]

        user_text = (
            "다음은 현재 센서 상태이다.\n"
            f"object: {obj}\n"
            f"gyro: {list(gyro)}\n"
            f"distances: {list(distances)}\n\n"
            '위 규칙에 따라 emotion, left, right 를 결정하고, '
            '반드시 JSON 하나만 반환하라. 예: {"emotion":"happy","left":10,"right":10}'
        )

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

    def decide(self, sensor: dict):
        msgs = self._build_messages(sensor)
        try:
            res = requests.post(
                self.endpoint,
                headers={"Content-Type": "application/json"},
                data=json.dumps(
                    {
                        "model": self.model,
                        "messages": msgs,
                        "temperature": 0.0,
                        "max_tokens": 64,
                    }
                ),
                timeout=5,
            )
        except Exception:
            return 0.0, 0.0, "neutral"

        if res.status_code != 200:
            return 0.0, 0.0, "neutral"

        try:
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            obj = json.loads(content)
            emotion = str(obj.get("emotion", "neutral"))
            left = float(obj.get("left", 0.0))
            right = float(obj.get("right", 0.0))
            if left < -100:
                left = -100.0
            if left > 100:
                left = 100.0
            if right < -100:
                right = -100.0
            if right > 100:
                right = 100.0
            return left, right, emotion
        except Exception:
            return 0.0, 0.0, "neutral"