import os
from dotenv import load_dotenv
from embedder import query, get_abstract
from embedder import QueryResult
from schemas_model import (AnswerResponse, SourceResponse, Citation, LLMAnswer, 
                           RewrittenQueries, SuggestedQuestions, AgentDeps)
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.messages import ModelMessage

load_dotenv()

model = OpenAIChatModel("gpt-4o")

SYSTEM_PROMPT = """You are a research assistant that helps users understand academic papers.

- For casual messages or general concepts not in the paper, answer directly without searching
- Set found to true if you have relevant content, false only if you searched and found nothing
- Cite ALL sections your answer draws from, avoid Abstract unless no other section covers it
- Be precise and concise

Formatting:
- Bullet points or numbered lists for multiple findings
- **Bold** key terms, max 1-2 sentences per bullet
- Only use a paragraph for single simple points
"""

agent = Agent(
    model,
    output_type=LLMAnswer,
    system_prompt=SYSTEM_PROMPT,
    model_settings=OpenAIChatModelSettings(
        max_tokens=1000,
        temperature=0
    ),
    deps_type=AgentDeps
)

RELEVANCE_THRESHOLD = 0.6

@agent.tool
async def search_paper(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search the paper for relevant content. Use this for any question about the paper's methodology, results, findings, or specific details."""
    results = await query_multi(query, ctx.deps.arxiv_id, n_results=5)

    relevant = [c for c in results.chunks if c.distance < RELEVANCE_THRESHOLD]
    if not relevant:
        abstract_chunks = get_abstract(ctx.deps.arxiv_id)
        existing_text = {c.text for c in results.chunks}
        for chunk in abstract_chunks:
            if chunk.text not in existing_text:
                results.chunks.append(chunk)

    ctx.deps.last_results = results # store for confidence calc

    # debug
    print("\nRetrieved chunks:")
    for chunk in results.chunks:
        print(f"  {chunk.format_section()} | distance: {chunk.distance:.3f}")

    return build_context(results)
            


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

def get_abstract_text(arxiv_id: str) -> str:
    abstract_chunks = get_abstract(arxiv_id)
    return " ".join([c.text for c in abstract_chunks])

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
    abstract_text = get_abstract_text(arxiv_id)

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

async def answer(question: str, arxiv_id: str, history: list[ModelMessage] = []) -> AnswerResponse:
    deps = AgentDeps(arxiv_id=arxiv_id)

    result = await agent.run(
        question,
        deps=deps,
        message_history=history
    )

    llm = result.output
    confidence = build_confidence(deps.last_results) if deps.last_results else None

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
        ) if llm.citations else None,
        confidence=confidence
    )

summary_agent = Agent(
    model,
    output_type=str,
    system_prompt="""You are an expert research assistant that summarises academic papers.
You have expertise in identifying the core contributions, methodology, and impact of research.
Always use markdown formatting with clear sections and **bold** key terms."""
)

async def generate_summary(arxiv_id: str, title: str = "") -> str:
    abstract_text = get_abstract_text(arxiv_id)
    result = await summary_agent.run(
        f"""Summarise this paper:
- One sentence TL;DR
- The problem it solves
- The approach taken
- The key findings

Title: {title}
Abstract: {abstract_text}"""
    )
    return result.output


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
    abstract_text = get_abstract_text(arxiv_id)

    result = await suggested_questions_agent.run(
        f"Paper abstract: {abstract_text}"
    )
    return result.output.questions

_paper_context: str = ""

def set_paper_context(title: str, summary: str) -> None:
    global _paper_context
    _paper_context = f"Title: {title}\nSummary: {summary}"
    agent.system_prompt = f"{SYSTEM_PROMPT}\n\nCurrently loaded paper:\n{_paper_context}"

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