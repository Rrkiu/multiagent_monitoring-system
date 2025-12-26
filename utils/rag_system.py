"""
RAG (Retrieval-Augmented Generation) 시스템
지식 베이스 문서를 벡터화하고 검색하는 기능 제공
"""

from pathlib import Path
from typing import List, Optional
import logging

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

from config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """RAG 시스템 클래스"""

    def __init__(
            self,
            knowledge_base_dir: str = None,
            persist_dir: str = None,
            embedding_model: str = None,
            chunk_size: int = 500,
            chunk_overlap: int = 50
    ):
        """
        RAG 시스템 초기화

        Args:
            knowledge_base_dir: 지식 베이스 디렉토리 경로
            persist_dir: ChromaDB 저장 경로
            embedding_model: 임베딩 모델 이름
            chunk_size: 문서 청크 크기
            chunk_overlap: 청크 간 오버랩 크기
        """
        self.knowledge_base_dir = knowledge_base_dir or settings.knowledge_base_dir
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 임베딩 모델 초기화
        logger.info(f"임베딩 모델 로드 중: {self.embedding_model_name}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # 벡터 스토어 초기화
        self.vectorstore = None

    def load_documents(self) -> List[Document]:
        """지식 베이스에서 문서 로드"""
        logger.info(f"문서 로드 중: {self.knowledge_base_dir}")

        # DirectoryLoader로 마크다운 파일 로드
        loader = DirectoryLoader(
            self.knowledge_base_dir,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )

        documents = loader.load()
        logger.info(f"총 {len(documents)}개의 문서 로드 완료")

        # 각 문서에 메타데이터 추가
        for doc in documents:
            # 파일명에서 이벤트 타입 추출
            filename = Path(doc.metadata['source']).stem
            doc.metadata['event_type'] = filename
            doc.metadata['source_file'] = Path(doc.metadata['source']).name

        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """문서를 청크로 분할"""
        logger.info(f"문서 분할 중 (chunk_size={self.chunk_size}, overlap={self.chunk_overlap})")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )

        chunks = text_splitter.split_documents(documents)
        logger.info(f"총 {len(chunks)}개의 청크 생성 완료")

        return chunks

    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """벡터 스토어 생성 및 저장"""
        logger.info("벡터 스토어 생성 중...")

        # 기존 디렉토리가 있으면 삭제
        persist_path = Path(self.persist_dir)
        if persist_path.exists():
            import shutil
            shutil.rmtree(persist_path)
            logger.info(f"기존 벡터 스토어 삭제: {self.persist_dir}")

        # ChromaDB 생성
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_dir
        )

        logger.info(f"벡터 스토어 저장 완료: {self.persist_dir}")

        return vectorstore

    def load_vectorstore(self) -> Chroma:
        """기존 벡터 스토어 로드"""
        logger.info(f"벡터 스토어 로드 중: {self.persist_dir}")

        vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings
        )

        logger.info("벡터 스토어 로드 완료")

        return vectorstore

    def initialize(self, force_rebuild: bool = False):
        """RAG 시스템 초기화"""
        persist_path = Path(self.persist_dir)

        # 벡터 스토어가 이미 존재하고 rebuild가 아니면 로드
        if persist_path.exists() and not force_rebuild:
            logger.info("기존 벡터 스토어 사용")
            self.vectorstore = self.load_vectorstore()
        else:
            logger.info("새로운 벡터 스토어 생성")
            # 문서 로드
            documents = self.load_documents()

            # 문서 분할
            chunks = self.split_documents(documents)

            # 벡터 스토어 생성
            self.vectorstore = self.create_vectorstore(chunks)

        logger.info("RAG 시스템 초기화 완료")

    def search(
            self,
            query: str,
            k: int = 3,
            filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """
        유사도 기반 문서 검색

        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter_dict: 메타데이터 필터 (예: {"event_type": "NO_HELMET"})

        Returns:
            검색된 문서 리스트
        """
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")

        if filter_dict:
            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = self.vectorstore.similarity_search(query, k=k)

        return results

    def search_by_event_type(self, event_type: str, k: int = 3) -> List[Document]:
        """
        특정 이벤트 타입에 대한 문서 검색

        Args:
            event_type: 이벤트 타입 (예: "NO_HELMET")
            k: 반환할 문서 수

        Returns:
            검색된 문서 리스트
        """
        return self.search(
            query=event_type,
            k=k,
            filter_dict={"event_type": event_type}
        )

    def get_action_guide(self, event_type: str) -> str:
        """
        특정 이벤트 타입에 대한 조치 가이드 반환

        Args:
            event_type: 이벤트 타입

        Returns:
            조치 가이드 텍스트
        """
        docs = self.search_by_event_type(event_type, k=1)

        if not docs:
            return f"{event_type}에 대한 조치 가이드를 찾을 수 없습니다."

        return docs[0].page_content


def main():
    """테스트용 메인 함수"""
    print("=" * 60)
    print("RAG 시스템 테스트")
    print("=" * 60)

    # RAG 시스템 초기화
    rag = RAGSystem()
    rag.initialize(force_rebuild=True)

    print("\n" + "=" * 60)
    print("검색 테스트")
    print("=" * 60)

    # 테스트 쿼리
    test_queries = [
        "안전모를 착용하지 않았을 때 어떻게 해야 하나요?",
        "작업자가 넘어졌을 때 조치 방법",
        "화재 위험이 발견되면 어떻게 대응하나요?",
    ]

    for query in test_queries:
        print(f"\n질문: {query}")
        print("-" * 60)

        results = rag.search(query, k=2)

        for i, doc in enumerate(results, 1):
            print(f"\n[결과 {i}]")
            print(f"이벤트 타입: {doc.metadata.get('event_type', 'N/A')}")
            print(f"출처: {doc.metadata.get('source_file', 'N/A')}")
            print(f"내용 미리보기:\n{doc.page_content[:200]}...")

    print("\n" + "=" * 60)
    print("이벤트 타입별 검색 테스트")
    print("=" * 60)

    event_types = ["NO_HELMET", "FALL_DETECTED", "FIRE_HAZARD"]

    for event_type in event_types:
        print(f"\n이벤트 타입: {event_type}")
        print("-" * 60)

        guide = rag.get_action_guide(event_type)
        print(guide[:300] + "...")

    print("\n" + "=" * 60)
    print("✅ RAG 시스템 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()