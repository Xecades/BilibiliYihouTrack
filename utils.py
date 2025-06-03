from enum import Enum


class SIG(Enum):
    ROOM_NOT_EXIST = 1
    LIVE_NOT_STARTED = 2
    OCR_FAILED = 3
    OTHER_ERROR = 4


class RoomNotExistError(Exception):
    pass


class LiveNotStartedError(Exception):
    pass


class RoomIdRetrievalError(Exception):
    pass


class ScreenshotError(Exception):
    pass


class OcrError(Exception):
    pass
