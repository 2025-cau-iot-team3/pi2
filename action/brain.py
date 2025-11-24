# brain.py

CLIFF_THRESHOLD_CM = 5.0

HAPPY_OBJECTS = {"person", "cat", "dog"}
SCARY_OBJECTS = {"fork", "knife", "spoon"}

class Brain:
    def __init__(self):
        pass

    def _get_front_back(self, distances):
        """distances = [front, back] 형태를 안전하게 파싱"""
        if not distances:
            return 9999.0, 9999.0
        front = float(distances[0]) if len(distances) > 0 else 9999.0
        back = float(distances[1]) if len(distances) > 1 else 9999.0
        return front, back

    def decide_emotion(self, sensor):
        """
        센서값으로 감정만 결정 (움직임은 act()에서 따로 결정)
        """
        obj = sensor.get("object")
        gyro = sensor.get("gyro") or (0.0, 0.0, 0.0)
        distances = sensor.get("distances") or [9999.0, 9999.0]
        front, back = self._get_front_back(distances)

        # 0) 앞뒤 모두 낭떠러지 근접 → 패닉
        if front < CLIFF_THRESHOLD_CM and back < CLIFF_THRESHOLD_CM:
            return "panic"

        # 1) 자이로 값 중 하나라도 50 초과 → dizzy
        if max(abs(g) for g in gyro) > 50:
            return "dizzy"

        # 2) 위험 물체 → scary
        if obj in SCARY_OBJECTS:
            return "scary"

        # 3) (선택) 뒤쪽 거리가 매우 멀면 불안 → scary
        if back >= 200:
            return "scary"

        # 4) 좋아하는 물체 → happy
        if obj in HAPPY_OBJECTS:
            return "happy"

        # 5) 나머지 → neutral
        return "neutral"

    def act(self, sensor):
        """
        최종 모터값 + 감정 반환
        (left, right, emotion)
        """
        emotion = self.decide_emotion(sensor)

        distances = sensor.get("distances") or [9999.0, 9999.0]
        front, back = self._get_front_back(distances)

        left = 0.0
        right = 0.0

        # 🔴 안전 우선: 패닉 / 낭떠러지 근접시 완전 정지
        if emotion == "panic":
            return 0.0, 0.0, emotion

        # 🤢 어지러움: 그냥 멈춤 (원하면 나중에 빙글빙글 회전 패턴 추가 가능)
        if emotion == "dizzy":
            return 0.0, 0.0, emotion

        # 😱 무서움: 기본은 뒤로 가기, 단 뒤쪽 낭떠러지면 정지
        if emotion == "scary":
            if back >= CLIFF_THRESHOLD_CM:
                left = -20.0
                right = -20.0
            else:
                left = right = 0.0

        # 😄 행복: 기본은 앞으로 가기, 단 앞쪽 낭떠러지면 정지
        elif emotion == "happy":
            if front >= CLIFF_THRESHOLD_CM:
                left = 20.0
                right = 20.0
            else:
                left = right = 0.0

        # 😐 중립: 그냥 멈춤
        elif emotion == "neutral":
            left = right = 0.0

        # 최종 모터 값 클리핑 (-100 ~ 100)
        left = max(-100.0, min(100.0, left))
        right = max(-100.0, min(100.0, right))

        return left, right, emotion