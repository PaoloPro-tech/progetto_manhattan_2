from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

class RAGService:
    def __init__(self, persist_dir: str, collection_name: str, top_k: int = 4):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.top_k = top_k
        self._vs = Chroma(
            persist_directory=persist_dir,
            embedding_function=OpenAIEmbeddings(),
            collection_name=collection_name
        )

    def retrieve(self, query: str):
        retriever = self._vs.as_retriever(search_kwargs={"k": self.top_k})
        return retriever.invoke(query)
