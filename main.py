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
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None

def parse_sensor_json(sensor_json):
    try:
        data = json.loads(sensor_json)
        gyro = tuple(data["gyro"])
        ultrasonic = [data["ultrasonic_1"], data["ultrasonic_2"]]
        return gyro, ultrasonic
    except (json.JSONDecodeError, KeyError):
        return None, None

def main():
    obj = read_file("/action/yolo_obj")
    sensor_json = read_file("/sensor/sensor_state")

    if sensor_json:
        gyro, ultrasonic = parse_sensor_json(sensor_json)
        t = {"object": obj, "gyro": gyro, "distances": ultrasonic}
        run(t)
        return True
    else:
        return False

if __name__ == "__main__":
    main()
