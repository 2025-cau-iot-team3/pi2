import json
import requests
import time

LLM_ENDPOINT = "http://127.0.0.1:11434/api/chat"
LLM_MODEL = "robot-llm"

class Brain:
    def __init__(self, endpoint=LLM_ENDPOINT, model=LLM_MODEL):
        self.endpoint = endpoint
        self.model = model
        self.last_output = (0.0, 0.0, "neutral")
        self.timeout_sec = 3

    def _build_messages(self, sensor):
        # sensor dict는 그대로 JSON 문자열로 user 메시지에 전달
        return [
            {"role": "user", "content": json.dumps(sensor)}
        ]

    def _fallback(self):
        # LLM 응답 실패 시 안전 정지
        return 0.0, 0.0, "neutral"

    def act(self, sensor):
        msgs = self._build_messages(sensor)

        try:
            res = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "messages": msgs,
                    "stream": False
                },
                timeout=self.timeout_sec
            )
        except Exception:
            return self._fallback()

        if res.status_code != 200:
            return self._fallback()

        try:
            data = res.json()
            content = data["message"]["content"]
            obj = json.loads(content)

            left = float(obj.get("left", 0.0))
            right = float(obj.get("right", 0.0))
            emotion = str(obj.get("emotion", "neutral"))

            # 모터 값 제한
            left = max(-100, min(100, left))
            right = max(-100, min(100, right))

            self.last_output = (left, right, emotion)
            return self.last_output

        except Exception:
            # JSON 파싱 실패하면 정지
            return self._fallback()