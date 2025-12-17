import os, glob
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader

EXCLUDE_SUBSTRINGS = [
    ".git/", "node_modules/", "dist/", "build/", "__pycache__/", ".venv/",
    "app/data/.rag/", ".env", "/.ipynb_checkpoints/"
]

# Consiglio: docs-only per evitare hit sul codice
INCLUDE_GLOBS = [
    "docs/**/*.md",
    "docs/**/*.txt",
    "docs/**/*.pdf",
]

def _load_text_file(path: str, repo_root: str) -> list[Document]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()
    if not text:
        return []
    rel = os.path.relpath(path, repo_root).replace("\\", "/")
    return [Document(page_content=text, metadata={"source": rel})]

def _load_pdf_file(path: str, repo_root: str) -> list[Document]:
    loader = PyPDFLoader(path)
    pages = loader.load()  # 1 Document per pagina
    rel = os.path.relpath(path, repo_root).replace("\\", "/")

    out: list[Document] = []
    for d in pages:
        page = d.metadata.get("page")
        src = f"{rel}#page={page}" if page is not None else rel
        d.metadata["source"] = src
        out.append(d)
    return out

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

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                docs.extend(_load_pdf_file(path, repo_root))
            else:
                docs.extend(_load_text_file(path, repo_root))
        except Exception:
            continue

    return docs

def build_vectorstore(repo_root: str, persist_dir: str, collection_name: str) -> None:
    docs = load_repo_docs(repo_root)
    print(f"📄 Documenti caricati (incl. pagine PDF): {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"✂️  Chunk generati: {len(chunks)}")

    os.makedirs(persist_dir, exist_ok=True)

    # Persistenza automatica (NO vs.persist())
    Chroma.from_documents(
        chunks,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=persist_dir,
        collection_name=collection_name,
        collection_metadata={"hnsw:space": "cosine"},
    )

if __name__ == "__main__":
    repo_root = os.getenv("RAG_REPO_ROOT", ".")
    persist_dir = os.getenv("RAG_PERSIST_DIR", "./app/data/.rag/chroma")
    collection = os.getenv("RAG_COLLECTION_NAME", "internal_repo")

    build_vectorstore(repo_root, persist_dir, collection)
    print(f"✅ Indicizzazione completata: {persist_dir} (collection={collection})")
