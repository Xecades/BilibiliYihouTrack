from typing import Union
from loguru import logger as L
from utils import *
import requests
import json
import cv2


def get_request(address, params):
    response = requests.get(
        address,
        params=params,
        headers={"User-Agent": "curl/8.7.1"}
    )
    return response.content.decode("utf-8")


class BilibiliStream:
    room_id: int
    real_room_id: Union[int, None] = None
    V1API = "https://api.live.bilibili.com/xlive/web-room/v1/playUrl/playUrl"

    def __init__(self, room_id: int):
        self.room_id = room_id
        L.info(f"BilibiliStream Engine initialized with room ID: {room_id}")

    def screenshot(self):
        L.info(f"Taking screenshot for room ID: {self.room_id}")
        self.real_room_id = self.get_real_room_id()
        self.quality = self.get_quality()
        urls = self.get_urls()
        for i, url in enumerate(urls):
            L.info(f"Trying URL {i}")
            frame = self.screenshot_from_url(url)
            if frame is not None:
                L.success("Screenshot taken successfully.")
                break
        if frame is None:
            raise ScreenshotError("Failed to take screenshot.")
        return frame

    def screenshot_from_url(self, url: str):
        cap = cv2.VideoCapture(url)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            L.info("Failed to read frame from the video stream.")
            return None
        return frame

    def get_urls(self) -> list[str]:
        params = {
            "cid": str(self.real_room_id),
            "platform": "hls",
            "qn": str(self.quality)
        }
        result = get_request(self.V1API, params)
        L.debug(f"Response from get_urls: {result}")

        data = json.loads(result)
        urls = []

        for durl_item in data.get("data", {}).get("durl", []):
            urls.append(durl_item.get("url", ""))

        if urls:
            L.success(f"Get URLs successfully")
        else:
            L.error(f"Failed to get URLs")
        return urls

    def get_quality(self) -> int:
        params = {"cid": str(self.real_room_id), "platform": "hls"}
        result = get_request(self.V1API, params)
        L.debug(f"Response from get_quality: {result}")

        data = json.loads(result)
        quality_map = data.get("data", {}).get("quality_description", [])

        L.success(f"Get available qualities: {quality_map}")
        qn = quality_map[0].get("qn")
        L.info(f"Use quality qn: {qn}")
        return qn

    def get_real_room_id(self) -> int | None:
        room_id = self.room_id
        address = "https://api.live.bilibili.com/room/v1/Room/room_init"
        result = get_request(address, {"id": room_id})
        L.debug(f"Response from room_init: {result}")
        real_room_id = self.handle_live_status(result)

        if real_room_id is None:
            raise RoomIdRetrievalError(
                f"Failed to retrieve real room ID for room {room_id}.")
        else:
            L.success(f"Get real room ID: {real_room_id}")

        return real_room_id

    def handle_live_status(self, result: str) -> int | None:
        data = json.loads(result)
        code = data.get("code")

        if code == 60004:
            raise RoomNotExistError(f"Room {self.room_id} does not exist.")

        if code == 0:
            live_status = data.get("data", {}).get("live_status")
            if live_status != 1:
                raise LiveNotStartedError(f"Room {self.room_id} is not live.")

        return data.get("data", {}).get("room_id")
