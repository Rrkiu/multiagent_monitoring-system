"""
Knowledge Management Skill
RAG 기반 지식 관리 및 검색
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document
from config import settings
from skills.base_skill import BaseSkill, SkillMetadata
from utils.rag_system import RAGSystem


class KnowledgeManagementSkill(BaseSkill):
    """
    RAG 기반 지식 관리 Skill
    
    기능:
    - 지식 베이스 검색
    - 이벤트별 조치 가이드 조회
    - 안전 규정 검색
    - 문서 임베딩 및 저장
    - 시맨틱 검색
    """
    
    def _load_metadata(self) -> SkillMetadata:
        """메타데이터 로드"""
        return SkillMetadata(
            name="knowledge_management",
            description="RAG 기반 지식 관리 및 검색",
            version="1.0.0",
            author="Safety Team",
            dependencies=[
                "langchain",
                "langchain-community",
                "chromadb",
                "sentence-transformers"
            ],
            tags=["knowledge", "rag", "search", "embedding", "vector"]
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
        
        # RAG 시스템 초기화
        rag_system = RAGSystem(
            knowledge_base_dir=config.get('knowledge_base_dir', settings.knowledge_base_dir),
            persist_dir=config.get('persist_dir', settings.chroma_persist_dir),
            embedding_model=config.get('embedding_model', settings.embedding_model),
            chunk_size=config.get('chunk_size', 500),
            chunk_overlap=config.get('chunk_overlap', 50)
        )
        
        # RAG 시스템 초기화 (기존 벡터 스토어 사용)
        try:
            rag_system.initialize(force_rebuild=False)
        except Exception as e:
            print(f"[Warning] RAG 시스템 초기화 실패: {e}")
            print("[Info] 지식 베이스가 없거나 초기화되지 않았습니다.")
        
        return {
            'llm': llm,
            'rag_system': rag_system,
            'knowledge_searcher': self._create_knowledge_searcher(rag_system),
            'action_guide_retriever': self._create_action_guide_retriever(rag_system),
            'regulation_searcher': self._create_regulation_searcher(rag_system)
        }
    
    def _create_knowledge_searcher(self, rag_system: RAGSystem):
        """지식 검색 도구 생성"""
        def search(query: str, k: int = 3, filter_dict: Optional[Dict] = None) -> List[Document]:
            """지식 베이스 검색"""
            try:
                results = rag_system.search(query, k=k, filter_dict=filter_dict)
                return results
            except Exception as e:
                print(f"[Error] 지식 검색 실패: {e}")
                return []
        
        return search
    
    def _create_action_guide_retriever(self, rag_system: RAGSystem):
        """조치 가이드 검색 도구 생성"""
        def retrieve(event_type: str) -> str:
            """이벤트 타입별 조치 가이드 조회"""
            try:
                guide = rag_system.get_action_guide(event_type)
                return guide
            except Exception as e:
                print(f"[Error] 조치 가이드 조회 실패: {e}")
                return f"{event_type}에 대한 조치 가이드를 찾을 수 없습니다."
        
        return retrieve
    
    def _create_regulation_searcher(self, rag_system: RAGSystem):
        """안전 규정 검색 도구 생성"""
        def search(query: str, k: int = 2) -> List[Document]:
            """안전 규정 검색"""
            try:
                results = rag_system.search(query, k=k)
                # 법규 관련 내용만 필터링
                regulation_results = []
                for doc in results:
                    if "관련 법규" in doc.page_content or "법" in doc.page_content:
                        regulation_results.append(doc)
                return regulation_results
            except Exception as e:
                print(f"[Error] 안전 규정 검색 실패: {e}")
                return []
        
        return search
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Knowledge Management 실행
        
        Args:
            task: 수행할 작업
            context: 작업 컨텍스트
            
        Returns:
            작업 결과
        """
        if context is None:
            context = {}
        
        # Task 라우팅
        if task == "search_knowledge":
            return self._search_knowledge(context)
        elif task == "get_action_guide":
            return self._get_action_guide(context)
        elif task == "search_regulations":
            return self._search_regulations(context)
        elif task == "search_by_event_type":
            return self._search_by_event_type(context)
        elif task == "answer_question":
            return self._answer_question(context)
        elif task == "rebuild_vectorstore":
            return self._rebuild_vectorstore(context)
        else:
            raise ValueError(f"Unknown task: {task}")
    
    def _search_knowledge(self, context: Dict) -> Dict:
        """지식 베이스 검색"""
        query = context.get('query', '')
        k = context.get('k', 3)
        filter_dict = context.get('filter')
        
        if not query:
            return {"error": "query가 필요합니다."}
        
        results = self.tools['knowledge_searcher'](query, k, filter_dict)
        
        if not results:
            return {
                "query": query,
                "results": [],
                "message": "관련 정보를 찾을 수 없습니다."
            }
        
        # 결과를 딕셔너리로 변환
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "event_type": doc.metadata.get('event_type', 'N/A'),
                "source_file": doc.metadata.get('source_file', 'N/A')
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
    
    def _get_action_guide(self, context: Dict) -> Dict:
        """조치 가이드 조회"""
        event_type = context.get('event_type', '')
        
        if not event_type:
            return {"error": "event_type이 필요합니다."}
        
        guide = self.tools['action_guide_retriever'](event_type)
        
        return {
            "event_type": event_type,
            "guide": guide
        }
    
    def _search_regulations(self, context: Dict) -> Dict:
        """안전 규정 검색"""
        query = context.get('query', '')
        k = context.get('k', 2)
        
        if not query:
            return {"error": "query가 필요합니다."}
        
        results = self.tools['regulation_searcher'](query, k)
        
        if not results:
            return {
                "query": query,
                "regulations": [],
                "message": "관련 안전 규정을 찾을 수 없습니다."
            }
        
        # 결과 포맷팅
        regulations = []
        for doc in results:
            regulations.append({
                "content": doc.page_content,
                "event_type": doc.metadata.get('event_type', 'N/A')
            })
        
        return {
            "query": query,
            "regulations": regulations,
            "total_results": len(regulations)
        }
    
    def _search_by_event_type(self, context: Dict) -> Dict:
        """이벤트 타입별 검색"""
        event_type = context.get('event_type', '')
        k = context.get('k', 3)
        
        if not event_type:
            return {"error": "event_type이 필요합니다."}
        
        # 이벤트 타입으로 필터링하여 검색
        results = self.tools['knowledge_searcher'](
            event_type, 
            k, 
            filter_dict={"event_type": event_type}
        )
        
        if not results:
            return {
                "event_type": event_type,
                "results": [],
                "message": f"{event_type}에 대한 정보를 찾을 수 없습니다."
            }
        
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return {
            "event_type": event_type,
            "results": formatted_results,
            "total_results": len(formatted_results)
        }
    
    def _answer_question(self, context: Dict) -> Dict:
        """질문에 대한 답변 생성 (RAG + LLM)"""
        question = context.get('question', '')
        k = context.get('k', 3)
        
        if not question:
            return {"error": "question이 필요합니다."}
        
        # 1. 관련 문서 검색
        search_results = self.tools['knowledge_searcher'](question, k)
        
        if not search_results:
            return {
                "question": question,
                "answer": "관련 정보를 찾을 수 없어 답변을 생성할 수 없습니다.",
                "sources": []
            }
        
        # 2. 검색된 문서를 컨텍스트로 사용하여 LLM에게 답변 요청
        context_text = "\n\n".join([
            f"[문서 {i+1}]\n{doc.page_content}" 
            for i, doc in enumerate(search_results)
        ])
        
        prompt = self.get_prompt('answer_generation')
        if not prompt:
            prompt = self._get_default_answer_prompt()
        
        prompt = prompt.format(
            context=context_text,
            question=question
        )
        
        try:
            response = self.tools['llm'].invoke(prompt)
            answer = response.content
        except Exception as e:
            answer = f"답변 생성 중 오류가 발생했습니다: {str(e)}"
        
        # 출처 정보
        sources = [
            {
                "event_type": doc.metadata.get('event_type', 'N/A'),
                "source_file": doc.metadata.get('source_file', 'N/A')
            }
            for doc in search_results
        ]
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "context_used": len(search_results)
        }
    
    def _rebuild_vectorstore(self, context: Dict) -> Dict:
        """벡터 스토어 재구축"""
        try:
            self.tools['rag_system'].initialize(force_rebuild=True)
            return {
                "success": True,
                "message": "벡터 스토어가 성공적으로 재구축되었습니다."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"벡터 스토어 재구축 실패: {str(e)}"
            }
    
    def get_capabilities(self) -> List[str]:
        """Skill 기능 목록"""
        return [
            "search_knowledge",
            "get_action_guide",
            "search_regulations",
            "search_by_event_type",
            "answer_question",
            "rebuild_vectorstore"
        ]
    
    def validate_input(self, task: str, context: Dict[str, Any]) -> bool:
        """입력 검증"""
        if task == "search_knowledge":
            return 'query' in context
        elif task == "get_action_guide" or task == "search_by_event_type":
            return 'event_type' in context
        elif task == "search_regulations":
            return 'query' in context
        elif task == "answer_question":
            return 'question' in context
        elif task == "rebuild_vectorstore":
            return True  # 파라미터 불필요
        return False
    
    # Helper methods
    
    def _get_default_answer_prompt(self) -> str:
        """기본 답변 생성 프롬프트"""
        return """당신은 안전 모니터링 시스템의 지식 관리 전문가입니다.

다음 문서들을 참고하여 사용자의 질문에 답변해주세요:

{context}

질문: {question}

답변 작성 지침:
1. 제공된 문서의 내용을 기반으로 답변하세요
2. 구체적이고 실용적인 정보를 제공하세요
3. 관련 법규나 규정이 있다면 언급하세요
4. 조치 방법이 있다면 단계별로 설명하세요
5. 문서에 없는 내용은 추측하지 마세요

답변:"""
