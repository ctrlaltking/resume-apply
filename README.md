# resume-apply

A Selenium-based tool that parses your resume (PDF or DOCX) and automatically fills out job application forms — pausing when you need to handle logins, CAPTCHAs, or unknown fields.

## How it works

1. Opens the job application URL in a visible Chrome window
2. Pauses so you can log in or solve any CAPTCHA
3. Scans all form fields and fills them using data from your resume
4. For any field it doesn't recognize, it asks you in the terminal and caches your answer
5. Pauses for a final review before submitting

Unknown field answers are saved to `answer_cache.json` — so questions like "Are you authorized to work in the US?" are only asked once across all applications.

## Setup

**Requirements:** Python 3.10+, Google Chrome installed

```bash
pip install -r requirements.txt
```

## Usage

```bash
python automator.py "<job_application_url>" resume.pdf
```

or with a DOCX:

```bash
python automator.py "<job_application_url>" resume.docx
```

## What gets auto-filled

| Field | Source |
|-------|--------|
| First / Last / Full name | Resume header |
| Email | Resume contact info |
| Phone | Resume contact info |
| LinkedIn URL | Resume contact info |
| GitHub URL | Resume contact info |
| Summary / Objective | Resume summary section |
| Skills | Resume skills section |
| Education | Resume education section |
| Work experience | Resume experience section |

Fields not matched from the resume are asked interactively in the terminal and cached for future runs.

## Files

| File | Purpose |
|------|---------|
| `automator.py` | Main script — Selenium driver and form-filling logic |
| `resume_parser.py` | Extracts structured data from PDF or DOCX |
| `field_mapper.py` | Maps form field labels/names to resume data |
| `answer_cache.py` | Reads/writes cached answers to unknown fields |
| `answer_cache.json` | Your saved answers (auto-created, git-ignored) |

## Notes

- `answer_cache.json` and your resume files are excluded from git via `.gitignore`
- The browser window stays visible throughout — you stay in control
- The tool will not auto-submit without your confirmation
