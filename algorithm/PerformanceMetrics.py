from abc import ABC, abstractmethod

class PerformanceMetrics:
    time: float
    memory: float # KB

    def __init__(self):
        self.time = 0
        self.memory = 0

    @abstractmethod
    def solve(self):
        pass