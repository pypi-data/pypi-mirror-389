"""
vision_ai.py — pyaidrone / 교육용 Vision & AI 유틸 모듈 (단일 파일 버전)

외부 의존성:
  - numpy
  - opencv-python (cv2)
  - (선택) tflite-runtime 또는 tensorflow  : TFLiteDetector 사용 시 필요

기능 요약:
  1) 좌표계 변환 헬퍼
     - xywh_to_xyxy, xyxy_to_xywh

  2) 기본 영상 전처리/디버그 유틸
     - to_gray, bgr_to_rgb, normalize_img
     - stack_images, put_fps

  3) 비율 유지 리사이즈 + 패딩 (YOLO 스타일)
     - letterbox

  4) 박스 그리기
     - draw_box_xywh

  5) TFLite 모델 추론 래퍼
     - TFLiteDetector

  6) OpenCV 추적기 생성
     - create_tracker

  7) 실전 유틸
     - iou, nms, largest_contour, contour_centroid, scale_box_from_letterbox

  8) 딥러닝 후처리 유틸
     - decode_yolov8   : YOLOv8 스타일 TFLite 출력 디코딩
     - mask_to_contours: 세그멘테이션 마스크 → 컨투어/박스
"""

from __future__ import annotations

from typing import Any, List, Tuple, Optional, Callable, Iterable
import numpy as np
import cv2

__version__ = "1.2.0"


# ---------------------------------------------------------------------------
# 1) 좌표계 변환 헬퍼
# ---------------------------------------------------------------------------

def xywh_to_xyxy(x: int, y: int, w: int, h: int) -> tuple[int, int, int, int]:
    """
    (x,y,w,h) → (x1,y1,x2,y2) 변환 헬퍼.
    - x,y : 좌상단
    - w,h : 폭, 높이
    """
    return int(x), int(y), int(x + w), int(y + h)


def xyxy_to_xywh(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
    """
    (x1,y1,x2,y2) → (x,y,w,h) 변환 헬퍼.
    - x1,y1 : 좌상단
    - x2,y2 : 우하단
    """
    return int(x1), int(y1), int(x2 - x1), int(y2 - y1)


# ---------------------------------------------------------------------------
# 2) 기본 영상 전처리/디버그 유틸
# ---------------------------------------------------------------------------

def to_gray(img: np.ndarray) -> np.ndarray:
    """
    BGR 또는 Gray 이미지를 항상 Gray로 변환.
    """
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    """
    OpenCV BGR 이미지를 RGB로 변환 (딥러닝 프레임워크와 연동 시 유용).
    """
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def normalize_img(img: np.ndarray, mean: float | tuple = 0.0, std: float | tuple = 1.0) -> np.ndarray:
    """
    이미지를 float32로 변환하고 (img - mean) / std 정규화.
    - mean, std 가 스칼라면 전체에 적용
    - (3,) 튜플이면 채널별로 적용 (B,G,R 순서)
    """
    x = img.astype(np.float32)
    if isinstance(mean, (int, float)) and isinstance(std, (int, float)):
        return (x - mean) / (std if std != 0 else 1.0)

    mean_arr = np.array(mean, dtype=np.float32).reshape(1, 1, -1)
    std_arr  = np.array(std,  dtype=np.float32).reshape(1, 1, -1)
    std_arr[std_arr == 0] = 1.0
    return (x - mean_arr) / std_arr


def stack_images(imgs: list[np.ndarray], cols: int = 2, scale: float = 1.0) -> np.ndarray:
    """
    여러 이미지를 그리드로 쌓아서 한 장으로 합치는 디버그용 유틸.
    - imgs: 길이 N의 BGR 또는 Gray 이미지 리스트
    - cols: 열(column) 개수
    - scale: 최종 출력 스케일

    반환: 합쳐진 BGR 이미지
    """
    if not imgs:
        raise ValueError("stack_images: imgs 리스트가 비었습니다.")

    # 모두 BGR로 맞추기
    proc = []
    for im in imgs:
        if im.ndim == 2:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        proc.append(im)

    h0, w0 = proc[0].shape[:2]
    rows = (len(proc) + cols - 1) // cols

    # 각 칸의 크기를 첫 이미지 기준으로 맞춤
    grid = []
    idx = 0
    for r in range(rows):
        row_imgs = []
        for c in range(cols):
            if idx < len(proc):
                im = proc[idx]
                if im.shape[:2] != (h0, w0):
                    im = cv2.resize(im, (w0, h0))
            else:
                im = np.zeros((h0, w0, 3), dtype=np.uint8)
            row_imgs.append(im)
            idx += 1
        grid.append(np.hstack(row_imgs))
    out = np.vstack(grid)

    if scale != 1.0:
        out = cv2.resize(out, (0, 0), fx=scale, fy=scale)
    return out


def put_fps(img: np.ndarray, fps: float, pos: tuple[int, int] = (10, 20)) -> None:
    """
    좌측 상단 등에 FPS 텍스트를 그려 넣기.
    - img: BGR
    - fps: 측정된 FPS
    - pos: 텍스트 시작 위치 (x,y)
    """
    txt = f"FPS: {fps:.1f}"
    cv2.putText(img, txt, pos, cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 255), 2, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# 3) letterbox — 비율 유지 리사이즈 + 패딩 (YOLO 스타일)
# ---------------------------------------------------------------------------

def letterbox(
    img: np.ndarray,
    new_shape: Tuple[int, int] | int,
    color: Tuple[int, int, int] = (114, 114, 114),
    auto: bool = False,
    scaleFill: bool = False,
    scaleup: bool = True,
    stride: int = 32,
) -> tuple[np.ndarray, float, tuple[int, int]]:
    """
    비율 유지 리사이즈 + 패딩 (YOLO 스타일)

    Args:
        img: 입력 BGR 이미지 (H, W, 3)
        new_shape: (width, height) 또는 int (정사각형 한 변)
        color: 패딩 색 (B,G,R)
        auto: stride 배수에 맞춰 패딩을 조정할지 여부
        scaleFill: 강제로 new_shape에 딱 맞게 리사이즈(비율 무시)
        scaleup: True면 확대 허용, False면 축소만 허용
        stride: auto=True일 때 패딩 맞출 stride

    Returns:
        padded_img: 패딩된 이미지
        r: 원본 대비 스케일 (float)
        pad: (pad_w_left, pad_h_top)
    """
    shape = img.shape[:2]  # (h, w)
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    new_w, new_h = int(new_shape[0]), int(new_shape[1])

    orig_h, orig_w = shape[0], shape[1]

    if scaleFill:
        # 비율 무시하고 강제로 new_shape에 맞춤
        r_w = new_w / orig_w
        r_h = new_h / orig_h
        r = (r_w + r_h) / 2.0  # 의미상 평균
        resized = cv2.resize(img, (new_w, new_h))
        return resized, float(r), (0, 0)

    # 비율 유지 리사이즈
    r = min(new_w / orig_w, new_h / orig_h)
    if not scaleup:
        r = min(r, 1.0)

    resize_w, resize_h = int(round(orig_w * r)), int(round(orig_h * r))
    resized = cv2.resize(img, (resize_w, resize_h))

    # 패딩 계산
    dw = new_w - resize_w
    dh = new_h - resize_h

    if auto:
        # stride 배수에 맞게 padding 조정
        dw = dw % stride
        dh = dh % stride

    dw /= 2.0
    dh /= 2.0
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))

    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=color
    )

    return padded, float(r), (left, top)


# ---------------------------------------------------------------------------
# 4) draw_box_xywh — 박스 그리기
# ---------------------------------------------------------------------------

def draw_box_xywh(
    img: np.ndarray,
    box_xywh: tuple[int, int, int, int],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
    label: str | None = None,
):
    """
    xywh 박스를 받아 그대로 그립니다.

    Args:
        img: BGR 이미지
        box_xywh: (x, y, w, h)
        color: (B,G,R)
        thickness: 테두리 두께
        label: 박스 위에 표시할 문자열 (None이면 미표시)
    """
    x, y, w, h = box_xywh
    x1, y1, x2, y2 = xywh_to_xyxy(x, y, w, h)

    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

    if label:
        font = cv2.FONT_HERSHEY_SIMPLEX
        fs = 0.5
        (tw, th), _ = cv2.getTextSize(label, font, fs, 1)
        # 텍스트 배경 박스
        cv2.rectangle(
            img,
            (x1, y1 - th - 4),
            (x1 + tw + 4, y1),
            color,
            thickness=-1,
        )
        cv2.putText(
            img, label,
            (x1 + 2, y1 - 2),
            font, fs,
            (0, 0, 0), 1,
            lineType=cv2.LINE_AA,
        )


# ---------------------------------------------------------------------------
# 5) TFLiteDetector — TFLite 모델 추론 래퍼
# ---------------------------------------------------------------------------

def _try_import(mod: str):
    try:
        return __import__(mod)
    except Exception:
        return None

_tflite_runtime = _try_import("tflite_runtime.interpreter")
_tf = _try_import("tensorflow")


class TFLiteDetector:
    """
    다양한 TFLite 탐지/분류 모델을 보조하기 위한 최소 래퍼.

    - 입력: BGR 이미지 (H,W,3)
    - 내부에서 모델 입력 크기로 리사이즈 + dtype 맞춤
    - 출력: 모델별로 다른 raw tensor들을 decode_fn으로 후처리

    사용 예시:
        det = TFLiteDetector("model.tflite")

        def decode_fn(outs, orig_wh, inp_wh):
            ...
            return boxes, scores, classes

        boxes, scores, classes = det.infer(img, decode_fn)
    """

    def __init__(self, model: str):
        if _tflite_runtime is not None:
            Interpreter = _tflite_runtime.Interpreter
        elif _tf is not None:
            Interpreter = _tf.lite.Interpreter
        else:
            raise RuntimeError(
                "TFLite 인터프리터가 없습니다. "
                "tflite-runtime 또는 tensorflow 중 하나가 필요합니다."
            )

        self.inter = Interpreter(model_path=model)
        self.inter.allocate_tensors()
        self.inputs = self.inter.get_input_details()
        self.outputs = self.inter.get_output_details()

        if len(self.inputs) != 1:
            raise ValueError("현재 TFLiteDetector는 입력이 1개인 모델만 지원합니다.")

    def _prep(self, img: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        inp_h, inp_w = self.inputs[0]["shape"][1:3]
        x = cv2.resize(img, (inp_w, inp_h))

        if self.inputs[0]["dtype"] == np.float32:
            x = x.astype(np.float32) / 255.0
        x = x[None, ...]  # 배치 축 추가: (1,H,W,C)

        return x, (inp_w, inp_h)

    def infer(
        self,
        img: np.ndarray,
        decode_fn: Callable[[List[np.ndarray], tuple[int, int], tuple[int, int]], Any],
    ):
        """
        Args:
            img: BGR np.ndarray (H,W,3)
            decode_fn: 후처리 함수
              인자: (raw_tensors, (orig_w,orig_h), (inp_w,inp_h))

        Returns:
            decode_fn이 돌려주는 임의의 값
        """
        orig_wh = img.shape[1::-1]  # (w, h)
        x, inp_wh = self._prep(img)

        self.inter.set_tensor(self.inputs[0]["index"], x)
        self.inter.invoke()
        outs = [self.inter.get_tensor(o["index"]) for o in self.outputs]

        return decode_fn(outs, orig_wh, inp_wh)


# ---------------------------------------------------------------------------
# 6) OpenCV 추적기 생성 (호환성 고려)
# ---------------------------------------------------------------------------

def create_tracker(name: str = "CSRT"):
    """
    OpenCV 추적기 생성 (opencv-contrib-python 버전마다 네임스페이스 차이를 흡수).

    Args:
        name: "KCF", "CSRT", "MOSSE" 등 (대소문자 무시)

    Returns:
        tracker 객체

    Raises:
        RuntimeError: 해당 이름의 추적기를 만들 수 없는 경우
    """
    name = name.upper()

    # 1) cv2.legacy 네임스페이스 우선
    try:
        if hasattr(cv2, "legacy"):
            fn = getattr(cv2.legacy, f"Tracker{name}_create", None)
            if callable(fn):
                return fn()
    except Exception:
        pass

    # 2) 구 버전(OpenCV 3.x 스타일) API 폴백
    fn2 = getattr(cv2, f"Tracker{name}_create", None)
    if callable(fn2):
        return fn2()

    # 3) 최종 실패
    raise RuntimeError(
        f"{name} tracker 생성 실패: "
        f"opencv-contrib-python 또는 해당 추적기 지원이 필요할 수 있습니다."
    )


# ---------------------------------------------------------------------------
# 7) 실전 유틸 (IoU, NMS, 컨투어, letterbox 좌표 복원)
# ---------------------------------------------------------------------------

def iou(a_xyxy: tuple[int, int, int, int],
        b_xyxy: tuple[int, int, int, int]) -> float:
    """두 박스(xyxy)의 IoU(Intersection-over-Union)."""
    ax1, ay1, ax2, ay2 = a_xyxy
    bx1, by1, bx2, by2 = b_xyxy

    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)

    iw, ih = max(0, inter_x2 - inter_x1), max(0, inter_y2 - inter_y1)
    inter = iw * ih

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter

    return float(inter / union) if union > 0 else 0.0


def nms(boxes_xyxy: np.ndarray,
        scores: np.ndarray,
        iou_th: float = 0.45) -> List[int]:
    """
    간단 NMS.

    Args:
        boxes_xyxy: (N,4) 배열, 각 행은 (x1,y1,x2,y2)
        scores: (N,) 점수 배열
        iou_th: IoU 임계값 (이보다 큰 박스는 제거)

    Returns:
        keep 인덱스 리스트
    """
    if len(boxes_xyxy) == 0:
        return []

    idxs = scores.argsort()[::-1]
    keep: List[int] = []

    while len(idxs) > 0:
        i = int(idxs[0])
        keep.append(i)
        if len(idxs) == 1:
            break

        rest = idxs[1:]
        ious = np.array([
            iou(tuple(boxes_xyxy[i]), tuple(boxes_xyxy[j]))
            for j in rest
        ])

        idxs = rest[ious <= iou_th]

    return keep


def largest_contour(contours: Iterable[np.ndarray]) -> Optional[np.ndarray]:
    """가장 넓은 컨투어 반환(없으면 None)."""
    try:
        return max(contours, key=cv2.contourArea)
    except ValueError:  # empty iterable
        return None


def contour_centroid(c: np.ndarray) -> Optional[tuple[int, int]]:
    """컨투어 무게중심(정수 픽셀). 실패 시 None."""
    if c is None or len(c) == 0:
        return None

    M = cv2.moments(c)
    if M["m00"] == 0:
        return None

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy)


def scale_box_from_letterbox(
    box_xyxy: tuple[int, int, int, int],
    r: float,
    pad: tuple[int, int],
) -> tuple[int, int, int, int]:
    """
    letterbox 좌표(xyxy, 패딩된 이미지 기준)를
    원본 이미지 좌표(xyxy)로 복원.

    Args:
        box_xyxy: (x1,y1,x2,y2) on padded image
        r: letterbox에서 반환한 스케일 (float)
        pad: (pad_w_left, pad_h_top)

    Returns:
        (x1,y1,x2,y2) on original image
    """
    x1, y1, x2, y2 = box_xyxy
    left, top = pad

    x1 = (x1 - left) / r
    y1 = (y1 - top) / r
    x2 = (x2 - left) / r
    y2 = (y2 - top) / r

    return (
        int(round(x1)),
        int(round(y1)),
        int(round(x2)),
        int(round(y2)),
    )


# ---------------------------------------------------------------------------
# 8) YOLOv8 디코더 & 세그멘테이션 마스크 후처리
# ---------------------------------------------------------------------------

def decode_yolov8(
    outs: List[np.ndarray],
    orig_wh: tuple[int, int],
    inp_wh: tuple[int, int],
    conf_th: float = 0.25,
    iou_th: float = 0.45,
    max_det: int = 300,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    YOLOv8 스타일 TFLite 출력 디코딩 헬퍼.

    전제:
      - outs[0] 형태가 다음 중 하나라고 가정:
        (1, N, C) 또는 (1, C, N) 또는 (N, C)
      - C >= 6, 맨 앞 5개는 [cx, cy, w, h, obj_conf],
        나머지 C-5개는 class별 score (예: 80개)

      - 좌표 (cx,cy,w,h)는 TFLite 입력 해상도 기준 '픽셀' 단위라고 가정
        (TFLiteDetector가 단순 resize만 사용하므로 letterbox 미사용)

    Args:
        outs: TFLiteDetector.infer 에서 받은 raw 출력 리스트
        orig_wh: 원본 이미지 (w,h)
        inp_wh: TFLite 입력 이미지 (w,h)
        conf_th: confidence threshold
        iou_th: NMS IoU threshold
        max_det: 최대 유지 박스 수

    Returns:
        boxes_xyxy: (M,4) int32, 원본 이미지 기준 (x1,y1,x2,y2)
        scores:     (M,) float32
        cls_ids:    (M,) int32
    """
    if not outs:
        return (
            np.zeros((0, 4), dtype=np.int32),
            np.zeros((0,), dtype=np.float32),
            np.zeros((0,), dtype=np.int32),
        )

    pred = outs[0]

    # 모양 통일: (N, C)
    if pred.ndim == 3:
        # (1, N, C) 또는 (1, C, N)
        if pred.shape[0] == 1:
            pred = pred[0]
        else:
            # (B,N,C)인 경우 B=1 만 지원한다고 가정
            pred = pred[0]
    if pred.shape[0] < pred.shape[1] and pred.shape[1] >= 6:
        # (C,N) 형태라고 가정 → (N,C)로 transpose
        pred = pred.T

    if pred.ndim != 2 or pred.shape[1] < 6:
        # 예상과 다른 모양이면 빈 결과
        return (
            np.zeros((0, 4), dtype=np.int32),
            np.zeros((0,), dtype=np.float32),
            np.zeros((0,), dtype=np.int32),
        )

    # 분해
    boxes = pred[:, :4]                # (cx, cy, w, h)
    obj   = pred[:, 4:5]               # (N,1)
    cls_raw = pred[:, 5:]              # (N,num_classes)

    # objectness * class score
    cls_scores = obj * cls_raw         # broadcast → (N,num_classes)
    cls_ids = np.argmax(cls_scores, axis=1)
    scores  = np.max(cls_scores, axis=1)

    # confidence 필터
    keep_conf = scores >= conf_th
    if not np.any(keep_conf):
        return (
            np.zeros((0, 4), dtype=np.int32),
            np.zeros((0,), dtype=np.float32),
            np.zeros((0,), dtype=np.int32),
        )

    boxes = boxes[keep_conf]
    scores = scores[keep_conf]
    cls_ids = cls_ids[keep_conf]

    # cx,cy,w,h → x1,y1,x2,y2 (입력 해상도 기준)
    cx, cy, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    x1 = cx - w / 2.0
    y1 = cy - h / 2.0
    x2 = cx + w / 2.0
    y2 = cy + h / 2.0

    inp_w, inp_h = float(inp_wh[0]), float(inp_wh[1])
    orig_w, orig_h = float(orig_wh[0]), float(orig_wh[1])

    # 단순 resize 비율로 매핑 (letterbox 미사용 전제)
    gain_w = orig_w / inp_w
    gain_h = orig_h / inp_h

    x1 *= gain_w
    x2 *= gain_w
    y1 *= gain_h
    y2 *= gain_h

    boxes_xyxy = np.stack(
        [x1, y1, x2, y2], axis=1
    ).round().astype(np.int32)

    # NMS
    keep = nms(boxes_xyxy, scores, iou_th=iou_th)
    if len(keep) > max_det:
        keep = keep[:max_det]

    boxes_xyxy = boxes_xyxy[keep]
    scores = scores[keep].astype(np.float32)
    cls_ids = cls_ids[keep].astype(np.int32)

    return boxes_xyxy, scores, cls_ids


def mask_to_contours(
    mask: np.ndarray,
    thresh: float | int = 0.5,
    area_min: float = 10.0,
    mode: str = "external",
    as_boxes: bool = True,
) -> tuple[list[np.ndarray], list[tuple[int, int, int, int]]]:
    """
    세그멘테이션 마스크(또는 확률 맵)를 외곽선(컨투어)와 박스로 변환.

    Args:
        mask:
          - 2D (H,W) 또는 3채널 (H,W,3)
          - float형인 경우 [0,1] 확률 맵이라고 가정하고 thresh 이상을 1로 binarize
          - uint8형인 경우 0/255 이진 마스크라고 가정 (thresh는 1~254 범위로 사용 가능)
        thresh:
          - float: [0,1] 기준 임계값
          - int:   0~255 기준 임계값
        area_min:
          - 이 픽셀 수보다 작은 컨투어는 무시
        mode:
          - "external" → RETR_EXTERNAL
          - 그 외 → RETR_TREE (전체 계층)
        as_boxes:
          - True면 각 컨투어의 외접 사각형(x,y,w,h) 리스트도 함께 반환

    Returns:
        contours: 필터링된 컨투어 리스트
        boxes:    각 컨투어에 대응하는 (x,y,w,h) 리스트 (as_boxes=False면 빈 리스트)
    """
    if mask.ndim == 3:
        # 컬러/3채널인 경우 Gray로
        mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    else:
        mask_gray = mask.copy()

    if mask_gray.dtype == np.float32 or mask_gray.dtype == np.float64:
        # 확률 맵이라고 가정하고 [0,1] → 0~255 후 이진화
        m = np.clip(mask_gray, 0.0, 1.0)
        thr_val = float(thresh)
        _, mask_bin = cv2.threshold(
            (m * 255).astype(np.uint8),
            int(thr_val * 255),
            255,
            cv2.THRESH_BINARY
        )
    else:
        # uint8 마스크라고 가정
        thr_val = int(thresh)
        _, mask_bin = cv2.threshold(
            mask_gray,
            thr_val,
            255,
            cv2.THRESH_BINARY
        )

    # 노이즈 제거를 위한 간단한 모폴로지 (필요 없으면 주석 처리 가능)
    kernel = np.ones((3, 3), np.uint8)
    mask_bin = cv2.morphologyEx(mask_bin, cv2.MORPH_OPEN, kernel, iterations=1)
    mask_bin = cv2.morphologyEx(mask_bin, cv2.MORPH_CLOSE, kernel, iterations=1)

    # 컨투어 추출
    if mode.lower() == "external":
        retrieval = cv2.RETR_EXTERNAL
    else:
        retrieval = cv2.RETR_TREE

    contours, _ = cv2.findContours(
        mask_bin, retrieval, cv2.CHAIN_APPROX_SIMPLE
    )

    # 면적 필터링
    filtered_contours: list[np.ndarray] = []
    boxes: list[tuple[int, int, int, int]] = []

    for c in contours:
        a = cv2.contourArea(c)
        if a < area_min:
            continue
        filtered_contours.append(c)
        if as_boxes:
            x, y, w, h = cv2.boundingRect(c)
            boxes.append((int(x), int(y), int(w), int(h)))

    if not as_boxes:
        boxes = []

    return filtered_contours, boxes


# ---------------------------------------------------------------------------
# 9) 공개 심볼
# ---------------------------------------------------------------------------

__all__ = sorted({
    # 좌표계
    "xywh_to_xyxy", "xyxy_to_xywh",
    # 기본 전처리/디버그
    "to_gray", "bgr_to_rgb", "normalize_img", "stack_images", "put_fps",
    # letterbox & 박스
    "letterbox", "draw_box_xywh",
    # TFLite & 추적기
    "TFLiteDetector", "create_tracker",
    # 유틸
    "iou", "nms",
    "largest_contour", "contour_centroid", "scale_box_from_letterbox",
    # 딥러닝 후처리
    "decode_yolov8", "mask_to_contours",
})
