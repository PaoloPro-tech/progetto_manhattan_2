import os, glob
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

EXCLUDE_SUBSTRINGS = [
    ".git/", "node_modules/", "dist/", "build/", "__pycache__/", ".venv/",
    "app/data/.rag/", ".env"
]

INCLUDE_GLOBS = [
    "**/*.md", "**/*.txt",
    "app/**/*.py",
    "**/*.yaml", "**/*.yml", "**/*.json"
]

def load_repo_docs(repo_root: str) -> list[Document]:
    files: list[str] = []
    for pattern in INCLUDE_GLOBS:
        files += glob.glob(os.path.join(repo_root, pattern), recursive=True)

    docs: list[Document] = []
    for path in sorted(set(files)):
        norm = path.replace("\\", "/")
        if any(x in norm for x in EXCLUDE_SUBSTRINGS):
            continue
        if os.path.isdir(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
            if not text:
                continue
            rel = os.path.relpath(path, repo_root).replace("\\", "/")
            docs.append(Document(page_content=text, metadata={"source": rel}))
        except Exception:
            continue
    return docs

def build_vectorstore(repo_root: str, persist_dir: str, collection_name: str) -> None:
    docs = load_repo_docs(repo_root)
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    os.makedirs(persist_dir, exist_ok=True)

vs = Chroma.from_documents(
    chunks,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    persist_directory=persist_dir,
    collection_name=collection_name,
    collection_metadata={"hnsw:space": "cosine"},
)
    vs.persist()

if __name__ == "__main__":
    repo_root = os.getenv("RAG_REPO_ROOT", ".")
    persist_dir = os.getenv("RAG_PERSIST_DIR", "./app/data/.rag/chroma")
    collection = os.getenv("RAG_COLLECTION_NAME", "internal_repo")

    build_vectorstore(repo_root, persist_dir, collection)
    print(f"✅ Indicizzazione completata: {persist_dir} (collection={collection})")
