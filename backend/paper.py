import arxiv
# import pymupdf as fitz
import tempfile
import os
import re
import requests
from pydantic import BaseModel
from bs4 import BeautifulSoup

SKIP_SECTIONS = {
    "references",
    "acknowledgements", 
    "acknowledgments",
    "report github issue",
    "instructions for reporting errors",
}

class SectionData(BaseModel):
    section_number: str     # "3.2.1" or "" for abstract
    section_name: str       # "Scaled Dot-Product Attention"
    parent_section: str     # "3 Model Architecture" or "" for top-level
    text: str               # can be empty for parent sections with no body text

def extract_arxiv_id(url: str) -> str:
    match = re.search(r"arxiv\.org/abs/([^\s/]+)", url)
    if not match:
        raise ValueError(f"Could not extract ArXiv ID from URL: {url}")
    return match.group(1)

def fetch_metadata(arxiv_id: str) -> arxiv.Result:
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(client.results(search)) # get the first item
        print(f"Title: {paper.title}")
        return paper
    except StopIteration:
        raise ValueError(f"No paper found for ID: {arxiv_id}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch paper from ArXiv: {e}")

def fetch_html(arxiv_id: str) -> str | None:
    try:
        url = f"https://arxiv.org/html/{arxiv_id}"
        print(f"Fetching HTML from: {url}")
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            print("HTML version found")
            return response.text
        else:
            print(f"HTML version not available (status {response.status_code})")
            return None
    except Exception as e:
        print(f"Failed to fetch HTML: {e}")
        return None

def parse_section_number(heading: str) -> tuple[str, str]:
    match = re.match(r"^(\d+(?:\.\d+)*)\s*(.*)", heading)
    if match:
        return match.group(1), match.group(2).strip()
    return "", heading.strip()

# def get_direct_paragraphs(section_tag) -> str:
#     """Get only paragraphs directly in this section, not in nested sections"""
#     paragraphs = []
#     for child in section_tag.children:
#         # Skip nested sections entirely
#         if getattr(child, "name", None) == "section":
#             continue
#         # Get paragraphs from direct children
#         if hasattr(child, "find_all"):
#             for p in child.find_all("p", recursive=False):
#                 text = p.get_text(strip=True)
#                 if text:
#                     paragraphs.append(text)
#             # Also check if the child itself is a p
#             if child.name == "p":
#                 text = child.get_text(strip=True)
#                 if text:
#                     paragraphs.append(text)
#     return " ".join(paragraphs).strip()

# def get_direct_paragraphs(section_tag) -> str:
#     """Get only text directly in this section, not in nested sections"""
#     import copy
#     section_copy = copy.copy(section_tag)
    
#     # Remove nested sections from the copy
#     for nested in section_copy.find_all("section"):
#         nested.decompose()
    
#     return section_copy.get_text(separator=" ", strip=True)
def get_direct_paragraphs(section_tag) -> str:
    """Get only text directly in this section, not in nested sections"""
    import copy
    section_copy = copy.copy(section_tag)
    
    # Remove nested sections
    for nested in section_copy.find_all("section"):
        nested.decompose()
    
    # Remove the heading
    for heading in section_copy.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        heading.decompose()
    
    return section_copy.get_text(separator=" ", strip=True)

def parse_section(section_tag, parent_section: str = "") -> list[SectionData]:
    """Recursively parse a section and its subsections"""
    results = []

    # Get heading
    heading_tag = section_tag.find(["h1", "h2", "h3", "h4", "h5", "h6"], recursive=False)
    if not heading_tag:
        # Try one level deeper
        for child in section_tag.children:
            if hasattr(child, "find"):
                heading_tag = child.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                if heading_tag:
                    break

    if not heading_tag:
        return results

    heading_text = heading_tag.get_text(strip=True)

    # Skip unwanted sections
    if heading_text.lower() in SKIP_SECTIONS:
        return results

    # Split into number and name
    section_number, section_name = parse_section_number(heading_text)

    # Get direct paragraph text (not from nested sections)
    text = get_direct_paragraphs(section_tag)

    # Full section label for use as parent reference
    full_label = f"{section_number} {section_name}".strip()

    results.append(SectionData(
        section_number=section_number,
        section_name=section_name,
        parent_section=parent_section,
        text=text
    ))

    # Recursively parse nested sections
    for nested in section_tag.find_all("section", recursive=False):
        results.extend(parse_section(nested, parent_section=full_label))

    return results

def parse_outside_sections(soup) -> list[SectionData]:
    """Get any headings and their text that live outside of section tags"""
    results = []
    current_heading = None
    current_text = []

    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"]):
        # Skip if this element is inside a section tag
        if element.find_parent("section"):
            continue

        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            heading_text = element.get_text(strip=True)
            # print(heading_text, "<<<< HEADING TEXT OUTSIDE SECTIONS")
            # Skip unwanted sections
            if heading_text.lower() in SKIP_SECTIONS:
                # Save whatever we have before resetting
                if current_heading and current_text:
                    results.append(SectionData(
                        section_number="",
                        section_name=current_heading,
                        parent_section="",
                        text=" ".join(current_text).strip()
                    ))
                current_heading = None
                current_text = []
                continue

            if current_heading and current_text:
                results.append(SectionData(
                    section_number="",
                    section_name=current_heading,
                    parent_section="",
                    text=" ".join(current_text).strip()
                ))
            current_heading = heading_text
            current_text = []
        elif element.name == "p":
            text = element.get_text(strip=True)
            # print(text, "<<<< TEXTTTTTT")
            if text:
                current_text.append(text)

    # Don't forget the last one
    if current_heading and current_text:
        results.append(SectionData(
            section_number="",
            section_name=current_heading,
            parent_section="",
            text=" ".join(current_text).strip()
        ))

    return results

def parse_sections_from_html(html: str) -> list[SectionData]:
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "figure", "table"]):
        tag.decompose()

    sections = []

    # Capture everything outside section tags (abstract, preamble, etc.)
    sections.extend(parse_outside_sections(soup))

    # Walk top-level section tags only, recursion handles the rest
    body = soup.find("body") or soup
    for section_tag in body.find_all("section", recursive=True):
        if not section_tag.find_parent("section"):
            sections.extend(parse_section(section_tag, parent_section=""))
        # sections.extend(parse_section(section_tag, parent_section=""))

    # # Also check one level deeper in case sections are wrapped in a div
    # if not sections:
    #     for wrapper in body.find_all(recursive=False):
    #         if hasattr(wrapper, "find_all"):
    #             for section_tag in wrapper.find_all("section", recursive=False):
    #                 sections.extend(parse_section(section_tag, parent_section=""))

    return sections

def fetch_paper(url: str) -> tuple[arxiv.Result, list[SectionData]]:
    try:
        arxiv_id = extract_arxiv_id(url)
        print(f"Fetching paper: {arxiv_id}")

        metadata = fetch_metadata(arxiv_id)

        html = fetch_html(arxiv_id)
        if html:
            sections = parse_sections_from_html(html)
            print(f"Extracted {len(sections)} sections from HTML")
            return metadata, sections, arxiv_id

        raise RuntimeError(
            "HTML version not available for this paper. "
            "PDF fallback not yet implemented."
        )

    except ValueError as e:
        print(f"Invalid URL: {e}")
        raise

# def download_pdf(pdf_url: str) -> bytes:
#     try:
#         print(f"Downloading PDF from: {pdf_url}")
#         response = requests.get(pdf_url)
#         response.raise_for_status()
#         return response.content
#     except Exception as e:
#         raise RuntimeError(f"Failed to download PDF: {e}")

# def save_pdf(pdf_bytes: bytes, tmp_dir: str) -> str:
#     pdf_path = f"{tmp_dir}/paper.pdf"
#     with open(pdf_path, "wb") as f:
#         f.write(pdf_bytes)
#     return pdf_path

# def extract_text(pdf_bytes: bytes) -> list[PageData]:
#     try:
#         with tempfile.TemporaryDirectory() as tmp_dir:
#             # Save PDF to a temp folder
#             pdf_path = save_pdf(pdf_bytes, tmp_dir)

#             # Extract text page by page
#             doc = fitz.open(pdf_path)
#             pages = []
#             for page_num, page in enumerate(doc, start=1):
#                 text = page.get_text()
#                 pages.append({
#                     "page": page_num,
#                     "text": text
#                 })
#                 print(f"--- Page {page_num} ---")
#                 print(text[:300])

#             doc.close()

#         return pages
#     except Exception as e:
#         raise RuntimeError(f"Failed to extract text from PDF: {e}")


# def fetch_paper(url: str) -> tuple[arxiv.Result, list[PageData]]:
#     try:
#         arxiv_id = extract_arxiv_id(url)
#         print(f"Fetching paper: {arxiv_id}")

#         metadata = fetch_metadata(arxiv_id)
#         pdf_bytes = download_pdf(metadata.pdf_url)
#         pages = extract_text(pdf_bytes)

#         return metadata, pages
#     except ValueError as e:
#         print(f"Invalid URL: {e}")
#         raise

if __name__ == "__main__":
    url = "https://arxiv.org/abs/1706.03762"
    # url = "https://arxiv.org/abs/2608.15187"
    # metadata, pages = fetch_paper(url)
    # print(f"\nDone. Extracted {len(pages)} pages from: {metadata.title}")

    metadata, sections = fetch_paper(url)

    # print(f"\nDone. Extracted {len(sections)} sections from: {metadata.title}")
    # print("\nSections:")
    # for section in sections:
    #     # print(f"\n--- Section: {section.section} ---")
    #     # print(section.text[:300])
    #     print(f"Section: {section.section} | Text length: {len(section.text)}")

    print(f"\nDone. Extracted {len(sections)} sections from: {metadata.title}")
    print("\nAll sections:")
    for s in sections:
        parent = f" (under {s.parent_section})" if s.parent_section else ""
        print(f"{s.section_number} {s.section_name}{parent} | Text length: {len(s.text)}")
        print(s.text[:200])