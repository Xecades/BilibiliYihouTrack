from loguru import logger as L
import pytesseract
import cv2
import re

# x1, y1, x2, y2
TIME_BBOX = (1606, 342, 1862, 406)
OCR_REPROCESS_COUNT_MAX = 3


def ocr(frame) -> str | None:
    for _ in range(OCR_REPROCESS_COUNT_MAX):
        time_text = extract_time(frame)
        if re.match(r"^(\d:)?(\d\d?:)?\d\d?$", time_text):
            return time_text
    return None


def extract_time(frame, bbox=TIME_BBOX):
    x1, y1, x2, y2 = bbox
    roi = frame[y1:y2, x1:x2]

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.imwrite("snapshot_with_bbox.jpg", frame)
    L.info("Snapshot with bounding box saved as 'snapshot_with_bbox.jpg'")

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(
        gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    cv2.imwrite("snapshot_thresh.jpg", thresh)

    text = pytesseract.image_to_string(
        roi, config='-c tessedit_char_whitelist=0123456789:')
    return text.strip()
