# test_llm.py
from action.brain import Brain
import json

def run(sensor):
    brain = Brain()
    left, right, emotion = brain.act(sensor)
    print("input :", sensor)
    print("output:", left, right, emotion)
    print()
    
def read_file(file_path):
    print(f"[DEBUG] 파일 읽기 시도: {file_path}")
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"[DEBUG] 파일 읽기 성공: {len(content)} bytes")
            print(f"[DEBUG] 내용: {content[:100]}...")
            return content
    except FileNotFoundError:
        print(f"[DEBUG] 파일을 찾을 수 없음: {file_path}")
        return None
    except Exception as e:
        print(f"[DEBUG] 파일 읽기 오류: {e}")
        return None

def parse_sensor_json(sensor_json):
    print(f"[DEBUG] JSON 파싱 시도")
    print(f"[DEBUG] 입력 데이터: {sensor_json}")
    try:
        data = json.loads(sensor_json)
        print(f"[DEBUG] JSON 파싱 성공: {data}")
        gyro = tuple(data["gyro"])
        print(f"[DEBUG] gyro 파싱: {gyro}")
        ultrasonic = [data["ultrasonic_1"], data["ultrasonic_2"]]
        print(f"[DEBUG] ultrasonic 파싱: {ultrasonic}")
        return gyro, ultrasonic
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON 파싱 실패: {e}")
        return None, None
    except KeyError as e:
        print(f"[DEBUG] 키를 찾을 수 없음: {e}")
        return None, None
    except Exception as e:
        print(f"[DEBUG] 파싱 오류: {e}")
        return None, None

def main():
    print("[DEBUG] main() 시작")

    obj = read_file("/action/yolo_obj")
    print(f"[DEBUG] obj 값: {obj}")

    sensor_json = read_file("/sensor/sensor_state")
    print(f"[DEBUG] sensor_json 값: {sensor_json}")

    if sensor_json:
        print("[DEBUG] sensor_json이 존재함, 파싱 시작")
        gyro, ultrasonic = parse_sensor_json(sensor_json)
        print(f"[DEBUG] 파싱 결과 - gyro: {gyro}, ultrasonic: {ultrasonic}")
        t = {"object": obj, "gyro": gyro, "distances": ultrasonic}
        print(f"[DEBUG] 최종 센서 데이터: {t}")
        run(t)
        return True
    else:
        print("[DEBUG] sensor_json이 None, False 반환")
        return False

if __name__ == "__main__":
    print(main())
