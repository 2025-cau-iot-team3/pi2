# test_llm.py
from action.brain import Brain

def run(sensor):
    brain = Brain()
    left, right, emotion = brain.act(sensor)
    print("input :", sensor)
    print("output:", left, right, emotion)
    print()

if __name__ == "__main__":
    tests = [
        {"object": "dog", "gyro": (10, 10, 20), "distances": [120, 150]},
        {"object": "dog", "gyro": (10, 10, 20), "distances": [120, 250]},
        {"object": "fork", "gyro": (10, 10, 10), "distances": [80, 90]},
        {"object": "tree", "gyro": (0, 0, 0), "distances": [100, 100]},
        {"object": "cat", "gyro": (60, 10, 10), "distances": [100, 100]},
    ]

    for t in tests:
        run(t)