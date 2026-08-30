import os
from dotenv import load_dotenv
from embedder import query, get_abstract
from openai import OpenAI
from embedder import QueryResult
import json

load_dotenv()

client = OpenAI()

SYSTEM_PROMPT = """You are a research assistant that answers questions about academic papers.

Rules:
- Answer ONLY from the provided context chunks
- If the answer is not in the context, set found to false
- Always cite the section your answer comes from
- Quote the exact passage that supports your answer
- Be precise and concise
- Pay attention to whether the context is describing the paper's own model or other models being compared

Always respond in this JSON format:
{
    "found": true or false,
    "answer": "your answer here",
    "quote": "exact passage from context",
    "section": "section name"
}"""

def build_context(results: QueryResult) -> str:
    """Format retreived chunks into a context string for the LLM"""
    context_parts = []

    for chunk in results.chunks:
        context_parts.append(f"[Section: {chunk.format_section()}]\n{chunk.text}")
    return "\n\n---\n\n".join(context_parts)

def build_confidence(results: QueryResult) -> str:
    if not results.chunks:
        return "unknown"
    avg_distance = sum(c.distance for c in results.chunks) / len(results.chunks)
    if avg_distance < 0.5:
        # return f"{avg_distance} high"
        return f"high"
    elif avg_distance < 0.8:
        # return f"{avg_distance} medium"
        return f"medium"
    else:
        # return f"{avg_distance} low"
        return f"low"

def answer(question: str, arxiv_id: str) -> dict:
    results = query(question, arxiv_id, n_results=5)

    # Always include abstract in context
    abstract_chunks = get_abstract(arxiv_id)
    existing_text =  {c.text for c in results.chunks}
    for chunk in abstract_chunks:
        if chunk.text not in existing_text:
            results.chunks.insert(0, chunk)

    # debug
    print("\nRetrieved chunks:")
    for chunk in results.chunks:
        print(f"  {chunk.format_section()} | distance: {chunk.distance:.3f}")

    if not results.chunks:
        return {
            "answer": "I couldn't find any relevant content in this paper.",
            "source": None,
            "confidence": "low"
        }

    context = build_context(results)
    confidence = build_confidence(results)

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Context from the paper:

{context}

Question: {question}"""
            }
        ]
    )

    try:
        answer_text = response.choices[0].message.content
        # print(f"Type: {type(answer_text)}")
        # print(f"Length: {len(answer_text) if answer_text else 'None'}")
        # print(repr(answer_text[:100]) if answer_text else "EMPTY")
        # print(answer_text, "<< raw response")
        start = answer_text.index("{")
        end = answer_text.rindex("}") + 1
        parsed = json.loads(answer_text[start:end])
        # parsed = json.loads(answer_text)
        # print(parsed, "<<< parsed")
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")  # add this
        return {
            "answer": "Failed to parse response.",
            "source": None,
            "confidence": "low"
        }

    if not parsed.get("found"):
        return {
            "answer": "I can't find this in the paper.",
            "source": None,
            "confidence": "low"
        }

    return {
        "answer": parsed["answer"],
        "source": {
            "section": parsed["section"],
            "passage": parsed["quote"]
        },
        "confidence": confidence
    }

if __name__ == "__main__":
    from paper import fetch_paper
    from chunker import chunk_sections
    from embedder import embed_chunks

    url = "https://arxiv.org/abs/1706.03762"
    metadata, sections, arxiv_id = fetch_paper(url)
    chunks = chunk_sections(sections)
    embed_chunks(chunks, arxiv_id)

    # Test questions
    questions = [
        "How does the attention mechanism work?",
        "What datasets were used for training?",
        "What are the limitations of this model?",
        "What is the meaning of life?",  # should get "I can't find this"
        "What's the paper about?"
    ]

    for question in questions:
        print(f"\nQ: {question}")
        result = answer(question, arxiv_id)
        print(f"Confidence: {result['confidence']}")
        print(f"A: {result['answer'][:500]}")
        if result['source']:
            print(f"Source: {result['source']['section']}")
            print(f"Quote: {result['source']['passage'][:200]}")