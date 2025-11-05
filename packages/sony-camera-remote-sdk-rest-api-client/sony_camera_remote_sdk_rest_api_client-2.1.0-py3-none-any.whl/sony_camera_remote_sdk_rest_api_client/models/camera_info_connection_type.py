from enum import Enum


class CameraInfoConnectionType(str, Enum):
    NETWORK = "Network"
    USB = "USB"

    def __str__(self) -> str:
        return str(self.value)
