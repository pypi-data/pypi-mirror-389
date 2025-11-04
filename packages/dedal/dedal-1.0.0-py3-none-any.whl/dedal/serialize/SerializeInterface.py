from abc import ABC, abstractmethod
from typing import Any

class SerializerInterface(ABC):
    @abstractmethod
    def serialize(self, obj: Any) -> None:
        """
        Serialize `obj` to the given file path.
        """
        pass

    @abstractmethod
    def deserialize(self) -> Any:
        """
        Deserialize and return the object from the given file path.
        """
        pass
