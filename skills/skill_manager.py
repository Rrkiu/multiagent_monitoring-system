"""
Skill Manager
Skills를 관리하는 중앙 관리자
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import importlib
import sys

from skills.base_skill import BaseSkill


class SkillManager:
    """
    Skills를 관리하는 중앙 관리자
    
    - Skill 로드 및 초기화
    - Skill 실행
    - Skill 목록 관리
    """
    
    def __init__(self, skills_dir: str = "skills"):
        """
        SkillManager 초기화
        
        Args:
            skills_dir: Skills 디렉토리 경로
        """
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, BaseSkill] = {}
        self._ensure_skills_dir()
        self._load_all_skills()
    
    def _ensure_skills_dir(self):
        """Skills 디렉토리가 존재하는지 확인"""
        if not self.skills_dir.exists():
            raise FileNotFoundError(f"Skills directory not found: {self.skills_dir}")
    
    def _load_all_skills(self):
        """모든 Skills 로드"""
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir() and not skill_path.name.startswith('_'):
                skill_file = skill_path / "skill.py"
                if skill_file.exists():
                    try:
                        self._load_skill(skill_path.name)
                        print(f"✅ Loaded skill: {skill_path.name}")
                    except Exception as e:
                        print(f"❌ Failed to load skill {skill_path.name}: {str(e)}")
    
    def _load_skill(self, skill_name: str):
        """
        개별 Skill 로드
        
        Args:
            skill_name: Skill 이름 (디렉토리 이름)
        """
        try:
            # 모듈 임포트
            module_path = f"skills.{skill_name}.skill"
            module = importlib.import_module(module_path)
            
            # Skill 클래스 찾기
            class_name = self._to_class_name(skill_name)
            skill_class = getattr(module, class_name)
            
            # Skill 인스턴스 생성
            self.skills[skill_name] = skill_class()
            
        except Exception as e:
            raise ImportError(f"Failed to load skill '{skill_name}': {str(e)}")
    
    def reload_skill(self, skill_name: str):
        """
        Skill 재로드 (개발 중 유용)
        
        Args:
            skill_name: Skill 이름
        """
        if skill_name in self.skills:
            del self.skills[skill_name]
        
        # 모듈 재로드
        module_path = f"skills.{skill_name}.skill"
        if module_path in sys.modules:
            importlib.reload(sys.modules[module_path])
        
        self._load_skill(skill_name)
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """
        Skill 가져오기
        
        Args:
            skill_name: Skill 이름
            
        Returns:
            Optional[BaseSkill]: Skill 인스턴스 또는 None
        """
        return self.skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """
        사용 가능한 Skill 목록
        
        Returns:
            List[str]: Skill 이름 리스트
        """
        return list(self.skills.keys())
    
    def get_all_skills_metadata(self) -> List[Dict[str, Any]]:
        """
        모든 Skills의 메타데이터 반환
        
        Returns:
            List[Dict[str, Any]]: 메타데이터 리스트
        """
        return [
            skill.get_metadata()
            for skill in self.skills.values()
        ]
    
    def execute_skill(
        self,
        skill_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Skill 실행
        
        Args:
            skill_name: Skill 이름
            task: 수행할 작업
            context: 작업 컨텍스트
            
        Returns:
            Dict[str, Any]: 작업 결과
            
        Raises:
            ValueError: Skill을 찾을 수 없는 경우
        """
        skill = self.get_skill(skill_name)
        
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
        
        # 입력 검증
        if not skill.validate_input(task, context or {}):
            raise ValueError(f"Invalid input for skill '{skill_name}' task '{task}'")
        
        # Skill 실행
        try:
            result = skill.execute(task, context)
            return {
                'success': True,
                'skill': skill_name,
                'task': task,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'skill': skill_name,
                'task': task,
                'error': str(e)
            }
    
    def get_skill_capabilities(self, skill_name: str) -> List[str]:
        """
        특정 Skill의 기능 목록
        
        Args:
            skill_name: Skill 이름
            
        Returns:
            List[str]: 기능 목록
        """
        skill = self.get_skill(skill_name)
        if skill:
            return skill.get_capabilities()
        return []
    
    def find_skills_by_tag(self, tag: str) -> List[str]:
        """
        태그로 Skill 검색
        
        Args:
            tag: 검색할 태그
            
        Returns:
            List[str]: 해당 태그를 가진 Skill 이름 리스트
        """
        matching_skills = []
        
        for skill_name, skill in self.skills.items():
            if tag in skill.metadata.tags:
                matching_skills.append(skill_name)
        
        return matching_skills
    
    def find_skill_for_task(self, task_description: str) -> Optional[str]:
        """
        작업 설명으로 적합한 Skill 찾기 (간단한 키워드 매칭)
        
        Args:
            task_description: 작업 설명
            
        Returns:
            Optional[str]: Skill 이름 또는 None
        """
        task_lower = task_description.lower()
        
        # 키워드 매핑
        keyword_mapping = {
            'image': 'vision_analysis',
            'vision': 'vision_analysis',
            'ppe': 'vision_analysis',
            'safety': 'vision_analysis',
            'search': 'web_intelligence',
            'web': 'web_intelligence',
            'regulation': 'web_intelligence',
            'statistics': 'data_analytics',
            'analytics': 'data_analytics',
            'trend': 'data_analytics',
            'report': 'report_generation',
            'knowledge': 'knowledge_management',
            'rag': 'knowledge_management',
            'security': 'security_validation',
            'validate': 'security_validation'
        }
        
        for keyword, skill_name in keyword_mapping.items():
            if keyword in task_lower and skill_name in self.skills:
                return skill_name
        
        return None
    
    @staticmethod
    def _to_class_name(skill_name: str) -> str:
        """
        skill_name을 클래스명으로 변환
        
        예: vision_analysis -> VisionAnalysisSkill
        
        Args:
            skill_name: Skill 이름
            
        Returns:
            str: 클래스명
        """
        return ''.join(word.capitalize() for word in skill_name.split('_')) + 'Skill'
    
    def __repr__(self) -> str:
        return f"<SkillManager skills={len(self.skills)} loaded={list(self.skills.keys())}>"
