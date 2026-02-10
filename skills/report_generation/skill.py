"""
Report Generation Skill
분석 결과 기반 보고서 생성
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from skills.base_skill import BaseSkill, SkillMetadata


class ReportGenerationSkill(BaseSkill):
    """
    보고서 생성 Skill
    
    기능:
    - 이벤트 보고서 생성
    - 통계 보고서 생성
    - 조치 방안 보고서 생성
    - 일일/주간/월간 보고서
    - 사고 분석 보고서
    """
    
    def _load_metadata(self) -> SkillMetadata:
        """메타데이터 로드"""
        return SkillMetadata(
            name="report_generation",
            description="분석 결과 기반 보고서 생성",
            version="1.0.0",
            author="Safety Team",
            dependencies=["langchain-google-genai"],
            tags=["report", "document", "analysis", "summary"]
        )
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """도구 초기화"""
        # config가 아직 로드되지 않았을 수 있으므로 안전하게 접근
        config = getattr(self, 'config', {})
        
        # LLM 초기화
        llm = ChatGoogleGenerativeAI(
            model=config.get('llm_model', settings.llm_model),
            temperature=config.get('temperature', 0.3),
            google_api_key=settings.google_api_key
        )
        
        return {
            'llm': llm,
            'event_report_generator': self._create_event_report_generator(llm),
            'statistics_report_generator': self._create_statistics_report_generator(llm),
            'action_plan_generator': self._create_action_plan_generator(llm),
            'summary_generator': self._create_summary_generator(llm),
            'incident_report_generator': self._create_incident_report_generator(llm)
        }
    
    def _create_event_report_generator(self, llm):
        """이벤트 보고서 생성 도구"""
        def generate(events: List[Dict], period: str = "일일") -> str:
            """이벤트 보고서 생성"""
            if not events:
                return "보고할 이벤트가 없습니다."
            
            # 프롬프트 가져오기
            prompt = self.get_prompt('event_report')
            if not prompt:
                prompt = self._get_default_event_report_prompt()
            
            # 이벤트 데이터 포맷팅
            events_text = self._format_events(events)
            
            prompt = prompt.format(
                period=period,
                events=events_text,
                total_events=len(events)
            )
            
            try:
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                return f"보고서 생성 중 오류: {str(e)}"
        
        return generate
    
    def _create_statistics_report_generator(self, llm):
        """통계 보고서 생성 도구"""
        def generate(statistics: Dict, period: str = "주간") -> str:
            """통계 보고서 생성"""
            if not statistics:
                return "통계 데이터가 없습니다."
            
            prompt = self.get_prompt('statistics_report')
            if not prompt:
                prompt = self._get_default_statistics_report_prompt()
            
            stats_text = json.dumps(statistics, ensure_ascii=False, indent=2)
            
            prompt = prompt.format(
                period=period,
                statistics=stats_text
            )
            
            try:
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                return f"통계 보고서 생성 중 오류: {str(e)}"
        
        return generate
    
    def _create_action_plan_generator(self, llm):
        """조치 방안 생성 도구"""
        def generate(event_data: Dict, knowledge_context: Optional[str] = None) -> str:
            """조치 방안 생성"""
            if not event_data:
                return "이벤트 데이터가 없습니다."
            
            prompt = self.get_prompt('action_plan')
            if not prompt:
                prompt = self._get_default_action_plan_prompt()
            
            event_text = json.dumps(event_data, ensure_ascii=False, indent=2)
            context = knowledge_context or "관련 지식 베이스 정보 없음"
            
            prompt = prompt.format(
                event=event_text,
                knowledge_context=context
            )
            
            try:
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                return f"조치 방안 생성 중 오류: {str(e)}"
        
        return generate
    
    def _create_summary_generator(self, llm):
        """요약 생성 도구"""
        def generate(content: str, max_length: int = 200) -> str:
            """내용 요약 생성"""
            if not content:
                return "요약할 내용이 없습니다."
            
            prompt = f"""다음 내용을 {max_length}자 이내로 요약해주세요:

{content}

요약 (핵심 내용만 간결하게):"""
            
            try:
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                return f"요약 생성 중 오류: {str(e)}"
        
        return generate
    
    def _create_incident_report_generator(self, llm):
        """사고 분석 보고서 생성 도구"""
        def generate(incident_data: Dict, analysis_data: Optional[Dict] = None) -> str:
            """사고 분석 보고서 생성"""
            if not incident_data:
                return "사고 데이터가 없습니다."
            
            prompt = self.get_prompt('incident_report')
            if not prompt:
                prompt = self._get_default_incident_report_prompt()
            
            incident_text = json.dumps(incident_data, ensure_ascii=False, indent=2)
            analysis_text = json.dumps(analysis_data, ensure_ascii=False, indent=2) if analysis_data else "분석 데이터 없음"
            
            prompt = prompt.format(
                incident=incident_text,
                analysis=analysis_text
            )
            
            try:
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                return f"사고 보고서 생성 중 오류: {str(e)}"
        
        return generate
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Report Generation 실행
        
        Args:
            task: 수행할 작업
            context: 작업 컨텍스트
            
        Returns:
            작업 결과
        """
        if context is None:
            context = {}
        
        # Task 라우팅
        if task == "generate_event_report":
            return self._generate_event_report(context)
        elif task == "generate_statistics_report":
            return self._generate_statistics_report(context)
        elif task == "generate_action_plan":
            return self._generate_action_plan(context)
        elif task == "generate_summary":
            return self._generate_summary(context)
        elif task == "generate_incident_report":
            return self._generate_incident_report(context)
        elif task == "generate_daily_report":
            return self._generate_daily_report(context)
        elif task == "generate_weekly_report":
            return self._generate_weekly_report(context)
        else:
            raise ValueError(f"Unknown task: {task}")
    
    def _generate_event_report(self, context: Dict) -> Dict:
        """이벤트 보고서 생성"""
        events = context.get('events', [])
        period = context.get('period', '일일')
        
        if not events:
            return {"error": "이벤트 데이터가 필요합니다."}
        
        report = self.tools['event_report_generator'](events, period)
        
        return {
            "report_type": "event_report",
            "period": period,
            "total_events": len(events),
            "report": report
        }
    
    def _generate_statistics_report(self, context: Dict) -> Dict:
        """통계 보고서 생성"""
        statistics = context.get('statistics', {})
        period = context.get('period', '주간')
        
        if not statistics:
            return {"error": "통계 데이터가 필요합니다."}
        
        report = self.tools['statistics_report_generator'](statistics, period)
        
        return {
            "report_type": "statistics_report",
            "period": period,
            "report": report
        }
    
    def _generate_action_plan(self, context: Dict) -> Dict:
        """조치 방안 생성"""
        event_data = context.get('event_data', {})
        knowledge_context = context.get('knowledge_context')
        
        if not event_data:
            return {"error": "이벤트 데이터가 필요합니다."}
        
        action_plan = self.tools['action_plan_generator'](event_data, knowledge_context)
        
        return {
            "report_type": "action_plan",
            "event_type": event_data.get('event_type', 'N/A'),
            "action_plan": action_plan
        }
    
    def _generate_summary(self, context: Dict) -> Dict:
        """요약 생성"""
        content = context.get('content', '')
        max_length = context.get('max_length', 200)
        
        if not content:
            return {"error": "요약할 내용이 필요합니다."}
        
        summary = self.tools['summary_generator'](content, max_length)
        
        return {
            "original_length": len(content),
            "summary_length": len(summary),
            "summary": summary
        }
    
    def _generate_incident_report(self, context: Dict) -> Dict:
        """사고 분석 보고서 생성"""
        incident_data = context.get('incident_data', {})
        analysis_data = context.get('analysis_data')
        
        if not incident_data:
            return {"error": "사고 데이터가 필요합니다."}
        
        report = self.tools['incident_report_generator'](incident_data, analysis_data)
        
        return {
            "report_type": "incident_report",
            "incident_id": incident_data.get('id', 'N/A'),
            "severity": incident_data.get('severity', 'N/A'),
            "report": report
        }
    
    def _generate_daily_report(self, context: Dict) -> Dict:
        """일일 보고서 생성 (통합)"""
        date = context.get('date', datetime.now().strftime('%Y-%m-%d'))
        events = context.get('events', [])
        statistics = context.get('statistics', {})
        
        # 이벤트 보고서
        event_report = ""
        if events:
            event_report = self.tools['event_report_generator'](events, "일일")
        
        # 통계 보고서
        stats_report = ""
        if statistics:
            stats_report = self.tools['statistics_report_generator'](statistics, "일일")
        
        # 통합 보고서 생성
        combined_report = f"""# 일일 안전 모니터링 보고서
날짜: {date}

## 1. 이벤트 현황
{event_report if event_report else "이벤트 없음"}

## 2. 통계 분석
{stats_report if stats_report else "통계 데이터 없음"}

---
보고서 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return {
            "report_type": "daily_report",
            "date": date,
            "total_events": len(events),
            "report": combined_report
        }
    
    def _generate_weekly_report(self, context: Dict) -> Dict:
        """주간 보고서 생성 (통합)"""
        start_date = context.get('start_date')
        end_date = context.get('end_date')
        events = context.get('events', [])
        statistics = context.get('statistics', {})
        trend_data = context.get('trend_data', {})
        
        period = f"{start_date} ~ {end_date}" if start_date and end_date else "주간"
        
        # 이벤트 보고서
        event_report = ""
        if events:
            event_report = self.tools['event_report_generator'](events, "주간")
        
        # 통계 보고서
        stats_report = ""
        if statistics:
            stats_report = self.tools['statistics_report_generator'](statistics, "주간")
        
        # 추세 분석
        trend_text = json.dumps(trend_data, ensure_ascii=False, indent=2) if trend_data else "추세 데이터 없음"
        
        # 통합 보고서 생성
        combined_report = f"""# 주간 안전 모니터링 보고서
기간: {period}

## 1. 이벤트 현황
{event_report if event_report else "이벤트 없음"}

## 2. 통계 분석
{stats_report if stats_report else "통계 데이터 없음"}

## 3. 추세 분석
{trend_text}

---
보고서 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return {
            "report_type": "weekly_report",
            "period": period,
            "total_events": len(events),
            "report": combined_report
        }
    
    def get_capabilities(self) -> List[str]:
        """Skill 기능 목록"""
        return [
            "generate_event_report",
            "generate_statistics_report",
            "generate_action_plan",
            "generate_summary",
            "generate_incident_report",
            "generate_daily_report",
            "generate_weekly_report"
        ]
    
    def validate_input(self, task: str, context: Dict[str, Any]) -> bool:
        """입력 검증"""
        if task == "generate_event_report":
            return 'events' in context
        elif task == "generate_statistics_report":
            return 'statistics' in context
        elif task == "generate_action_plan":
            return 'event_data' in context
        elif task == "generate_summary":
            return 'content' in context
        elif task == "generate_incident_report":
            return 'incident_data' in context
        elif task == "generate_daily_report" or task == "generate_weekly_report":
            return True  # 선택적 파라미터
        return False
    
    # Helper methods
    
    def _format_events(self, events: List[Dict]) -> str:
        """이벤트 데이터 포맷팅"""
        formatted = []
        for idx, event in enumerate(events, 1):
            formatted.append(f"""
이벤트 {idx}:
- ID: {event.get('id', 'N/A')}
- 타입: {event.get('event_type', 'N/A')}
- 심각도: {event.get('severity', 'N/A')}
- 카메라: {event.get('camera_name', 'N/A')} ({event.get('camera_id', 'N/A')})
- 시간: {event.get('timestamp', 'N/A')}
- 해결 여부: {'해결됨' if event.get('resolved') else '미해결'}
- 설명: {event.get('description', 'N/A')}
""")
        return "\n".join(formatted)
    
    def _get_default_event_report_prompt(self) -> str:
        """기본 이벤트 보고서 프롬프트"""
        return """당신은 안전 모니터링 시스템의 보고서 작성 전문가입니다.

다음 {period} 이벤트 데이터를 바탕으로 전문적인 보고서를 작성해주세요:

총 이벤트 수: {total_events}

{events}

보고서 작성 지침:
1. 명확하고 구조화된 형식으로 작성
2. 주요 이벤트를 우선순위별로 정리
3. 심각도가 높은 이벤트를 강조
4. 미해결 이벤트에 대한 조치 필요성 언급
5. 전문적이고 간결한 문체 사용

보고서:"""
    
    def _get_default_statistics_report_prompt(self) -> str:
        """기본 통계 보고서 프롬프트"""
        return """당신은 안전 모니터링 시스템의 데이터 분석 전문가입니다.

다음 {period} 통계 데이터를 바탕으로 분석 보고서를 작성해주세요:

{statistics}

보고서 작성 지침:
1. 주요 통계 지표를 명확하게 제시
2. 데이터에서 발견되는 패턴이나 트렌드 분석
3. 우려되는 부분을 강조
4. 개선이 필요한 영역 식별
5. 구체적인 숫자와 퍼센트 포함

분석 보고서:"""
    
    def _get_default_action_plan_prompt(self) -> str:
        """기본 조치 방안 프롬프트"""
        return """당신은 안전 관리 전문가입니다.

다음 이벤트에 대한 구체적인 조치 방안을 작성해주세요:

이벤트 정보:
{event}

관련 지식:
{knowledge_context}

조치 방안 작성 지침:
1. 즉시 조치 사항 (Immediate Actions)
2. 단기 조치 사항 (Short-term Actions)
3. 장기 예방 조치 (Long-term Prevention)
4. 관련 법규 및 규정 준수 사항
5. 담당자 및 책임 소재

조치 방안:"""
    
    def _get_default_incident_report_prompt(self) -> str:
        """기본 사고 보고서 프롬프트"""
        return """당신은 안전 사고 조사 전문가입니다.

다음 사고에 대한 상세 분석 보고서를 작성해주세요:

사고 정보:
{incident}

분석 데이터:
{analysis}

보고서 구성:
1. 사고 개요 (Incident Overview)
2. 발생 경위 (Sequence of Events)
3. 원인 분석 (Root Cause Analysis)
4. 영향 평가 (Impact Assessment)
5. 재발 방지 대책 (Prevention Measures)
6. 권고 사항 (Recommendations)

사고 분석 보고서:"""
