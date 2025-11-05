from enum import Enum


class ConnectCameraBodyMode(str, Enum):
    CONTENTS_TRANSFER = "contents-transfer"
    REMOTE = "remote"
    REMOTE_TRANSFER = "remote-transfer"

    def __str__(self) -> str:
        return str(self.value)
