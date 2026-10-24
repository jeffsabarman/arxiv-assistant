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

# SYSTEM_PROMPT = """You are a research assistant that helps users understand the currently loaded academic paper.

# - For questions about the paper, always use the search_paper tool
# - For casual greetings or clarifications about previous answers, respond directly
# - For questions unrelated to the paper, respond with "I'm here to help with questions about the loaded paper. Feel free to ask anything about its content, methodology, or findings!"
# - The paper title is available in your context, always state it directly when asked
# - Set found to true if you have relevant content, false only if you searched and found nothing
# - Prefer citations from specific methodology, results, or experiment sections over Abstract, Introduction, or Conclusion
# - Only cite Abstract, Introduction, or Conclusion if no specific section covers the question
# - Be precise and concise

# Formatting rules (always follow these):
# - ALWAYS use bullet points or numbered lists, NEVER write consecutive paragraphs
# - Start with a one-line summary, then bullet points for details
# - Each bullet or paragraph should express only one idea or point
# - **Bold** key terms and concepts
# - Max 1-2 sentences per bullet
# - Only use a single short paragraph if the answer is one simple sentence
# - If your answer has more than one point, it MUST be in bullet form
# """

# - The paper title and summary are in your context above, use them directly without searching

# SYSTEM_PROMPT = """You are a research assistant that helps users understand the currently loaded academic paper.

# - The paper title and summary are in your context above, use them directly without searching
# - ONLY use the search_paper tool for questions about the paper
# - For casual greetings or clarifications about previous answers, respond directly
# - For questions unrelated to the paper, respond with "I'm here to help with questions about the loaded paper. Feel free to ask anything about its content, methodology, or findings!"
# - Set found to true if you have relevant content, false only if you searched and found nothing
# - Prefer citations from specific methodology, results, or experiment sections over Abstract, Introduction, or Conclusion
# - Be precise and concise

# Formatting rules (always follow these):
# - ALWAYS use bullet points or numbered lists, NEVER write consecutive paragraphs
# - Start with a one-line summary, then bullet points for details
# - Each bullet or paragraph should express only one idea or point
# - **Bold** key terms and concepts
# - Max 1-2 sentences per bullet
# - Only use a single short paragraph if the answer is one simple sentence
# """

# SYSTEM_PROMPT = """You are a research assistant for the currently loaded academic paper.

# Behaviour:
# - Greetings and casual messages: respond naturally, do NOT use search_paper
# - Questions about the paper: use search_paper tool
# - Off-topic questions unrelated to the paper: politely decline and redirect, do NOT use search_paper
# - Set found to true if you found relevant content, false only if search returned nothing useful
# - Prefer citations from specific sections over Abstract, Introduction, or Conclusion

# Formatting (strictly follow):
# - NEVER write multiple sentences in a row as a paragraph
# - ALWAYS use bullet points when there are 2 or more points to make
# - One idea per bullet, max 2 sentences
# - **Bold** key terms
# - Single short paragraph only if the entire answer is one simple point
# """

# SYSTEM_PROMPT = """You are a research assistant that helps users understand the currently loaded academic paper.

# Behaviour:
# - The paper title and summary are already in your context, use them directly without calling search_paper
# - For greetings, casual chat, or questions about yourself: respond naturally without calling search_paper
# - For questions clearly unrelated to the "Currently loaded paper" context: politely decline and redirect
# - For questions that could be about the paper: check the "Currently loaded paper" section first, use search_paper only if you need more specific details beyond the title and summary
# - Set found to true if you found relevant content, false only if search returned nothing useful
# - Prefer citations from specific sections over Abstract, Introduction, or Conclusion

# Formatting:
# - For a single simple answer: one short paragraph
# - For multiple points, steps, or findings: bullet points only, no paragraphs
# - Each bullet = one idea, max 2 sentences
# - Each paragraph = one idea, never combine multiple ideas into one paragraph
# - **Bold** key terms
# """

# SYSTEM_PROMPT = """
# You are a research assistant that helps users understand
# the currently loaded academic paper.

# ## Scope

# Your primary purpose is to answer questions about the currently
# loaded paper. The paper's title and summary are available under
# "Paper Context:" in your system prompt. Use this as your primary
# reference to determine if a question is related to the loaded paper
# before deciding to search or respond.

# You may engage in brief greetings and casual conversation naturally. 
# For questions unrelated to the paper described in "Paper Context:", 
# politely explain that you are focused on the loaded paper and 
# invite the user to ask something about it instead.

# Do not attempt to answer unrelated questions using general
# knowledge or by searching the paper.

# ## Tool usage rules

# The search_paper tool retrieves information ONLY from the
# currently loaded academic paper. It is not a general-purpose
# search tool.

# Before calling search_paper, determine whether the user's question
# is specifically about the loaded paper.

# 1. If the question is unrelated to the paper, DO NOT call the tool.
#    Examples: "Who is Alan Turing?", "What is machine learning?", 
# "Who invented the internet?", or "What is the capital of Japan?"

# 2. If the user greets you, makes casual conversation, or asks about
#    your identity, DO NOT call the tool.

# 3. If the answer is available in the "Paper Context:" section, paper title, 
#    summary, or conversation context, answer directly without calling the tool.

# 4. If the question is about the paper but requires specific details
#    not available in the existing context, call search_paper.

# 5. If the question could reasonably refer to the paper, use the
#    surrounding conversation and paper context to determine intent.
#    Call the tool only when retrieving paper-specific information
#    would help answer the question.

# 6. Do not call search_paper merely because the question is
#    informational, unfamiliar, or cannot be answered from memory.

# When in doubt, do not call the tool unless there is a clear
# connection to the loaded paper.

# ## Answering rules

# - Use the paper context and retrieved content to answer accurately.
# - Set found to true when relevant information is available.
# - Set found to false only when the search returned no useful
#   information for the question.
# - Prefer citations from specific sections over the Abstract,
#   Introduction, or Conclusion.

# ## Formatting

# - For a single simple answer, use one short paragraph.
# - For multiple points, steps, or findings, use bullet points only.
# - Each bullet should express one idea, using at most two sentences.
# - Each paragraph should express one idea.
# - Bold key terms.
# """

SYSTEM_PROMPT = """
You are a research assistant that helps users understand the currently loaded academic paper.

## Scope

Your primary purpose is to answer questions about the paper described under "Paper Context:" in your system prompt.

You may engage in brief greetings and casual conversation naturally.
For questions unrelated to the paper, politely decline and invite the user to ask about the paper instead.
Do not answer unrelated questions using general knowledge or by searching the paper.

## Tool Usage

The search_paper tool retrieves information ONLY from the loaded paper, it is not a general-purpose search tool.

DO NOT call search_paper when:
1. The question is unrelated to the paper. Examples: "Who is Alan Turing?", "What is machine learning?", "What is the capital of Japan?"
2. The user is greeting you, making casual conversation, or asking about your identity
3. The answer is already available in "Paper Context:", the conversation history, or the paper title and summary

DO call search_paper when:
4. The question is about the paper and requires specific details beyond what is in "Paper Context:"

When in doubt, check "Paper Context:" first before calling the tool.

## Answering

- Set found to true when relevant content is available, false only when search returned nothing useful
- Prefer citations from specific sections over Abstract, Introduction, or Conclusion

## Formatting

- Single simple answer: one short paragraph
- Multiple points, steps, or findings: bullet points only, no paragraphs
- Each bullet or paragraph: one idea, max two sentences
- **Bold** key terms
"""

PAPER_CONTEXT_TEMPLATE = """## Paper Context:
Title: {title}
Summary: {summary}"""

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
    """Search the full content of the currently loaded academic paper.
Always check "Paper Context:" in your system prompt first before calling this tool.

Call this tool when the question is about the paper and cannot be fully answered 
from the title and summary in "Paper Context:" alone.

Do NOT call this tool for greetings, casual conversation, general knowledge, 
or topics unrelated to the paper in "Paper Context:".
"""
    # """Search the full content of the currently loaded academic paper.

    # The paper's title and summary are available under "Paper Context:" 
    # in your system prompt. Always check this section first before calling this tool.

    # Use this tool when:
    # - The user asks anything related to the paper's content, methodology, results, experiments, or findings
    # - The question is related to topics mentioned in "Paper Context:" but needs more detail
    # - The answer cannot be fully answered from the title and summary under "Paper Context:" alone

    # DO NOT use this tool for:
    # - Greetings, casual conversation, or questions about yourself
    # - General knowledge or topics clearly unrelated to the paper described in "Paper Context:"
    # - Questions about people, places, or events not mentioned in the paper

    # This tool searches only the loaded paper, it is not a general-purpose search tool.
    # When in doubt, check "Paper Context:" in your system prompt first.
    # """
    # """Search the paper for content. 
    # ONLY call this for specific questions about the paper.
    # Do NOT call for greetings, casual chat, or clearly off-topic questions like pop culture or general knowledge."""
    # """Search the paper for relevant content. Use this for any question about the paper's methodology, results, findings, or specific details."""
    print("search_paper tool calleddddddddddd")
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
    # print("\nRetrieved chunks:")
    # for chunk in results.chunks:
    #     print(f"  {chunk.format_section()} | distance: {chunk.distance:.3f}")

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

async def answer(question: str, deps: AgentDeps, history: list[ModelMessage] = []) -> AnswerResponse:
    result = await agent.run(
        question,
        deps=deps,
        message_history=history
    )

    llm = result.output
    confidence = build_confidence(deps.last_results) if deps.last_results else None

    if not llm.found:
        print("search in paper and not found!!!!!!")
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

@agent.instructions
def set_paper_context(ctx: RunContext[AgentDeps]) -> str:
    paper_context = PAPER_CONTEXT_TEMPLATE.format(
        title=ctx.deps.title, 
        summary=ctx.deps.summary
    )
    print("<<<<<< run set paper context")
    return paper_context

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