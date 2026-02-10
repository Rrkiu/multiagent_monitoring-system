"""
Data Analytics Skill
이벤트 데이터 분석 및 통계 생성
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from skills.base_skill import BaseSkill, SkillMetadata
from tools.data_tools import load_events, parse_date


class DataAnalyticsSkill(BaseSkill):
    """
    이벤트 데이터 분석 Skill
    
    기능:
    - 이벤트 통계 계산
    - 추세 분석
    - 위험도 평가
    - 카메라별 분석
    - 시계열 분석
    """
    
    def _load_metadata(self) -> SkillMetadata:
        """메타데이터 로드"""
        return SkillMetadata(
            name="data_analytics",
            description="이벤트 데이터 분석 및 통계 생성",
            version="1.0.0",
            author="Safety Team",
            dependencies=["langchain-google-genai"],
            tags=["analytics", "statistics", "data", "events", "trend"]
        )
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """도구 초기화"""
        # config가 아직 로드되지 않았을 수 있으므로 안전하게 접근
        config = getattr(self, 'config', {})
        
        # LLM 초기화
        llm = ChatGoogleGenerativeAI(
            model=config.get('llm_model', settings.llm_model),
            temperature=0.0,
            google_api_key=settings.google_api_key
        )
        
        return {
            'llm': llm,
            'statistics_calculator': self._create_statistics_calculator(),
            'trend_analyzer': self._create_trend_analyzer(),
            'risk_assessor': self._create_risk_assessor(),
            'top_camera_finder': self._create_top_camera_finder()
        }
    
    def _create_statistics_calculator(self):
        """통계 계산 도구 생성"""
        def calculate(start_date: str, end_date: str) -> Dict:
            """기간별 통계 계산"""
            events = load_events()
            
            start = parse_date(start_date)
            end = parse_date(end_date).replace(hour=23, minute=59, second=59)
            
            # 기간 내 이벤트 필터링
            filtered = [
                e for e in events
                if start <= datetime.fromisoformat(e['timestamp']) <= end
            ]
            
            if not filtered:
                return {"error": "해당 기간에 발생한 이벤트가 없습니다."}
            
            # 통계 계산
            total_events = len(filtered)
            resolved = sum(1 for e in filtered if e['resolved'])
            unresolved = total_events - resolved
            
            # 타입별, 심각도별, 카메라별 집계
            type_counts = Counter(e['event_type'] for e in filtered)
            severity_counts = Counter(e['severity'] for e in filtered)
            camera_counts = Counter(e['camera_id'] for e in filtered)
            
            return {
                "period": {"start_date": start_date, "end_date": end_date},
                "total_events": total_events,
                "resolved": resolved,
                "unresolved": unresolved,
                "resolution_rate": round(resolved / total_events * 100, 2) if total_events > 0 else 0,
                "by_event_type": dict(type_counts),
                "by_severity": dict(severity_counts),
                "by_camera": dict(camera_counts)
            }
        
        return calculate
    
    def _create_trend_analyzer(self):
        """추세 분석 도구 생성"""
        def analyze(current_start: str, current_end: str, 
                   previous_start: str, previous_end: str) -> Dict:
            """두 기간 비교 추세 분석"""
            events = load_events()
            
            # 현재 기간
            curr_start = parse_date(current_start)
            curr_end = parse_date(current_end).replace(hour=23, minute=59, second=59)
            current_events = [
                e for e in events
                if curr_start <= datetime.fromisoformat(e['timestamp']) <= curr_end
            ]
            
            # 이전 기간
            prev_start = parse_date(previous_start)
            prev_end = parse_date(previous_end).replace(hour=23, minute=59, second=59)
            previous_events = [
                e for e in events
                if prev_start <= datetime.fromisoformat(e['timestamp']) <= prev_end
            ]
            
            curr_count = len(current_events)
            prev_count = len(previous_events)
            
            # 증감률 계산
            if prev_count > 0:
                change_rate = round((curr_count - prev_count) / prev_count * 100, 2)
            else:
                change_rate = 100.0 if curr_count > 0 else 0.0
            
            # 타입별 증감
            curr_types = Counter(e['event_type'] for e in current_events)
            prev_types = Counter(e['event_type'] for e in previous_events)
            
            type_changes = {}
            all_types = set(curr_types.keys()) | set(prev_types.keys())
            
            for event_type in all_types:
                curr = curr_types.get(event_type, 0)
                prev = prev_types.get(event_type, 0)
                
                if prev > 0:
                    rate = round((curr - prev) / prev * 100, 2)
                else:
                    rate = 100.0 if curr > 0 else 0.0
                
                type_changes[event_type] = {
                    "current": curr,
                    "previous": prev,
                    "change": curr - prev,
                    "change_rate": rate
                }
            
            return {
                "current_period": {
                    "start": current_start,
                    "end": current_end,
                    "total_events": curr_count
                },
                "previous_period": {
                    "start": previous_start,
                    "end": previous_end,
                    "total_events": prev_count
                },
                "overall_change": curr_count - prev_count,
                "overall_change_rate": change_rate,
                "by_event_type": type_changes
            }
        
        return analyze
    
    def _create_risk_assessor(self):
        """위험도 평가 도구 생성"""
        def assess(camera_id: Optional[str] = None, days: int = 7) -> Dict:
            """위험도 평가"""
            events = load_events()
            
            # 기간 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 필터링
            filtered = [
                e for e in events
                if start_date <= datetime.fromisoformat(e['timestamp']) <= end_date
            ]
            
            if camera_id:
                filtered = [e for e in filtered if e['camera_id'] == camera_id]
            
            if not filtered:
                target = f"카메라 {camera_id}" if camera_id else "시스템"
                return {"error": f"{target}에서 최근 {days}일간 발생한 이벤트가 없습니다."}
            
            # 위험도 점수 계산
            severity_scores = {
                "LOW": 1,
                "MEDIUM": 3,
                "HIGH": 7,
                "CRITICAL": 10
            }
            
            total_score = sum(severity_scores.get(e['severity'], 0) for e in filtered)
            avg_score = total_score / len(filtered)
            
            # 미해결 이벤트
            unresolved = [e for e in filtered if not e['resolved']]
            critical_unresolved = [e for e in unresolved if e['severity'] == 'CRITICAL']
            
            # 위험 수준 결정
            if critical_unresolved or avg_score >= 7:
                risk_level = "CRITICAL"
            elif avg_score >= 5 or len(unresolved) > len(filtered) * 0.5:
                risk_level = "HIGH"
            elif avg_score >= 3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return {
                "target": camera_id if camera_id else "전체 시스템",
                "period_days": days,
                "total_events": len(filtered),
                "unresolved_events": len(unresolved),
                "critical_unresolved": len(critical_unresolved),
                "average_severity_score": round(avg_score, 2),
                "risk_level": risk_level,
                "recommendation": self._get_risk_recommendation(risk_level)
            }
        
        return assess
    
    def _create_top_camera_finder(self):
        """상위 카메라 검색 도구 생성"""
        def find(start_date: str, end_date: str, limit: int = 3) -> Dict:
            """가장 많은 이벤트가 발생한 카메라 찾기"""
            events = load_events()
            
            start = parse_date(start_date)
            end = parse_date(end_date).replace(hour=23, minute=59, second=59)
            
            # 기간 내 이벤트 필터링
            filtered = [
                e for e in events
                if start <= datetime.fromisoformat(e['timestamp']) <= end
            ]
            
            if not filtered:
                return {"error": "해당 기간에 발생한 이벤트가 없습니다."}
            
            # 카메라별 집계
            camera_stats = {}
            for event in filtered:
                cam_id = event['camera_id']
                cam_name = event['camera_name']
                
                if cam_id not in camera_stats:
                    camera_stats[cam_id] = {
                        "camera_id": cam_id,
                        "camera_name": cam_name,
                        "total_events": 0,
                        "event_types": Counter()
                    }
                
                camera_stats[cam_id]["total_events"] += 1
                camera_stats[cam_id]["event_types"][event['event_type']] += 1
            
            # 이벤트 수로 정렬
            sorted_cameras = sorted(
                camera_stats.values(),
                key=lambda x: x["total_events"],
                reverse=True
            )[:limit]
            
            # Counter를 dict로 변환
            for cam in sorted_cameras:
                cam["event_types"] = dict(cam["event_types"])
            
            return {
                "period": {"start_date": start_date, "end_date": end_date},
                "top_cameras": sorted_cameras
            }
        
        return find
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Data Analytics 실행
        
        Args:
            task: 수행할 작업
            context: 작업 컨텍스트
            
        Returns:
            작업 결과
        """
        if context is None:
            context = {}
        
        # Task 라우팅
        if task == "calculate_statistics":
            return self._calculate_statistics(context)
        elif task == "analyze_trend":
            return self._analyze_trend(context)
        elif task == "assess_risk":
            return self._assess_risk(context)
        elif task == "find_top_cameras":
            return self._find_top_cameras(context)
        elif task == "analyze_query":
            return self._analyze_query(context)
        else:
            raise ValueError(f"Unknown task: {task}")
    
    def _calculate_statistics(self, context: Dict) -> Dict:
        """통계 계산"""
        start_date = context.get('start_date')
        end_date = context.get('end_date')
        
        if not start_date or not end_date:
            return {"error": "start_date와 end_date가 필요합니다."}
        
        result = self.tools['statistics_calculator'](start_date, end_date)
        return result
    
    def _analyze_trend(self, context: Dict) -> Dict:
        """추세 분석"""
        current_start = context.get('current_start')
        current_end = context.get('current_end')
        previous_start = context.get('previous_start')
        previous_end = context.get('previous_end')
        
        if not all([current_start, current_end, previous_start, previous_end]):
            return {"error": "모든 기간 정보가 필요합니다."}
        
        result = self.tools['trend_analyzer'](
            current_start, current_end,
            previous_start, previous_end
        )
        return result
    
    def _assess_risk(self, context: Dict) -> Dict:
        """위험도 평가"""
        camera_id = context.get('camera_id')
        days = context.get('days', 7)
        
        result = self.tools['risk_assessor'](camera_id, days)
        return result
    
    def _find_top_cameras(self, context: Dict) -> Dict:
        """상위 카메라 찾기"""
        start_date = context.get('start_date')
        end_date = context.get('end_date')
        limit = context.get('limit', 3)
        
        if not start_date or not end_date:
            return {"error": "start_date와 end_date가 필요합니다."}
        
        result = self.tools['top_camera_finder'](start_date, end_date, limit)
        return result
    
    def _analyze_query(self, context: Dict) -> Dict:
        """자연어 쿼리 분석 (LLM 사용)"""
        query = context.get('query', '')
        
        if not query:
            return {"error": "query가 필요합니다."}
        
        # 날짜 정보 생성
        date_info = self._get_current_date_info()
        
        # LLM에게 어떤 도구를 사용할지 물어보기
        planning_prompt = self.get_prompt('query_planning')
        if not planning_prompt:
            planning_prompt = self._get_default_planning_prompt()
        
        planning_prompt = planning_prompt.format(
            date_info=date_info,
            user_query=query
        )
        
        try:
            # LLM에게 계획 요청
            planning_response = self.tools['llm'].invoke(planning_prompt)
            planning_text = planning_response.content
            
            # JSON 추출
            import re
            planning_text = planning_text.replace('```json', '').replace('```', '').strip()
            json_match = re.search(r'\{[\s\S]*\}', planning_text)
            
            if not json_match:
                return {"error": "도구 선택에 실패했습니다."}
            
            plan = json.loads(json_match.group())
            tool_name = plan.get("tool")
            parameters = plan.get("parameters", {})
            
            # 도구 실행
            if tool_name == "calculate_statistics":
                result = self._calculate_statistics(parameters)
            elif tool_name == "analyze_trend":
                result = self._analyze_trend(parameters)
            elif tool_name == "assess_risk":
                result = self._assess_risk(parameters)
            elif tool_name == "find_top_cameras":
                result = self._find_top_cameras(parameters)
            else:
                return {"error": f"알 수 없는 도구: {tool_name}"}
            
            # 결과를 자연어로 설명
            explanation_prompt = self._get_explanation_prompt(tool_name, result, query)
            explanation_response = self.tools['llm'].invoke(explanation_prompt)
            
            return {
                "raw_result": result,
                "explanation": explanation_response.content,
                "tool_used": tool_name
            }
            
        except Exception as e:
            return {"error": f"분석 처리 중 오류: {str(e)}"}
    
    def get_capabilities(self) -> List[str]:
        """Skill 기능 목록"""
        return [
            "calculate_statistics",
            "analyze_trend",
            "assess_risk",
            "find_top_cameras",
            "analyze_query"
        ]
    
    def validate_input(self, task: str, context: Dict[str, Any]) -> bool:
        """입력 검증"""
        if task == "calculate_statistics" or task == "find_top_cameras":
            return 'start_date' in context and 'end_date' in context
        elif task == "analyze_trend":
            return all(k in context for k in ['current_start', 'current_end', 
                                               'previous_start', 'previous_end'])
        elif task == "assess_risk":
            return 'days' in context or True  # days는 선택사항
        elif task == "analyze_query":
            return 'query' in context
        return False
    
    # Helper methods
    
    def _get_current_date_info(self) -> str:
        """현재 날짜 정보 반환"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        month_ago = today - timedelta(days=30)
        
        return f"""
오늘 날짜: {today.strftime('%Y-%m-%d')}
어제 날짜: {yesterday.strftime('%Y-%m-%d')}
7일 전: {week_ago.strftime('%Y-%m-%d')}
14일 전: {two_weeks_ago.strftime('%Y-%m-%d')}
30일 전: {month_ago.strftime('%Y-%m-%d')}
"""
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """위험 수준에 따른 권장 사항"""
        recommendations = {
            "LOW": "현재 안전 수준이 양호합니다. 정기적인 모니터링을 계속하세요.",
            "MEDIUM": "주의가 필요합니다. 미해결 이벤트를 우선 처리하고 안전 교육을 강화하세요.",
            "HIGH": "즉시 조치가 필요합니다. 모든 미해결 이벤트를 긴급 점검하고 안전 관리자 회의를 소집하세요.",
            "CRITICAL": "긴급 상황입니다. 즉시 현장 작업을 중단하고 전체 안전 점검을 실시하세요."
        }
        return recommendations.get(risk_level, "평가 불가")
    
    def _get_default_planning_prompt(self) -> str:
        """기본 계획 프롬프트"""
        return """당신은 안전 모니터링 시스템의 데이터 분석 전문가입니다.

현재 날짜 정보:
{date_info}

사용자 요청: {user_query}

사용 가능한 도구:
1. calculate_statistics - 기간별 통계 계산
   파라미터: start_date, end_date (YYYY-MM-DD)
   
2. find_top_cameras - 상위 카메라 찾기
   파라미터: start_date, end_date, limit (선택)
   
3. analyze_trend - 추세 분석
   파라미터: current_start, current_end, previous_start, previous_end
   
4. assess_risk - 위험도 평가
   파라미터: camera_id (선택), days

어떤 도구를 사용해야 하는지 JSON 형식으로만 답변하세요.

{{
  "tool": "도구_이름",
  "parameters": {{
    "param1": "value1"
  }}
}}"""
    
    def _get_explanation_prompt(self, tool_name: str, result: Dict, query: str) -> str:
        """설명 프롬프트 생성"""
        return f"""다음은 {tool_name} 도구의 실행 결과입니다:

{json.dumps(result, ensure_ascii=False, indent=2)}

사용자 요청: {query}

위 데이터를 바탕으로 사용자가 이해하기 쉽도록 한국어로 설명해주세요.
- 구체적인 숫자와 퍼센트를 포함하세요
- 주요 인사이트를 강조하세요
- 필요하면 권장 사항을 제시하세요
- 명확하고 간결하게 작성하세요"""
