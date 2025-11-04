import pickle
from pathlib import Path
from typing import Any

from dedal.serialize.SerializeInterface import SerializerInterface


class PickleSerializer(SerializerInterface):
    def __init__(self, file_path: Path, file_name: str) -> None:
        self.file = file_path / file_name

    def serialize(self, obj: Any) -> None:
        """
        Serialize `obj` to disk as `filename` using the highest available protocol.
        """
        with open(self.file, 'wb') as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

    def deserialize(self) -> Any:
        """
        Read `filename` from disk and return the original Python object.
        """
        with open(self.file, 'rb') as f:
            return pickle.load(f)
