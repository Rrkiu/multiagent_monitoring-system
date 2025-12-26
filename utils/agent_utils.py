"""
Agent 유틸리티 함수
"""


def create_parsing_error_handler():
    """파싱 에러 핸들러 생성"""
    def handle_error(error):
        error_msg = str(error)
        if "validation error" in error_msg.lower():
            return (
                "도구 입력 형식이 올바르지 않습니다. "
                "다음을 확인하세요:\n"
                "1. JSON 형식이 올바른가? (큰따옴표 사용)\n"
                "2. 모든 필수 파라미터가 포함되었는가?\n"
                "3. 파라미터 이름이 정확한가?\n"
                '예시: {"start_date": "2025-11-15", "end_date": "2025-11-22"}'
            )
        elif "field required" in error_msg.lower():
            import re
            # 누락된 필드 추출
            match = re.search(r"field required.*?(\w+)", error_msg)
            if match:
                field = match.group(1)
                return f"필수 파라미터 '{field}'가 누락되었습니다. 모든 필수 파라미터를 포함하여 다시 시도하세요."
            return "필수 파라미터가 누락되었습니다. 도구 설명을 다시 확인하세요."
        return f"오류: {error_msg}"

    return handle_error


def get_react_prompt_template(role_description: str, guidelines: list, additional_notes: str = "") -> str:
    """
    ReAct 프롬프트 템플릿 생성

    Args:
        role_description: 에이전트 역할 설명
        guidelines: 지침 리스트
        additional_notes: 추가 노트

    Returns:
        프롬프트 템플릿 문자열
    """
    guidelines_text = "\n".join(f"{i}. {g}" for i, g in enumerate(guidelines, 1))

    # JSON 예시를 작은따옴표로 감싸서 중괄호가 변수로 인식되지 않도록 함
    template = f"""당신은 안전 모니터링 시스템의 {role_description}입니다.

역할 및 지침:
{guidelines_text}

{additional_notes}

중요: Action Input은 반드시 유효한 JSON 형식이어야 합니다.
- 큰따옴표를 사용하세요
- 모든 필수 파라미터를 포함하세요

사용 가능한 도구들:
{{tools}}

도구 이름들: {{tool_names}}

다음 형식을 정확히 따르세요:

Question: 답변해야 할 입력 질문
Thought: 무엇을 해야 할지 생각합니다
Action: 수행할 작업 (도구 이름만 작성)
Action Input: 도구에 전달할 파라미터 (JSON 형식)
Observation: 작업의 결과
... (필요시 Thought/Action/Action Input/Observation 반복)
Thought: 이제 최종 답변을 알았습니다
Final Answer: 원래 입력 질문에 대한 최종 답변

시작하세요!

Question: {{input}}
Thought: {{agent_scratchpad}}"""

    return template