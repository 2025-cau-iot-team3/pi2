# brain_es.py
import numpy as np

class EvolutionStrategy:
    def __init__(self, weights, sigma=0.1, lr=0.03, population=10):
        self.weights = [w.copy() for w in weights]
        self.sigma = sigma
        self.lr = lr
        self.population = population

    def ask(self):
        noises = []
        for _ in range(self.population):
            noise = [np.random.randn(*w.shape) for w in self.weights]
            noises.append(noise)
        return noises

    def update(self, noise_list, rewards):
        rewards = np.array(rewards)
        A = (rewards - np.mean(rewards)) / (np.std(rewards) + 1e-7)

        updates = [np.zeros_like(w) for w in self.weights]

        for noise, r in zip(noise_list, A):
            for i in range(len(noise)):
                updates[i] += noise[i] * r

        for i in range(len(self.weights)):
            self.weights[i] += (self.lr / (self.population * self.sigma)) * updates[i]

        return self.weights
