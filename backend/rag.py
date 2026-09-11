import os
from dotenv import load_dotenv
from embedder import query, get_abstract
from openai import OpenAI
from embedder import QueryResult
import json
from schemas_model import (AnswerResponse, SourceResponse, Citation)

load_dotenv()

client = OpenAI()

SYSTEM_PROMPT = """You are a research assistant that answers questions about academic papers.

Rules:
- Answer ONLY from the provided context chunks
- If the answer is not in the context, set found to false
- Synthesise information from multiple sections when relevant
- Cite ALL sections your answer draws from
- Only cite Abstract if no other section covers the question
- Be precise and concise

Respond in this exact JSON format with no markdown:
{
    "found": true or false,
    "answer": "your answer here",
    "citations": [
        {"quote": "exact passage", "section": "3.2.1 Scaled Dot-Product Attention"},
        {"quote": "another passage", "section": "3.2.2 Multi-Head Attention"}
    ]
}"""

REWRITE_QUERY_SYSTEM_PROMPT = """Generate 3 different versions of the given question to improve academic paper retrieval.
Use different vocabulary and phrasing but keep the same meaning.
Use keywords and terminology from the provided abstract to make the queries more specific to this paper.

Respond in this exact JSON format:
{
    "queries": ["version 1", "version 2", "version 3"]
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

def rewrite_query(question: str, abstract: str = "") -> list[str]:
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=200,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            { "role": "system", "content": REWRITE_QUERY_SYSTEM_PROMPT },
            { 
                "role": "user",
                "content": f"""Paper abstract:
{abstract}

Question to rewrite: {question}"""
            }, 
        ]
    )

    try:
        parsed = json.loads(response.choices[0].message.content)
        return [question] + parsed["queries"]
    except Exception:
        return [question]

def query_multi(question: str, arxiv_id: str, n_results: int = 5) -> QueryResult:
    # Get abstract text for query rewriting context
    abstract_chunks = get_abstract(arxiv_id)
    abstract_text = " ".join([c.text for c in abstract_chunks])

    queries = rewrite_query(question, abstract=abstract_text)
    print(f"Rewritten queries: {queries}")

    seen_texts = set()
    all_chunks = []

    for q in queries:
        results = query(q, arxiv_id, n_results=n_results)
        for chunk in results.chunks:
            if chunk.text not in seen_texts:
                seen_texts.add(chunk.text)
                all_chunks.append(chunk)

    all_chunks.sort(key=lambda c: c.distance)
    return QueryResult(chunks=all_chunks[:n_results])



def answer(question: str, arxiv_id: str, history: list[dict] = []) -> AnswerResponse:
    # results = query(question, arxiv_id, n_results=5)
    results = query_multi(question, arxiv_id, n_results=5)

    # Always include abstract in context
    abstract_chunks = get_abstract(arxiv_id)
    existing_text =  {c.text for c in results.chunks}
    for chunk in abstract_chunks:
        if chunk.text not in existing_text:
            results.chunks.append(chunk)

    # debug
    print("\nRetrieved chunks:")
    for chunk in results.chunks:
        print(f"  {chunk.format_section()} | distance: {chunk.distance:.3f}")

    if not results.chunks:
        return AnswerResponse(
            answer="I couldn't find any relevant content in this paper.",
            source=None,
            confidence="low"
        )
    
    context = build_context(results)
    confidence = build_confidence(results)

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1000,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *history, # inject conversation history
            {
                "role": "user",
                "content": f"""Context from the paper:

{context}

Question: {question}"""
            }
        ]
    )

    try:
        # TODO: make it as a type
        answer_text = response.choices[0].message.content
        parsed = json.loads(answer_text)
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

    return AnswerResponse(
        answer=parsed["answer"],
        source=SourceResponse(
            citations=[
                Citation(quote=c["quote"], section=c["section"])
                for c in parsed["citations"]
            ]
        ),
        confidence=confidence
    )

def generate_summary(arxiv_id: str) -> str:
    result = answer(
        "Summarise this paper as: one sentence TL;DR, the problem it solves, the approach, and the key findings.",
        arxiv_id
    )
    return result.answer

# TODO: user able to add the default question or instruction after upload and question answerd after each upload
def generate_suggested_questions(arxiv_id: str) -> list[str]:
    abstract_chunks = get_abstract(arxiv_id)
    abstract_text = " ".join([c.text for c in abstract_chunks])

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=300,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """Generate 4 interesting questions that can be answered from this paper.
Focus on methodology, results, and key contributions.
Respond in this exact JSON format:
{
    "questions": ["question 1", "question 2", "question 3", "question 4"]
}"""
            },
            {
                "role": "user",
                "content": f"Paper abstract: {abstract_text}"
            }
        ]
    )

    try:
        parsed = json.loads(response.choices[0].message.content)
        return parsed["questions"]
    except Exception:
        return []

if __name__ == "__main__":
    from paper import fetch_paper
    from chunker import chunk_sections
    from embedder import embed_chunks

    url = "https://arxiv.org/abs/1706.03762"
    metadata, sections, arxiv_id = fetch_paper(url)
    chunks = chunk_sections(sections)
    embed_chunks(chunks, arxiv_id)

    # # Test questions
    # questions = [
    #     "How does the attention mechanism work?",
    #     "What datasets were used for training?",
    #     "What are the limitations of this model?",
    #     "What is the meaning of life?",  # should get "I can't find this"
    #     "What's the paper about?"
    # ]

    # for question in questions:
    #     print(f"\nQ: {question}")
    #     result = answer(question, arxiv_id)
    #     print(f"Confidence: {result['confidence']}")
    #     print(f"A: {result['answer'][:500]}")
    #     if result['source']:
    #         print(f"Source: {result['source']['section']}")
    #         print(f"Quote: {result['source']['passage'][:200]}")


    print("\n--- Summary ---")
    summary = generate_summary(arxiv_id)
    print(summary)

    print("\n--- Suggested Questions ---")
    questions = generate_suggested_questions(arxiv_id)
    for q in questions:
        print(f"- {q}")