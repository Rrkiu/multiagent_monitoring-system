"""
Vision Tools
이미지 처리 및 멀티모달 작업을 위한 도구들
"""

import base64
import io
import os
from pathlib import Path
from typing import Union, List, Optional
from PIL import Image
import requests
from config import settings


def load_image_from_path(image_path: str) -> Image.Image:
    """
    파일 경로에서 이미지 로드
    
    Args:
        image_path: 이미지 파일 경로
        
    Returns:
        PIL Image 객체
    """
    try:
        image = Image.open(image_path)
        return image
    except Exception as e:
        raise ValueError(f"이미지 로드 실패: {str(e)}")


def load_image_from_url(image_url: str) -> Image.Image:
    """
    URL에서 이미지 로드
    
    Args:
        image_url: 이미지 URL
        
    Returns:
        PIL Image 객체
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        return image
    except Exception as e:
        raise ValueError(f"URL에서 이미지 로드 실패: {str(e)}")


def load_image_from_base64(base64_string: str) -> Image.Image:
    """
    Base64 문자열에서 이미지 로드
    
    Args:
        base64_string: Base64 인코딩된 이미지 문자열
        
    Returns:
        PIL Image 객체
    """
    try:
        # data:image/png;base64, 접두사 제거
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        raise ValueError(f"Base64에서 이미지 로드 실패: {str(e)}")


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    PIL Image를 Base64 문자열로 변환
    
    Args:
        image: PIL Image 객체
        format: 이미지 포맷 (PNG, JPEG 등)
        
    Returns:
        Base64 인코딩된 문자열
    """
    try:
        buffered = io.BytesIO()
        image.save(buffered, format=format)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    except Exception as e:
        raise ValueError(f"이미지를 Base64로 변환 실패: {str(e)}")


def resize_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
    """
    이미지 리사이징 (비율 유지)
    
    Args:
        image: PIL Image 객체
        max_size: 최대 너비/높이
        
    Returns:
        리사이징된 PIL Image 객체
    """
    try:
        # 이미 작으면 그대로 반환
        if max(image.size) <= max_size:
            return image
        
        # 비율 유지하며 리사이징
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return image
    except Exception as e:
        raise ValueError(f"이미지 리사이징 실패: {str(e)}")


def validate_image_format(image_path: str) -> bool:
    """
    이미지 포맷 검증
    
    Args:
        image_path: 이미지 파일 경로
        
    Returns:
        유효한 포맷이면 True
    """
    ext = Path(image_path).suffix.lower().lstrip('.')
    return ext in settings.supported_image_formats


def validate_image_size(image_path: str) -> bool:
    """
    이미지 파일 크기 검증
    
    Args:
        image_path: 이미지 파일 경로
        
    Returns:
        허용된 크기 이내면 True
    """
    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    return file_size_mb <= settings.max_image_size_mb


def prepare_image_for_gemini(
    image_source: Union[str, Image.Image],
    resize: bool = True,
    max_size: int = 1024
) -> Image.Image:
    """
    Gemini API에 전송할 이미지 준비
    
    Args:
        image_source: 이미지 경로, URL, 또는 PIL Image 객체
        resize: 리사이징 여부
        max_size: 최대 크기
        
    Returns:
        처리된 PIL Image 객체
    """
    # 이미지 로드
    if isinstance(image_source, str):
        if image_source.startswith('http://') or image_source.startswith('https://'):
            image = load_image_from_url(image_source)
        elif image_source.startswith('data:image'):
            image = load_image_from_base64(image_source)
        else:
            # 파일 경로
            if not validate_image_format(image_source):
                raise ValueError(f"지원하지 않는 이미지 포맷입니다. 지원 포맷: {settings.supported_image_formats}")
            
            if not validate_image_size(image_source):
                raise ValueError(f"이미지 크기가 너무 큽니다. 최대 크기: {settings.max_image_size_mb}MB")
            
            image = load_image_from_path(image_source)
    elif isinstance(image_source, Image.Image):
        image = image_source
    else:
        raise ValueError("지원하지 않는 이미지 소스 타입입니다.")
    
    # RGB 변환 (RGBA, Grayscale 등 처리)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 리사이징
    if resize:
        image = resize_image(image, max_size)
    
    return image


def save_uploaded_image(image: Image.Image, filename: str) -> str:
    """
    업로드된 이미지를 저장
    
    Args:
        image: PIL Image 객체
        filename: 저장할 파일명
        
    Returns:
        저장된 파일 경로
    """
    try:
        # 업로드 디렉토리 생성
        upload_dir = Path(settings.image_upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        file_path = upload_dir / filename
        image.save(file_path)
        
        return str(file_path)
    except Exception as e:
        raise ValueError(f"이미지 저장 실패: {str(e)}")


def process_multiple_images(
    image_sources: List[Union[str, Image.Image]],
    resize: bool = True,
    max_size: int = 1024
) -> List[Image.Image]:
    """
    여러 이미지를 일괄 처리
    
    Args:
        image_sources: 이미지 소스 리스트
        resize: 리사이징 여부
        max_size: 최대 크기
        
    Returns:
        처리된 PIL Image 객체 리스트
    """
    processed_images = []
    
    for source in image_sources:
        try:
            image = prepare_image_for_gemini(source, resize, max_size)
            processed_images.append(image)
        except Exception as e:
            print(f"이미지 처리 실패: {source}, 오류: {str(e)}")
            continue
    
    return processed_images


# LangChain Tool로 사용할 함수들
def analyze_image_content(image_path: str) -> str:
    """
    이미지 내용 분석 (LangChain Tool용)
    
    Args:
        image_path: 이미지 파일 경로
        
    Returns:
        이미지 정보 문자열
    """
    try:
        image = prepare_image_for_gemini(image_path)
        
        info = {
            "크기": f"{image.size[0]}x{image.size[1]}",
            "포맷": image.format or "Unknown",
            "모드": image.mode,
            "파일": image_path
        }
        
        return f"이미지 정보: {info}"
    except Exception as e:
        return f"이미지 분석 실패: {str(e)}"
