import chromadb
from chromadb.utils import embedding_functions
from chunker import ChunkData
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

class ChunkMetadata(BaseModel):
    section_number: str
    section_name: str
    parent_section: str

class ChunkResult(BaseModel):
    text: str
    section_number: str
    section_name: str
    parent_section: str
    distance: float

    def format_section(self) -> str:
        section = f"{self.section_number} {self.section_name}".strip()
        parent = f" (under {self.parent_section})" if self.parent_section else ""
        return f"{section}{parent}"

class QueryResult(BaseModel):
    chunks: list[ChunkResult]

# Initialise ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# OpenAI embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPEN_API_KEY"),
    model_name="text-embedding-3-small"
)

def get_collection(arxiv_id: str):
    return chroma_client.get_or_create_collection(
        name=f"paper_{arxiv_id.replace('.', '_')}",
        embedding_function=openai_ef
    )

def embed_chunks(chunks: list[ChunkData], arxiv_id: str) -> None:
    collection = get_collection(arxiv_id)

    if collection.count() > 0:
        print(f"Paper already embedded, skipping. ({collection.count()} chunks)")
        return

    # Prepare data for ChromaDB
    ids = [str(chunk.chunk_index) for chunk in chunks]
    documents = [chunk.text for chunk in chunks]
    metadatas = [
        ChunkMetadata(
            section_number=chunk.section_number,
            section_name=chunk.section_name,
            parent_section=chunk.parent_section
        ).model_dump()
        for chunk in chunks
    ]

    # Store in ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Stored {len(chunks)} chunks in ChormaDB")

def query(question: str, arxiv_id: str, n_results: int = 5) -> QueryResult:
    collection = get_collection(arxiv_id)

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        typed_meta = ChunkMetadata(**meta) # converts dict back to Pydantic
        chunks.append(ChunkResult(
            text=doc,
            section_number=typed_meta.section_number,
            section_name=typed_meta.section_name,
            parent_section=typed_meta.parent_section,
            distance=distance
        ))

    return QueryResult(chunks=chunks)

def get_abstract(arxiv_id: str) -> ChunkResult | None:
    collection = get_collection(arxiv_id)
    results = collection.get(
        where={"section_name": "Abstract"}
    )

    if not results["documents"]:
        return []

    chunks = []
    for doc, meta in zip(results["documents"], results["metadatas"]):
        typed_meta = ChunkMetadata(**meta)
        chunks.append(ChunkResult(
            text=doc,
            section_number=typed_meta.section_number,
            section_name=typed_meta.section_name,
            parent_section=typed_meta.parent_section,
            distance=-1.0 # sentinel: no distance available
        ))

    return chunks

if __name__ == "__main__":
    from paper import fetch_paper
    from chunker import chunk_sections

    url = "https://arxiv.org/abs/1706.03762"
    metadata, sections, arxiv_id = fetch_paper(url)
    chunks = chunk_sections(sections)

    # Store chunks
    embed_chunks(chunks, arxiv_id)

    # Test query
    question = "How does the attention mechanism work?"
    print(f"\nQuerying: {question}")
    results = query(question, arxiv_id)

    print("\nTop results:")
    for i, chunk in enumerate(results.chunks):
        print(f"\n--- Result {i+1}: {chunk.format_section()} ---")
        print(chunk.text[:300])