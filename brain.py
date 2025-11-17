# brain.py
import numpy as np
from tiny_rnn import TinyRNN

ACTIONS = ["RUN_AWAY", "APPROACH", "TURN_LEFT", "TURN_RIGHT"]

class Brain:
    def __init__(self):
        self.rnn = TinyRNN(input_size=6, hidden_size=8, output_size=4)

    def build_input(self, s):
        return [
            min(s["dist"] / 200.0, 1.0),  # normalize
            s["object"],                  # 0 none, 1 cat, 2 human
            s["gyro"][0],
            s["gyro"][1],
            s["gyro"][2],
            s["brightness"]
        ]

    def act(self, sensor_data):
        x = self.build_input(sensor_data)
        y = self.rnn.step(x)
        idx = int(np.argmax(y))
        return ACTIONS[idx]

    def get_weights(self):
        return self.rnn.get_weights()

    def set_weights(self, w):
        self.rnn.set_weights(w)
