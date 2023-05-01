import abc


class Task(object, metaclass=abc.ABCMeta):
    def __init__(self):
        self.success = False

    @property
    @abc.abstractmethod
    def name(self):
        pass

    @property
    def followups(self):
        return []

    @abc.abstractmethod
    def run(self):
        pass

    def reset(self):
        self.success = False
