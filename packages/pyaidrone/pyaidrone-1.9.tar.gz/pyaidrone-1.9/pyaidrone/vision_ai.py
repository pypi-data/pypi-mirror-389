"""
vision_ai.py — pyaidrone용 Vision/AI 최종 병합판
- 베이스: vision_enhanced.py 전체 API 재사용
- 보강: vision.py의 TFLiteDetector + 권장사항 반영(좌표계 헬퍼, letterbox 문서화 래퍼)

변경점(혼선 최소화용):
1) 좌표계 변환 헬퍼 추가
   - xywh_to_xyxy(x,y,w,h)  → (x1,y1,x2,y2)
   - xyxy_to_xywh(x1,y1,x2,y2) → (x,y,w,h)
2) letterbox 문서화 래퍼 제공
   - r(배율)은 float 스칼라, pad는 (left, top) 튜플임을 명확히 표기
   - 내부적으로 vision_enhanced.letterbox를 호출
3) draw_box 사용 규약 주석 보강
   - 본 라이브러리 예제에서는 기본적으로 xyxy(좌상/우하) 좌표계를 권장
     (필요 시 xywh_to_xyxy/xyxy_to_xywh 헬퍼로 상호 변환)

vision_ai.py — pyaidrone용 Vision/AI 최종 병합판 (추가 유틸 5종 포함)
- 베이스: vision_enhanced.py 전체 API 재사용
- 보강: vision.py의 TFLiteDetector + 권장사항 반영(좌표계 헬퍼, letterbox 문서화 래퍼)
- 이번 수정: (1) draw_box 좌표계 주석 및 래퍼 일치화(xywh 기준), (2) __main__ 데모 블록 제거,
            (3) 실전 필수 유틸 5종 추가: iou, nms, largest_contour, contour_centroid, scale_box_from_letterbox
"""

from __future__ import annotations

from typing import Any, List, Tuple, Optional, Callable, Iterable
import numpy as np
import cv2

# 1) vision_enhanced 가져오기 (상대/절대 경로 모두 시도)
try:  # 패키지 내부 사용 (pyaidrone 패키지로 설치된 경우)
    from .vision_enhanced import *  # noqa: F401,F403
    from .vision_enhanced import (
        __all__ as _ENH_ALL,
        __version__ as _ENH_VER,
        letterbox as _enh_letterbox,
        draw_box as _enh_draw_box,
    )
except Exception:  # 단일 파일 배치/실습 편의
    try:
        from vision_enhanced import *  # noqa: F401,F403
        from vision_enhanced import (
            __all__ as _ENH_ALL,
            __version__ as _ENH_VER,
            letterbox as _enh_letterbox,
            draw_box as _enh_draw_box,
        )
    except Exception:
        _ENH_ALL = []
        _ENH_VER = "0.0.0"
        def _enh_letterbox(*args, **kwargs):
            raise RuntimeError("vision_enhanced.letterbox 가 필요합니다.")
        def _enh_draw_box(*args, **kwargs):
            raise RuntimeError("vision_enhanced.draw_box 가 필요합니다.")

# 2) 좌표계 변환 헬퍼 -----------------------------------------------------------
def xywh_to_xyxy(x: int, y: int, w: int, h: int) -> tuple[int, int, int, int]:
    """(x,y,w,h) → (x1,y1,x2,y2) 변환 헬퍼."""
    return int(x), int(y), int(x + w), int(y + h)

def xyxy_to_xywh(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
    """(x1,y1,x2,y2) → (x,y,w,h) 변환 헬퍼."""
    return int(x1), int(y1), int(x2 - x1), int(y2 - y1)


# 3) letterbox 문서화 래퍼 -----------------------------------------------------
def letterbox(img: np.ndarray,
              new_shape: Tuple[int, int] | int,
              color: Tuple[int, int, int] = (114, 114, 114),
              auto: bool = False,
              scaleFill: bool = False,
              scaleup: bool = True,
              stride: int = 32) -> tuple[np.ndarray, float, tuple[int, int]]:
    """
    비율 유지 리사이즈 + 패딩 (YOLO 스타일)

    반환값:
      - padded_img: 패딩된 이미지 (np.ndarray)
      - r: float 스칼라 배율(원본 대비 축소/확대 비율)
      - pad: (left, top) 패딩 픽셀 수 튜플

    주의:
      - 과거 코드 일부에서 (ratio_w, ratio_h) 튜플을 기대하는 경우가 있으나,
        본 래퍼는 **스칼라 r(float)** 을 반환합니다.
      - 필요시 r를 (r, r)로 확장하여 사용하세요.
    """
    return _enh_letterbox(img, new_shape, color=color,
                          auto=auto, scaleFill=scaleFill,
                          scaleup=scaleup, stride=stride)


# 4) draw_box 사용 규약(주석) --------------------------------------------------
# - vision_enhanced의 draw_box는 (x, y, w, h) 형태(xywh)를 기본으로 사용합니다.
# - 만약 검출기가 (x1,y1,x2,y2) 형태(xyxy)를 내놓으면 아래처럼 변환해서 사용하세요:
#     x, y, w, h = xyxy_to_xywh(x1, y1, x2, y2)
#     _enh_draw_box(img, (x, y, w, h), color=(0,255,0), thickness=2)
# - xywh 입력을 그대로 쓰고 싶을 때는 아래 래퍼를 사용하십시오.

def draw_box_xywh(img: np.ndarray,
                  box_xywh: tuple[int, int, int, int],
                  color=(0, 255, 0), thickness: int = 2, label: str | None = None):
    """xywh 박스를 받아 그대로 그립니다(vision_enhanced.draw_box는 xywh 기대)."""
    _enh_draw_box(img, box_xywh, color=color, thickness=thickness, label=label)


# 5) vision.py의 보강 요소: TFLiteDetector -----------------------------------

def _try_import(mod: str):
    try:
        return __import__(mod)
    except Exception:
        return None

_tflite_runtime = _try_import("tflite_runtime.interpreter")
_tf = _try_import("tensorflow")

class TFLiteDetector:
    """
    다양한 TFLite 탐지 모델을 보조하기 위한 최소 래퍼.
    - 입력: (N,H,W,C) float/uint8 자동 대응
    - 출력: 모델별 상이함 → 후처리는 사용자 정의 콜백으로 처리
      ex) decode_fn(tensors, (orig_w,orig_h), (inp_w,inp_h)) -> boxes,scores,classes
    """
    def __init__(self, model: str):
        if _tflite_runtime is not None:
            Interpreter = _tflite_runtime.Interpreter
        elif _tf is not None:
            Interpreter = _tf.lite.Interpreter
        else:
            raise RuntimeError("TFLite 인터프리터가 없습니다. tflite-runtime 또는 tensorflow 필요")
        self.inter = Interpreter(model_path=model)
        self.inter.allocate_tensors()
        self.inputs = self.inter.get_input_details()
        self.outputs = self.inter.get_output_details()
        if len(self.inputs) != 1:
            raise ValueError("현재 1 입력만 지원합니다.")

    def _prep(self, img: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        h, w = self.inputs[0]["shape"][1:3]
        x = cv2.resize(img, (w, h))
        if self.inputs[0]["dtype"] == np.float32:
            x = (x.astype(np.float32) / 255.0)[None, ...]
        else:
            x = x[None, ...]
        return x, (w, h)

    def infer(self, img: np.ndarray,
              decode_fn: Callable[[List[np.ndarray], tuple[int, int], tuple[int, int]], Any]):
        """
        img: BGR np.ndarray (H,W,3)
        decode_fn: 모델별 후처리 콜백
          - 인자: (raw_tensors, (orig_w,orig_h), (inp_w,inp_h))
          - 예시 리턴: (boxes[N,4 xyxy], scores[N], classes[N]) 등
        """
        x, wh = self._prep(img)
        self.inter.set_tensor(self.inputs[0]["index"], x)
        self.inter.invoke()
        outs = [self.inter.get_tensor(o["index"]) for o in self.outputs]
        return decode_fn(outs, img.shape[1::-1], wh)


# 6) OpenCV 추적기 생성 방어적 폴백(선택사항, 호환성 강화) ----------------------
def create_tracker(name: str = "CSRT"):
    name = name.upper()
    # 1) legacy 네임스페이스 우선
    try:
        if hasattr(cv2, "legacy"):
            fn = getattr(cv2.legacy, f"Tracker{name}_create", None)
            if callable(fn):
                return fn()
    except Exception:
        pass
    # 2) 구버전 API 폴백
    fn2 = getattr(cv2, f"Tracker{name}_create", None)
    if callable(fn2):
        return fn2()
    # 3) 최종 실패
    raise RuntimeError(f"{name} tracker 생성 실패: opencv-contrib-python 설치가 필요할 수 있습니다.")


# 7) 실전 유틸 5종 -------------------------------------------------------------

def iou(a_xyxy: tuple[int,int,int,int], b_xyxy: tuple[int,int,int,int]) -> float:
    """두 박스(xyxy)의 IoU(Intersection-over-Union)."""
    ax1, ay1, ax2, ay2 = a_xyxy
    bx1, by1, bx2, by2 = b_xyxy
    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, inter_x2 - inter_x1), max(0, inter_y2 - inter_y1)
    inter = iw * ih
    a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = a + b - inter
    return float(inter / union) if union > 0 else 0.0


def nms(boxes_xyxy: np.ndarray, scores: np.ndarray, iou_th: float = 0.45) -> List[int]:
    """간단 NMS. 입력: boxes[N,4](xyxy), scores[N]. 출력: keep 인덱스 리스트."""
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
        ious = np.array([iou(tuple(boxes_xyxy[i]), tuple(boxes_xyxy[j])) for j in rest])
        idxs = rest[ious <= iou_th]
    return keep


def largest_contour(contours: Iterable[np.ndarray]) -> Optional[np.ndarray]:
    """가장 넓은 컨투어 반환(없으면 None)."""
    try:
        return max(contours, key=cv2.contourArea)
    except ValueError:  # empty iterable
        return None


def contour_centroid(c: np.ndarray) -> Optional[tuple[int,int]]:
    """컨투어 무게중심(정수 픽셀). 실패 시 None."""
    if c is None or len(c) == 0:
        return None
    M = cv2.moments(c)
    if M['m00'] == 0:
        return None
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    return (cx, cy)


def scale_box_from_letterbox(box_xyxy: tuple[int,int,int,int],
                             r: float,
                             pad: tuple[int,int]) -> tuple[int,int,int,int]:
    """
    letterbox 좌표(xyxy, 패딩 이미지 기준)를 원본 이미지 좌표(xyxy)로 복원.
    - box_xyxy: (x1,y1,x2,y2) on padded image
    - r: letterbox 반환 배율(float)
    - pad: (left, top)
    """
    x1, y1, x2, y2 = box_xyxy
    left, top = pad
    x1 = (x1 - left) / r
    y1 = (y1 - top) / r
    x2 = (x2 - left) / r
    y2 = (y2 - top) / r
    return int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))


# 8) 메타데이터 및 공개 심볼 ---------------------------------------------------
__version__ = f"{_ENH_VER}+ai.3"
__all__ = sorted(set(list(_ENH_ALL) + [
    # vision_enhanced에서 가져온 공개 심볼 + 본 파일에서 추가하는 심볼
    "TFLiteDetector",
    "xywh_to_xyxy", "xyxy_to_xywh",
    "letterbox",           # 문서화 래퍼(함수명 동일, 본 모듈 정의가 우선)
    "draw_box_xywh",       # xywh 편의 래퍼
    "create_tracker",      # 방어적 생성기
    # 추가 유틸 5종
    "iou", "nms", "largest_contour", "contour_centroid", "scale_box_from_letterbox",
]))


