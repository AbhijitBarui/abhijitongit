import os
import json
from pathlib import Path
import fitz  # PyMuPDF

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# === Config ===
embedding_model = OllamaEmbeddings(model="nomic-embed-text")
FAISS_DB_PATH = "faiss_db"
TEXT_JSON_FILE = "text_data.json"
PDF_FOLDER = "pdf_docs"

# === Load JSON chunks ===
def load_json_documents(json_path: str) -> list[Document]:
    documents = []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data:
        content = entry.get("description") or entry.get("content") or entry.get("details")
        if content:
            documents.append(Document(page_content=content, metadata={"source": "text_data.json"}))
    return documents

# === Load PDFs ===
def extract_documents_from_pdfs(folder_path: str) -> list[Document]:
    documents = []
    for pdf_file in Path(folder_path).glob("*.pdf"):
        with fitz.open(pdf_file) as pdf:
            for i, page in enumerate(pdf):
                text = page.get_text()
                if text.strip():
                    documents.append(Document(
                        page_content=text,
                        metadata={"source": f"{pdf_file.name} - page {i+1}"}
                    ))
    return documents

# === Build FAISS Vector DB ===
def build_combined_faiss_db():
    text_docs = load_json_documents(TEXT_JSON_FILE)
    pdf_docs = extract_documents_from_pdfs(PDF_FOLDER)
    all_docs = text_docs + pdf_docs
    print(f"Loaded {len(all_docs)} total chunks ({len(text_docs)} text, {len(pdf_docs)} from PDFs)")

    vector_db = FAISS.from_documents(all_docs, embedding_model)
    vector_db.save_local(FAISS_DB_PATH)
    print(f"✅ Combined FAISS DB saved at: {FAISS_DB_PATH}")

if __name__ == "__main__":
    build_combined_faiss_db()
