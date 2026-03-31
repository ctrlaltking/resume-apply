"""
Parse PDF or DOCX resume into structured JSON data.
"""
import json
import re
import sys
from pathlib import Path


def parse_pdf(path: str) -> str:
    import pdfplumber
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)


def parse_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_email(text: str) -> str:
    m = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = re.search(r"(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})", text)
    return m.group(0).strip() if m else ""


def extract_linkedin(text: str) -> str:
    m = re.search(r"linkedin\.com/in/[\w-]+", text, re.IGNORECASE)
    return m.group(0) if m else ""


def extract_github(text: str) -> str:
    m = re.search(r"github\.com/[\w-]+", text, re.IGNORECASE)
    return m.group(0) if m else ""


def extract_name(text: str) -> dict:
    """Heuristic: first non-empty line is usually the name."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return {"first": "", "last": "", "full": ""}
    name = lines[0]
    parts = name.split()
    return {
        "first": parts[0] if parts else "",
        "last": parts[-1] if len(parts) > 1 else "",
        "full": name,
    }


def extract_section(text: str, headers: list[str]) -> str:
    """Extract text under a section header until the next section."""
    pattern = r"(?i)(?:^|\n)(?:" + "|".join(re.escape(h) for h in headers) + r")\s*\n(.*?)(?=\n[A-Z][A-Z\s]{3,}\n|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_resume(path: str) -> dict:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        text = parse_pdf(str(path))
    elif path.suffix.lower() in (".docx", ".doc"):
        text = parse_docx(str(path))
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    linkedin = extract_linkedin(text)
    github = extract_github(text)

    summary = extract_section(text, ["Summary", "Objective", "Profile", "About"])
    experience = extract_section(text, ["Experience", "Work Experience", "Employment"])
    education = extract_section(text, ["Education", "Academic Background"])
    skills = extract_section(text, ["Skills", "Technical Skills", "Core Competencies"])

    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "summary": summary,
        "experience_raw": experience,
        "education_raw": education,
        "skills_raw": skills,
        "full_text": text,
    }

    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resume_parser.py <resume.pdf|resume.docx>")
        sys.exit(1)
    parse_resume(sys.argv[1])
