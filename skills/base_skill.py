"""
Base Skill Interface
모든 Skill의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from pathlib import Path
import yaml


class SkillMetadata(BaseModel):
    """Skill 메타데이터"""
    name: str
    description: str
    version: str
    author: str = "Safety Team"
    dependencies: List[str] = []
    tags: List[str] = []


class BaseSkill(ABC):
    """
    모든 Skill의 기본 클래스
    
    각 Skill은 이 클래스를 상속받아 구현해야 합니다.
    """
    
    def __init__(self):
        """Skill 초기화"""
        self.metadata = self._load_metadata()
        self.tools = self._initialize_tools()
        self.prompts = self._load_prompts()
        self.config = self._load_config()
    
    @abstractmethod
    def _load_metadata(self) -> SkillMetadata:
        """
        SKILL.md에서 메타데이터 로드
        
        Returns:
            SkillMetadata: Skill 메타데이터
        """
        pass
    
    @abstractmethod
    def _initialize_tools(self) -> Dict[str, Any]:
        """
        Skill에서 사용할 도구들 초기화
        
        Returns:
            Dict[str, Any]: 도구 딕셔너리
        """
        pass
    
    def _load_prompts(self) -> Dict[str, str]:
        """
        프롬프트 템플릿 로드
        
        Returns:
            Dict[str, str]: 프롬프트 딕셔너리
        """
        prompts_dir = self._get_skill_dir() / "prompts"
        prompts = {}
        
        if prompts_dir.exists():
            for prompt_file in prompts_dir.glob("*.txt"):
                prompt_name = prompt_file.stem
                prompts[prompt_name] = prompt_file.read_text(encoding='utf-8')
        
        return prompts
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Skill 설정 로드
        
        Returns:
            Dict[str, Any]: 설정 딕셔너리
        """
        config_file = self._get_skill_dir() / "config.yaml"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        return {}
    
    def _get_skill_dir(self) -> Path:
        """
        현재 Skill의 디렉토리 경로 반환
        
        Returns:
            Path: Skill 디렉토리 경로
        """
        return Path(__file__).parent
    
    @abstractmethod
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Skill 실행
        
        Args:
            task: 수행할 작업 (예: "detect_ppe", "assess_safety")
            context: 작업 컨텍스트 (이미지 경로, 쿼리 등)
            
        Returns:
            Dict[str, Any]: 작업 결과
        """
        pass
    
    def get_capabilities(self) -> List[str]:
        """
        Skill이 수행할 수 있는 작업 목록
        
        Returns:
            List[str]: 작업 목록
        """
        return []
    
    def validate_input(self, task: str, context: Dict[str, Any]) -> bool:
        """
        입력 데이터 검증
        
        Args:
            task: 작업 이름
            context: 작업 컨텍스트
            
        Returns:
            bool: 유효하면 True
        """
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Skill 메타데이터 반환
        
        Returns:
            Dict[str, Any]: 메타데이터 딕셔너리
        """
        return self.metadata.dict()
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        특정 프롬프트 가져오기
        
        Args:
            prompt_name: 프롬프트 이름
            
        Returns:
            Optional[str]: 프롬프트 텍스트
        """
        return self.prompts.get(prompt_name)
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        프롬프트 템플릿에 변수 삽입
        
        Args:
            prompt_name: 프롬프트 이름
            **kwargs: 템플릿 변수
            
        Returns:
            str: 포맷팅된 프롬프트
        """
        prompt = self.get_prompt(prompt_name)
        if prompt:
            return prompt.format(**kwargs)
        return ""
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.metadata.name} version={self.metadata.version}>"
