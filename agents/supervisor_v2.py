"""
Supervisor Agent V2
Skills 기반 아키텍처를 사용하는 개선된 Supervisor Agent
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from skills.skill_manager import SkillManager
import json
import re
from typing import Optional, Dict, Any


class SupervisorAgentV2:
    """Skills 기반 Supervisor Agent"""

    def __init__(self):
        """Supervisor Agent V2 초기화"""

        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.0,
            google_api_key=settings.google_api_key
        )

        # Skill Manager 초기화
        self.skill_manager = SkillManager()
        
        # 사용 가능한 Skills 목록
        self.available_skills = self.skill_manager.list_skills()
        print(f"✅ Skills 로드 완료: {self.available_skills}")

    def quick_route(self, user_input: str) -> Optional[str]:
        """
        규칙 기반 빠른 라우팅 (LLM 호출 없음)
        
        Args:
            user_input: 사용자 입력
            
        Returns:
            skill_name 또는 None (LLM 라우팅 필요)
        """
        
        # 키워드 기반 매핑
        keywords_map = {
            'data_analytics': [
                '통계', '분석', '추세', '위험도', '비교', '계산',
                '증감', '변화', '평가', '많은', '적은', '높은', '낮은'
            ],
            'report_generation': [
                '보고서', '조치', '방안', '대응', '작성', '생성',
                '가이드', '계획', '요약', '정리'
            ],
            'knowledge_management': [
                '검색', '찾아', '알려', '법규', '규정', '어떻게',
                '무엇', '왜', '설명', '안내', '교육'
            ],
            'vision_analysis': [
                '이미지', '사진', '영상', '분석', 'PPE', '착용',
                '감지', '확인', '비교'
            ]
        }
        
        # 각 Skill에 대해 키워드 매칭
        for skill, keywords in keywords_map.items():
            if any(kw in user_input for kw in keywords):
                print(f"[빠른 라우팅] {skill} (키워드 매칭)")
                return skill
        
        return None

    def llm_route(self, user_input: str) -> dict:
        """
        LLM 기반 라우팅 (복잡한 쿼리용)
        
        Args:
            user_input: 사용자 입력
            
        Returns:
            라우팅 계획
        """
        
        routing_prompt = f"""당신은 안전 모니터링 시스템의 작업 분배 관리자입니다.

사용자 요청: {user_input}

사용 가능한 Skills:
1. data_analytics - 데이터 분석 전담
   - 통계 계산
   - 추세 분석
   - 위험도 평가
   - 카메라별 분석
   예: "통계 분석해줘", "가장 위험한 카메라는?", "증감률 계산"

2. report_generation - 보고서 및 대응 방안 작성
   - 일일/주간 보고서 생성
   - 조치 방안 제공
   - 사고 보고서 작성
   예: "보고서 작성해줘", "대응 방안 알려줘", "조치 사항은?"

3. knowledge_management - 지식 검색 및 질문 답변
   - 안전 규정 검색
   - 조치 가이드 조회
   - 질문 답변 (RAG)
   예: "안전모 착용 규정은?", "낙상 사고 대응 방법은?", "법규 알려줘"

4. vision_analysis - 이미지 분석 전담
   - 안전 위반 사항 감지
   - PPE 착용 확인
   - 작업장 안전 평가
   예: "이 이미지 분석해줘", "안전모 착용 확인"
   주의: 이미지가 제공된 경우에만 사용

사용자 요청을 분석하여 어떤 Skill을 사용할지 결정하세요.

복잡한 요청의 경우 여러 Skills를 순차적으로 사용할 수 있습니다:
- 예: "가장 위험한 구역의 대응 방안" → data_analytics (위험 구역 찾기) → report_generation (대응 방안)
- 예: "오늘 이벤트 보고서" → data_analytics (통계) → report_generation (보고서 생성)

응답 형식 (JSON만):
{{
  "skill": "data_analytics" | "report_generation" | "knowledge_management" | "vision_analysis",
  "task": "구체적인 작업 설명",
  "reason": "선택 이유",
  "multi_step": false
}}

또는 멀티스텝인 경우:
{{
  "multi_step": true,
  "steps": [
    {{"skill": "data_analytics", "task": "구체적인 작업"}},
    {{"skill": "report_generation", "task": "구체적인 작업"}}
  ],
  "reason": "멀티스텝 이유"
}}"""

        try:
            response = self.llm.invoke(routing_prompt)
            response_text = response.content.replace('```json', '').replace('```', '').strip()

            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if not json_match:
                # 기본값: knowledge_management
                return {
                    "skill": "knowledge_management",
                    "task": user_input,
                    "multi_step": False,
                    "reason": "파싱 실패, 기본값 사용"
                }

            routing_plan = json.loads(json_match.group())
            return routing_plan

        except Exception as e:
            print(f"라우팅 오류: {e}")
            return {
                "skill": "knowledge_management",
                "task": user_input,
                "multi_step": False,
                "reason": f"오류 발생: {str(e)}"
            }

    def _determine_task(self, user_input: str, skill_name: str) -> str:
        """
        Skill에 전달할 구체적인 task 결정
        
        Args:
            user_input: 사용자 입력
            skill_name: Skill 이름
            
        Returns:
            task 이름
        """
        
        # Skill별 task 매핑
        task_mapping = {
            'data_analytics': {
                'keywords': {
                    '통계': 'calculate_statistics',
                    '추세': 'analyze_trend',
                    '위험도': 'assess_risk',
                    '비교': 'compare_periods',
                    '많은': 'find_top_cameras',
                }
            },
            'report_generation': {
                'keywords': {
                    '조치': 'generate_action_plan',
                    '대응': 'generate_action_plan',
                    '방안': 'generate_action_plan',
                    '어떻게': 'generate_action_plan',  # "어떻게 해야" 패턴
                    '일일': 'generate_daily_report',
                    '주간': 'generate_weekly_report',
                    '사고': 'generate_incident_report',
                    '요약': 'generate_summary',
                    '보고서': 'generate_event_report',
                }
            },
            'knowledge_management': {
                'keywords': {
                    '검색': 'search_knowledge',
                    '법규': 'search_regulations',
                    '규정': 'search_regulations',
                    '찾아': 'search_knowledge',
                    '알려': 'answer_question',
                }
            },
            'vision_analysis': {
                'keywords': {
                    '분석': 'analyze_image',
                    'PPE': 'detect_ppe',
                    '착용': 'detect_ppe',
                    '비교': 'compare_images',
                }
            }
        }
        
        # 키워드 매칭으로 task 결정
        if skill_name in task_mapping:
            for keyword, task in task_mapping[skill_name]['keywords'].items():
                if keyword in user_input:
                    return task
        
        # 기본 task (각 Skill의 첫 번째 기능)
        default_tasks = {
            'data_analytics': 'calculate_statistics',
            'report_generation': 'generate_action_plan',  # 기본값을 action_plan으로
            'knowledge_management': 'search_knowledge',
            'vision_analysis': 'analyze_image'
        }
        
        return default_tasks.get(skill_name, 'execute')

    def execute(self, user_input: str, image_data: Optional[Dict] = None) -> str:
        """
        사용자 요청 실행
        
        Args:
            user_input: 사용자 입력
            image_data: 이미지 데이터 (선택)
            
        Returns:
            최종 응답
        """
        print(f"\n{'=' * 60}")
        print(f"사용자 요청: {user_input}")
        print(f"{'=' * 60}")

        try:
            # 1단계: 빠른 라우팅 시도
            skill_name = self.quick_route(user_input)
            
            if not skill_name:
                # 2단계: LLM 라우팅
                print("[LLM 라우팅 시작]")
                routing_plan = self.llm_route(user_input)
                print(f"[라우팅 계획]\n{json.dumps(routing_plan, ensure_ascii=False, indent=2)}")
                
                # 멀티스텝 확인
                if routing_plan.get("multi_step"):
                    return self._execute_multi_step(routing_plan, user_input)
                
                skill_name = routing_plan.get("skill")
                task_description = routing_plan.get("task", user_input)
            else:
                task_description = user_input
            
            # 3단계: Skill 실행
            return self._execute_skill(skill_name, task_description, user_input, image_data)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"요청 처리 중 오류가 발생했습니다: {str(e)}"

    def _execute_skill(
        self, 
        skill_name: str, 
        task_description: str,
        original_input: str,
        image_data: Optional[Dict] = None
    ) -> str:
        """단일 Skill 실행"""
        
        print(f"\n[실행] {skill_name} Skill")
        print(f"{'=' * 60}")

        try:
            # task 결정
            task = self._determine_task(original_input, skill_name)
            
            # context 준비
            context = {
                'query': original_input,
                'task_description': task_description
            }
            
            # task별 필수 데이터 추가
            if skill_name == 'report_generation':
                if task == 'generate_action_plan':
                    # 사용자 질문에서 이벤트 타입 추출
                    event_type = self._extract_event_type(original_input)
                    context['event_data'] = {
                        'event_type': event_type,
                        'description': original_input,
                        'severity': 'MEDIUM',  # 기본값
                        'timestamp': 'N/A'
                    }
                    # 지식 베이스 컨텍스트 추가 (선택)
                    context['knowledge_context'] = f"사용자 질문: {original_input}"
                
                elif task == 'generate_event_report':
                    # 이벤트 데이터가 없으면 빈 리스트
                    context['events'] = context.get('events', [])
                
                elif task == 'generate_statistics_report':
                    # 통계 데이터가 없으면 빈 dict
                    context['statistics'] = context.get('statistics', {})
            
            # 이미지 데이터 추가
            if image_data:
                context['images'] = image_data.get('images', [])
            
            # Skill 실행
            result = self.skill_manager.execute_skill(
                skill_name=skill_name,
                task=task,
                context=context
            )
            
            # 결과 포맷팅
            if isinstance(result, dict):
                # dict 결과를 문자열로 변환
                return self._format_result(result, skill_name, task)
            else:
                return str(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"{skill_name} Skill 실행 중 오류: {str(e)}"
    
    def _extract_event_type(self, user_input: str) -> str:
        """사용자 입력에서 이벤트 타입 추출"""
        
        # 키워드 매핑
        event_keywords = {
            'NO_HELMET': ['헬멧', '안전모', '모자'],
            'NO_SAFETY_VEST': ['조끼', '안전조끼', '형광조끼'],
            'FALL_DETECTED': ['낙상', '넘어짐', '떨어짐', '추락'],
            'FIRE_HAZARD': ['화재', '불', '연기'],
            'RESTRICTED_AREA': ['제한구역', '출입금지', '통제구역'],
            'EQUIPMENT_MISUSE': ['장비', '도구', '기계']
        }
        
        for event_type, keywords in event_keywords.items():
            if any(kw in user_input for kw in keywords):
                return event_type
        
        return 'UNKNOWN'  # 기본값

    def _format_result(self, result: Dict, skill_name: str, task: str) -> str:
        """Skill 결과를 사용자 친화적인 형식으로 변환"""
        
        # report_generation 결과
        if 'report' in result:
            return result['report']
        
        if 'action_plan' in result:
            return result['action_plan']
        
        if 'summary' in result:
            return result['summary']
        
        # knowledge_management 결과
        if 'answer' in result:
            return result['answer']
        
        if 'results' in result:
            results = result['results']
            if isinstance(results, list) and len(results) > 0:
                # 첫 번째 결과의 content만 반환 (가장 관련성 높음)
                first_result = results[0]
                if isinstance(first_result, dict):
                    content = first_result.get('content', '')
                    # metadata 제거하고 content만 반환
                    return content
                else:
                    # Document 객체인 경우
                    return first_result.page_content if hasattr(first_result, 'page_content') else str(first_result)
        
        # guide 결과 (get_action_guide)
        if 'guide' in result:
            return result['guide']
        
        # data_analytics 결과
        if 'statistics' in result:
            stats = result['statistics']
            return f"""
📊 통계 분석 결과

기간: {stats.get('period', {}).get('start_date', 'N/A')} ~ {stats.get('period', {}).get('end_date', 'N/A')}

총 이벤트: {stats.get('total_events', 0)}건
- 해결: {stats.get('resolved', 0)}건
- 미해결: {stats.get('unresolved', 0)}건
- 해결률: {stats.get('resolution_rate', 0)}%

이벤트 타입별:
{self._format_dict(stats.get('by_event_type', {}))}

심각도별:
{self._format_dict(stats.get('by_severity', {}))}
"""
        
        # 기본: JSON 출력
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _format_dict(self, d: Dict) -> str:
        """딕셔너리를 보기 좋게 포맷팅"""
        return "\n".join([f"  - {k}: {v}건" for k, v in d.items()])

    def _execute_multi_step(self, routing_plan: dict, original_input: str) -> str:
        """멀티스텝 실행"""
        
        print(f"\n[멀티스텝 실행]")

        steps = routing_plan.get("steps", [])
        results = []
        context = ""

        for i, step in enumerate(steps, 1):
            skill_name = step.get("skill")
            task_description = step.get("task", original_input)

            print(f"\n[Step {i}/{len(steps)}] {skill_name} - {task_description}")
            print(f"{'-' * 60}")

            # 이전 단계의 결과를 컨텍스트로 추가
            if context:
                task_description = f"{task_description}\n\n이전 단계 결과:\n{context}"

            # Skill 실행
            result = self._execute_skill(skill_name, task_description, original_input)
            results.append({
                "step": i,
                "skill": skill_name,
                "task": task_description,
                "result": result
            })

            context = result
            print(f"\n[Step {i} 결과]\n{result[:200]}...")

        # 마지막 결과 반환
        return results[-1]["result"] if results else "결과가 없습니다."


def main():
    """테스트용 메인 함수"""
    print("=" * 60)
    print("Supervisor Agent V2 테스트 (Skills 기반)")
    print("=" * 60)

    supervisor = SupervisorAgentV2()

    test_queries = [
        # 지식 검색
        "안전모를 착용하지 않으면 어떻게 되나요?",

        # 데이터 분석
        "최근 7일간 통계를 보여주세요",

        # 보고서 생성
        "오늘 일일 보고서를 작성해주세요",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'#' * 60}")
        print(f"테스트 {i}")
        print(f"{'#' * 60}")

        response = supervisor.execute(query)

        print(f"\n{'=' * 60}")
        print(f"[최종 응답]")
        print(f"{'=' * 60}")
        print(response)
        print(f"\n{'=' * 60}\n")

    print("\n✅ Supervisor Agent V2 테스트 완료")


if __name__ == "__main__":
    main()
