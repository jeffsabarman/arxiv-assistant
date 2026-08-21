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

def download_pdf(pdf_url: str) -> bytes:
    try:
        print(f"Downloading PDF from: {pdf_url}")
        response = requests.get(pdf_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise RuntimeError(f"Failed to download PDF: {e}")

def save_pdf(pdf_bytes: bytes, tmp_dir: str) -> str:
    pdf_path = f"{tmp_dir}/paper.pdf"
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    return pdf_path

def extract_text(pdf_bytes: bytes) -> list[dict]:
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save PDF to a temp folder
            pdf_path = save_pdf(pdf_bytes, tmp_dir)

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

        return pages
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")


def fetch_paper(url: str) -> list[dict]:
    try:
        arxiv_id = extract_arxiv_id(url)
        print(f"Fetching paper: {arxiv_id}")

        metadata = fetch_metadata(arxiv_id)
        pdf_bytes = download_pdf(metadata.pdf_url)
        pages = extract_text(pdf_bytes)

        return metadata, pages
    except ValueError as e:
        print(f"Invalid URL: {e}")
        raise

if __name__ == "__main__":
    url = "https://arxiv.org/abs/1706.03762"
    # url = "https://arxiv.org/abs/2608.15187"
    metadata, pages = fetch_paper(url)
    print(f"\nDone. Extracted {len(pages)} pages from: {metadata.title}")