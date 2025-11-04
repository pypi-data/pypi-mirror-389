from abc import ABC, abstractmethod

from getpycode.types import Module


class AbstractComment(ABC):
    @abstractmethod
    def get(self, module: Module) -> list[str]:
        pass
