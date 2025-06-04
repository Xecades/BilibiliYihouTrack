from loguru import logger as L
from stream import BilibiliStream
from dingtalk import send_dingtalk_message as send
from pytimeparse.timeparse import timeparse
from datetime import timedelta
from ocr import ocr
from utils import *
import time


is_notified = False
stream = BilibiliStream(room_id=60989)
TIME_THRES = timedelta(hours=1, minutes=20, seconds=0)
LARGE_DELAY = 20 * 60  # 20 minutes
SMALL_DELAY = 2 * 60   # 2 minutes
HIGH_FREQ_FAILURE_COUNT_MAX = 3
OCR_FAILURE_COUNT_MAX = 4


def notify(time_text: str):
    global is_notified
    sec = timeparse(time_text)
    t = timedelta(seconds=sec)
    if not is_notified and t > TIME_THRES:
        send(f"快快快快来直播间❗️当前记录时间：{time_text}")
        is_notified = True


def try_once() -> str | SIG:
    try:
        frame = stream.screenshot()
        if frame is None:
            raise ScreenshotError("Failed to take screenshot.")
        time_text = ocr(frame)
        if time_text is None:
            raise OcrError(f"Failed to extract time from screenshot.")
        L.success(f"Extracted time: {time_text}")
        notify(time_text)
        return time_text
    except Exception as e:
        L.error(f"{type(e).__name__}: {e}")
        if type(e) == RoomNotExistError:
            return SIG.ROOM_NOT_EXIST
        elif type(e) == LiveNotStartedError:
            return SIG.LIVE_NOT_STARTED
        elif type(e) == OcrError:
            return SIG.OCR_FAILED
        else:
            return SIG.OTHER_ERROR


# 初始化进入IDLE阶段。
# 在IDLE阶段，先执行一次try_once
#  - 如果成功返回时间，则进入HIGH_FREQ阶段，同时在进入的时候发送消息提醒（该部分逻辑先不写，留空）
#  - 如果失败，判断返回的SIG错误码
#     - ROOM_NOT_EXIST：直接退出程序
#     - LIVE_NOT_STARTED / OTHER_ERROR：等待LARGE_DELAY时间，重新执行IDLE阶段
#     - OCR_FAILED：再尝试OCR_FAILURE_COUNT_MAX次的try_once，每次尝试间隔SMALL_DELAY，
#                   如果全部失败则等待LARGE_DELAY时间，重新执行IDLE阶段，
#                   如果有一次成功则直接进入HIGH_FREQ并发送消息提醒（和前面的逻辑一样）
# 在HIGH_FREQ阶段，每隔SMALL_DELAY检测一次，如果try_once连续HIGH_FREQ_FAILURE_COUNT_MAX次失败
# 则发送另一个消息提醒（同样逻辑先留空），然后直接退出回到IDLE阶段
def main():
    def wait(seconds: int):
        L.info(f"Waiting for {seconds / 60:.1f} minutes...")
        time.sleep(seconds)

    def high_freq():
        global is_notified
        is_notified = False
        L.info("Entering HIGH_FREQ stage")
        send("国外大神 Yihou 开始直播空洞骑士了❗️")

        consecutive_failures = 0
        while consecutive_failures < HIGH_FREQ_FAILURE_COUNT_MAX:
            wait(SMALL_DELAY)
            result = try_once()

            if isinstance(result, str):
                L.success(f"HIGH_FREQ check: time is {result}")
                consecutive_failures = 0  # Reset counter on success
            else:
                consecutive_failures += 1
                L.warning(
                    f"HIGH_FREQ check failed ({consecutive_failures}/{HIGH_FREQ_FAILURE_COUNT_MAX})")

        L.info("Exiting HIGH_FREQ stage due to consecutive failures")
        send("空洞骑士直播结束了（悲")

    while True:
        # IDLE stage
        L.info("Entering IDLE stage")

        # First try_once attempt in IDLE stage
        result = try_once()

        # If successful, enter HIGH_FREQ stage
        if isinstance(result, str):
            L.success(f"Successfully detected time: {result}")
            high_freq()
            continue

        # Handle different error signals in IDLE stage
        if result == SIG.ROOM_NOT_EXIST:
            L.error("Room does not exist. Exiting program.")
            break

        elif result == SIG.LIVE_NOT_STARTED or result == SIG.OTHER_ERROR:
            L.warning(f"Got {result}. Waiting before retry.")
            wait(LARGE_DELAY)
            continue

        elif result == SIG.OCR_FAILED:
            # Try OCR again up to OCR_FAILURE_COUNT_MAX times
            L.warning("OCR failed. Trying additional attempts.")
            ocr_success = False

            for attempt in range(1, OCR_FAILURE_COUNT_MAX):
                wait(SMALL_DELAY)
                L.info(
                    f"OCR retry attempt {attempt}/{OCR_FAILURE_COUNT_MAX-1}")
                result = try_once()

                if isinstance(result, str):
                    L.success(f"OCR retry successful: {result}")
                    high_freq()
                    break

            if not ocr_success:
                L.error(f"All {OCR_FAILURE_COUNT_MAX} OCR attempts failed")
                wait(LARGE_DELAY)


if __name__ == "__main__":
    main()
