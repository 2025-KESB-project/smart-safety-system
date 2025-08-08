
import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from pathlib import Path
from loguru import logger

# 프로젝트 루트를 기준으로 폰트 경로를 설정합니다.
# 이 파일을 기준으로 세 번 상위 폴더로 올라가야 프로젝트 루트입니다.
DEFAULT_FONT_PATH = str(Path(__file__).resolve().parent.parent / 'assets/fonts/NanumGothicBold.ttf')

def put_text_korean(
    image: np.ndarray, 
    text: str, 
    position: tuple, 
    font_size: int, 
    color: tuple,
    font_path: str = DEFAULT_FONT_PATH
) -> np.ndarray:
    """
    OpenCV 이미지(np.ndarray)에 Pillow를 사용하여 한글 텍스트를 렌더링합니다.

    Args:
        image (np.ndarray): 텍스트를 추가할 OpenCV 이미지 (BGR 형식).
        text (str): 추가할 한글 텍스트.
        position (tuple): 텍스트를 추가할 위치 (x, y).
        font_size (int): 폰트 크기.
        color (tuple): 텍스트 색상 (B, G, R).
        font_path (str, optional): 사용할 TTF 폰트 파일의 경로. 
                                   기본값은 'assets/fonts/NanumGothicBold.ttf'입니다.

    Returns:
        np.ndarray: 텍스트가 추가된 OpenCV 이미지.
    """
    # 폰트 파일 존재 여부 확인
    if not Path(font_path).exists():
        # 경고 메시지를 한 번만 출력하기 위해 간단한 캐시 사용
        if not hasattr(put_text_korean, 'font_warning_logged'):
            logger.warning(f"폰트 파일을 찾을 수 없습니다: {font_path}. 텍스트 렌더링이 올바르게 동작하지 않을 수 있습니다.")
            put_text_korean.font_warning_logged = True
        # OpenCV의 기본 영어 폰트로 대체하여 오류 메시지 출력
        cv2.putText(image, f"Font not found!", position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return image

    try:
        # 1. OpenCV 이미지를 Pillow 이미지로 변환 (BGR -> RGB)
        img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # 2. Pillow의 ImageDraw 객체 생성 및 폰트 로드
        draw = ImageDraw.Draw(img_pil)
        font = ImageFont.truetype(font_path, font_size)

        # 3. 텍스트 렌더링 (Pillow는 RGB 색상 순서 사용)
        draw.text(position, text, font=font, fill=(color[2], color[1], color[0]))

        # 4. 다시 OpenCV 이미지(Numpy 배열)로 변환 (RGB -> BGR)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.error(f"한글 텍스트 렌더링 중 오류 발생: {e}")
        return image # 오류 발생 시 원본 이미지 반환
