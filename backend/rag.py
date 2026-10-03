import os
from dotenv import load_dotenv
from embedder import query, get_abstract
from embedder import QueryResult
from schemas_model import (AnswerResponse, SourceResponse, Citation, LLMAnswer, 
                           RewrittenQueries, SuggestedQuestions)
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings

load_dotenv()

model = OpenAIChatModel("gpt-4o")

SYSTEM_PROMPT = """You are a research assistant that answers questions about academic papers.

Rules:
- Answer ONLY from the provided context chunks
- If the context contains relevant information to answer the question, set found to true
- Only set found to false if the context has no relevant information at all
- Synthesise information from multiple sections when relevant
- Cite ALL sections your answer draws from
- Only cite Abstract if no other section covers the question
- Be precise and concise

Formatting rules:
- Use bullet points or numbered lists for multiple points or findings
- Use **bold** for key terms and concepts
- Keep each bullet to 1-2 sentences max
- Only use a paragraph if the answer is a single, simple point
"""

agent = Agent(
    model,
    output_type=LLMAnswer,
    system_prompt=SYSTEM_PROMPT,
    model_settings=OpenAIChatModelSettings(
        max_tokens=1000,
        temperature=0
    )
)

REWRITE_QUERY_SYSTEM_PROMPT = """Generate 3 different versions of the given question to improve academic paper retrieval.
Use different vocabulary and phrasing but keep the same meaning.
Use keywords and terminology from the provided abstract to make the queries more specific to this paper."""

def build_context(results: QueryResult) -> str:
    """Format retreived chunks into a context string for the LLM"""
    context_parts = []

    for chunk in results.chunks:
        context_parts.append(f"[Section: {chunk.format_section()}]\n{chunk.text}")
    return "\n\n---\n\n".join(context_parts)

def build_confidence(results: QueryResult) -> str:
    scored_chunks = [c for c in results.chunks if c.distance >= 0]
    if not scored_chunks:
        return "unknown"
    avg_distance = sum(c.distance for c in scored_chunks) / len(results.chunks)
    if avg_distance < 0.5:
        return f"high"
    elif avg_distance < 0.8:
        return f"medium"
    else:
        return f"low"

query_rewriter = Agent(
    model,
    output_type=RewrittenQueries,
    system_prompt=REWRITE_QUERY_SYSTEM_PROMPT
)

async def rewrite_query(question: str, abstract: str = "") -> list[str]:
    result = await query_rewriter.run(
        f"""Paper abstract:
{abstract}

Question to rewrite: {question}"""
    )
    return [question] + result.output.queries

async def query_multi(question: str, arxiv_id: str, n_results: int = 5) -> QueryResult:
    # Get abstract text for query rewriting context
    abstract_chunks = get_abstract(arxiv_id)
    abstract_text = " ".join([c.text for c in abstract_chunks])

    queries = await rewrite_query(question, abstract=abstract_text)

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


RELEVANCE_THRESHOLD = 0.6

async def answer(question: str, arxiv_id: str, history: list[dict] = []) -> AnswerResponse:
    results = await query_multi(question, arxiv_id, n_results=5)

    relevant = [c for c in results.chunks if c.distance < RELEVANCE_THRESHOLD]
    if not relevant:
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

    result = await agent.run(
        f"""Context from the paper:

{context}

Question: {question}""",
        message_history=history
    )

    llm = result.output

    if not llm.found:
        return AnswerResponse(
            answer="I can't find this in the paper.",
            source=None,
            confidence=None
        )

    return AnswerResponse(
        answer=llm.answer,
        source=SourceResponse(
            citations=[
                Citation(quote=c.quote, section=c.section)
                for c in llm.citations
            ]
        ),
        confidence=confidence
    )

async def generate_summary(arxiv_id: str) -> str:
    result = await answer(
        "Summarise this paper as: one sentence TL;DR, the problem it solves, the approach, and the key findings.",
        arxiv_id
    )
    return result.answer

suggested_questions_agent = Agent(
    model,
    output_type=SuggestedQuestions,
    system_prompt="""Generate 4 interesting questions that can be answered from this paper.
Focus on methodology, results, and key contributions.""",
  model_settings=OpenAIChatModelSettings(
        max_tokens=300,
        temperature=0
    )
)

# TODO: user able to add the default question or instruction after upload and question answerd after each upload
async def generate_suggested_questions(arxiv_id: str) -> list[str]:
    abstract_chunks = get_abstract(arxiv_id)
    abstract_text = " ".join([c.text for c in abstract_chunks])

    result = await suggested_questions_agent.run(
        f"Paper abstract: {abstract_text}"
    )
    return result.output.questions

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
        print(f"Confidence: {result.confidence}")
        print(f"A: {result.answer[:500]}")
        if result.source:
            for c in result.source.citations:
                print(f"Section: {c.section}")
                print(f"Quote: {c.quote[:200]}")


    print("\n--- Summary ---")
    summary = generate_summary(arxiv_id)
    print(summary)

    print("\n--- Suggested Questions ---")
    questions = generate_suggested_questions(arxiv_id)
    for q in questions:
        print(f"- {q}")