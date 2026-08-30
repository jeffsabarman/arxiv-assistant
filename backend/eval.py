import json
from rag import answer

# Test cases: question, expected_found, notes
TEST_CASES = [
    {
        "question": "What's the paper about?",
        "expected_found": True,
        "notes": "General question, should always be answered from the abstract"
    },
    {
        "question": "How does the attention mechanism work?",
        "expected_found": True,
        "notes": "Core topic of the paper, should always find"
    },
    {
        "question": "What datasets were used for training?",
        "expected_found": True,
        "notes": "Explicitly mentioned in section 5.1"
    },
    {
        "question": "What are the limitations of the Transformer model presented in this paper?",
        "expected_found": True,  # changed from False
        "notes": "Implicit limitation mentioned in section 4 Why Self-Attention - performance degrades for very long sequences"
    },
    {
        "question": "What future work do the authors suggest?",
        "expected_found": True,
        "notes": "Conclusion mentions future work"
    },
    {
        "question": "What is the meaning of life?",
        "expected_found": False,
        "notes": "Completely unrelated, should never find"
    },
    {
        "question": "What BLEU score did the Transformer achieve?",
        "expected_found": True,
        "notes": "Explicitly in results section"
    },
    {
        "question": "Who funded this research?",
        "expected_found": False,
        "notes": "Not in main paper content"
    },
]


def run_evals(arxiv_id: str):
    print(f"Running {len(TEST_CASES)} eval cases...\n")

    passed = 0
    failed = 0
    failed_cases = []

    for i, case in enumerate(TEST_CASES):
        result = answer(case["question"], arxiv_id)
        actual_found = result["source"] is not None

        success = actual_found == case["expected_found"]

        status = "✅ PASS" if success else "❌ FAIL"
        if success:
            passed += 1
        else:
            failed += 1
            failed_cases.append(case)

        print(f"{status} [{i+1}/{len(TEST_CASES)}] {case['question']}")
        print(f"       Expected found: {case['expected_found']} | Actual found: {actual_found}")
        print(f"       Confidence: {result['confidence']}")
        if not success:
            print(f"       Note: {case['notes']}")
            print(f"       Answer: {result['answer'][:200]}")
        print()

    print(f"Results: {passed}/{len(TEST_CASES)} passed")

    if failed_cases:
        print(f"\nFailed cases to fix:")
        for case in failed_cases:
            print(f"  - {case['question']}")
            print(f"    {case['notes']}")


if __name__ == "__main__":
    from paper import fetch_paper
    from chunker import chunk_sections
    from embedder import embed_chunks

    url = "https://arxiv.org/abs/1706.03762"
    metadata, sections, arxiv_id = fetch_paper(url)
    chunks = chunk_sections(sections)
    embed_chunks(chunks, arxiv_id)

    run_evals(arxiv_id)