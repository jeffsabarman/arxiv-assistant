import arxiv
import pymupdf as fitz
import tempfile
import os
import re
import requests

def extract_arxiv_id(url: str) -> str:
    # Handles URLs
    match = re.search(r"arxiv\.org/abs/([^\s/]+)", url)
    if not match:
        raise ValueError(f"Could not extract ArXiv ID from URL: {url}")
    return match.group(1)

def fetch_paper(url: str) -> list[dict]:
    # Extract ID from URL
    try:
        arxiv_id = extract_arxiv_id(url)
        print(f"Fetching paper: {arxiv_id}")
    except ValueError as e:
        print(f"Invalid URL: {e}")
        raise

    # Fetch paper metadata
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(client.results(search)) # get the first item
        print(f"Title: {paper.title}")
    except StopIteration:
        raise ValueError(f"No paper found for ID: {arxiv_id}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch paper from ArXiv: {e}")

    try:
        # pdf_url = paper.pdf_url
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        print(f"Downloading PDF from: {pdf_url}")

        response = requests.get(pdf_url)
        response.raise_for_status()

        # Save PDF to a temp folder
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = f"{tmp_dir}/paper.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)

            # Extract text page by page
            doc = fitz.open(pdf_path)
            pages = []
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                pages.append({
                    "page": page_num,
                    "text": text
                })
                print(f"--- Page {page_num} ---")
                print(text[:300])

            doc.close()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")

    return pages

if __name__ == "__main__":
    # url = "https://arxiv.org/abs/1706.03762"
    url = "https://arxiv.org/abs/2608.15187"
    pages = fetch_paper(url)
    print(f"\nDone. Extracted {len(pages)} pages.")