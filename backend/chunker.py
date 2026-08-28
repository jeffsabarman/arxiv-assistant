import re
from pydantic import BaseModel
from paper import SectionData
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ChunkData(BaseModel):
    text: str
    section_number: str
    section_name: str
    parent_section: str
    chunk_index: int


def chunk_sections(sections: list[SectionData]) -> list[ChunkData]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = []
    chunk_index = 0

    for section in sections:
        # Skip sections with no text
        if not section.text.strip():
            continue

        # Split section text into chunks
        section_chunks = splitter.split_text(section.text)

        for chunk_text in section_chunks:
            # Skip very short chunks
            if len(chunk_text.strip()) < 50:
                continue

            chunks.append(ChunkData(
                text=chunk_text.strip(),
                section_number=section.section_number,
                section_name=section.section_name,
                parent_section=section.parent_section,
                chunk_index=chunk_index
            ))
            chunk_index += 1

    return chunks

if __name__ == "__main__":
    from paper import fetch_paper

    url = "https://arxiv.org/abs/1706.03762"
    metadata, sections = fetch_paper(url)
    chunks = chunk_sections(sections)

    print(f"\nDone. Created {len(chunks)} chunks from {len(sections)} sections.")
    print("\nSample chunks:")
    for chunk in chunks[:3]:
        parent = f" (under {chunk.parent_section})" if chunk.parent_section else ""
        print(f"\n--- [{chunk.chunk_index}] {chunk.section_number} {chunk.section_name}{parent} ---")
        print(chunk.text[:300])
