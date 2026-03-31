"""
Map HTML form fields to resume data using label/attribute heuristics.
"""
from __future__ import annotations
import re


# Keyword groups → resume data key
FIELD_MAP = [
    (["first.name", "firstname", "first_name", "fname", "given.name"], "name.first"),
    (["last.name", "lastname", "last_name", "lname", "surname", "family.name"], "name.last"),
    (["full.name", "fullname", "your.name", "applicant.name", "name"], "name.full"),
    (["email", "e-mail", "email.address"], "email"),
    (["phone", "telephone", "mobile", "cell", "contact.number", "phone.number"], "phone"),
    (["linkedin", "linkedin.url", "linkedin.profile"], "linkedin"),
    (["github", "github.url", "github.profile"], "github"),
    (["summary", "objective", "about", "profile", "cover", "bio"], "summary"),
    (["skill", "skills", "competencies", "expertise", "technologies"], "skills_raw"),
    (["education", "degree", "school", "university", "college", "gpa"], "education_raw"),
    (["experience", "work.history", "employment", "work.experience", "job"], "experience_raw"),
]


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", ".", text.lower().strip())


def get_resume_value(field_label: str, field_name: str, field_id: str, resume: dict) -> str | None:
    """
    Given field identifiers, return the matching resume value or None if unknown.
    """
    tokens = [
        _normalize(field_label or ""),
        _normalize(field_name or ""),
        _normalize(field_id or ""),
    ]

    for keywords, data_key in FIELD_MAP:
        for token in tokens:
            for kw in keywords:
                if kw in token or token in kw:
                    return _resolve(data_key, resume)
    return None


def _resolve(key: str, resume: dict):
    parts = key.split(".")
    val = resume
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, "")
        else:
            return ""
    return val or ""
