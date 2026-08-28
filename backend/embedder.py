import chromadb
from chromadb.utils import embedding_functions
from chunker import ChunkData
import os
from dotenv import load_dotenv
load_dotenv()

# Initialise ChromaDB client
chroma_client = chromadb.Client()

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

    # Prepare data for ChromaDB
    ids = [str(chunk.chunk_index) for chunk in chunks]
    documents = [chunk.text for chunk in chunks]
    metadatas = [
        {
            "section_number": chunk.section_number,
            "section_name": chunk.section_name,
            "parent_section": chunk.parent_section
        }
        for chunk in chunks
    ]

    # Store in ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Stored {len(chunks)} chunks in ChormaDB")

def query(question: str, arxiv_id: str, n_results: int = 5):
    collection = get_collection(arxiv_id)

    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )

    return results

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
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        section = f"{meta['section_number']} {meta['section_name']}".strip()
        parent = f" (under {meta['parent_section']})" if meta['parent_section'] else ""
        print(f"\n--- Result {i+1}: {section}{parent} ---")
        print(doc[:300])