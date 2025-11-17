# tiny_rnn.py
import numpy as np

class TinyRNN:
    def __init__(self, input_size, hidden_size=8, output_size=4):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        self.Wxh = np.random.randn(hidden_size, input_size) * 0.1
        self.Whh = np.random.randn(hidden_size, hidden_size) * 0.1
        self.Why = np.random.randn(output_size, hidden_size) * 0.1

        self.h = np.zeros((hidden_size, 1))

    def step(self, x_vec):
        x = np.array(x_vec, dtype=np.float32).reshape(-1, 1)
        self.h = np.tanh(self.Wxh @ x + self.Whh @ self.h)
        y = self.Why @ self.h
        return y.flatten()

    def get_weights(self):
        return [self.Wxh.copy(), self.Whh.copy(), self.Why.copy()]

    def set_weights(self, weights):
        self.Wxh, self.Whh, self.Why = weights
