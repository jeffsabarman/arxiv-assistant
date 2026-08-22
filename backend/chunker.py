import re
from pydantic import BaseModel
from paper import PageData

class ChunkData(BaseModel):
    text: str
    section: str
    page: int

SECTION_HEADINGS = re.compile(
    r"^(abstract|introduction|background|related work|methodology|methods|"
    r"experiments|results|discussion|conclusion|references|appendix)\s*$",
    re.IGNORECASE | re.MULTILINE
)

def detect_section(text: str, current_section: str) -> str:
    match = SECTION_HEADINGS.search(text)
    if match:
        return match.group(1).title()
    return current_section

def chunk_pages(pages: list[PageData]) -> list[ChunkData]:
    chunks = []
    current_section = "Introduction"

    for page in pages:
        # Detect if this page starts a new section
        current_section = detect_section(page.text, current_section)

        # Split page text into paragraphs
        paragraphs = [p.strip() for p in page.text.split("\n\n") if p.strip()]

        for paragraph in paragraphs:
            # Skip very short paragraphs
            if len(paragraph) < 50:
                continue

            chunks.append(ChunkData(
                text=paragraph,
                section=current_section,
                page=page.page
            ))
    return chunks

if __name__ == "__main__":
    from paper import fetch_paper

    url = "https://arxiv.org/abs/1706.03762"
    metadata, pages = fetch_paper(url)
    chunks = chunk_pages(pages)

    print(f"\nDone. Created {len(chunks)} chunks from {len(pages)} pages.")
    print("\nSample chunks:")
    for chunk in chunks[:3]:
        print(f"\n--- Section: {chunk.section} | Page: {chunk.page} ---")
        print(chunk.text[:200])
