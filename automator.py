"""
Selenium-based form filler.

Usage:
    python automator.py <job_url> <resume.pdf|resume.docx>

Flow:
    1. Open job URL in visible Chrome window
    2. Wait for you to log in / pass CAPTCHA (press Enter in terminal)
    3. Scan all visible form fields
    4. Fill anything matched from resume
    5. For unknown required fields: ask you in terminal, cache answer, fill
    6. Pause before final submit so you can review — press Enter to submit
"""
from __future__ import annotations

import sys
import time
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementNotInteractableException,
    StaleElementReferenceException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager

from resume_parser import parse_resume
from field_mapper import get_resume_value
from answer_cache import load as load_cache, get_or_ask


def normalize_job_url(url: str) -> str:
    """Strip whitespace and fix accidental double schemes (e.g. https://https://...)."""
    url = url.strip()
    lower = url.lower()
    while lower.startswith("https://https://"):
        url = url[8:]
        lower = url.lower()
    while lower.startswith("http://http://"):
        url = url[7:]
        lower = url.lower()
    if lower.startswith("http://https://"):
        url = "https://" + url[7:]
    elif lower.startswith("https://http://"):
        url = "http://" + url[8:]
    return url


def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    return driver


def get_label_for(driver: webdriver.Chrome, element) -> str:
    """Find the visible label text associated with a form element."""
    eid = element.get_attribute("id") or ""
    # <label for="id">
    if eid:
        try:
            label = driver.find_element(By.CSS_SELECTOR, f'label[for="{eid}"]')
            return label.text.strip()
        except NoSuchElementException:
            pass
    # aria-label / placeholder / title
    for attr in ("aria-label", "placeholder", "title", "name"):
        val = element.get_attribute(attr) or ""
        if val.strip():
            return val.strip()
    # parent label wrapping the element
    try:
        parent = element.find_element(By.XPATH, "./ancestor::label[1]")
        return parent.text.strip()
    except NoSuchElementException:
        pass
    return ""


def fill_text(element, value: str):
    element.clear()
    element.send_keys(value)


def fill_select(element, value: str):
    sel = Select(element)
    try:
        sel.select_by_visible_text(value)
        return
    except Exception:
        pass
    # fuzzy match
    for opt in sel.options:
        if value.lower() in opt.text.lower() or opt.text.lower() in value.lower():
            sel.select_by_visible_text(opt.text)
            return
    # fall back to first non-empty option
    for opt in sel.options:
        if opt.get_attribute("value"):
            sel.select_by_visible_text(opt.text)
            return


def process_fields(driver: webdriver.Chrome, resume: dict, cache: dict):
    inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
    filled = 0
    skipped_labels = set()

    for el in inputs:
        try:
            tag = el.tag_name.lower()
            itype = (el.get_attribute("type") or "text").lower()

            # Skip hidden, submit, button, checkbox, radio (handle separately if needed)
            if itype in ("hidden", "submit", "button", "file", "checkbox", "radio"):
                continue
            if not el.is_displayed() or not el.is_enabled():
                continue

            label = get_label_for(driver, el)
            name = el.get_attribute("name") or ""
            eid = el.get_attribute("id") or ""

            # Try resume data first
            value = get_resume_value(label, name, eid, resume)

            if value:
                try:
                    if tag == "select":
                        fill_select(el, value)
                    else:
                        fill_text(el, value)
                    filled += 1
                    print(f"  [FILLED] {label or name or eid!r} → {str(value)[:60]}")
                except (ElementNotInteractableException, StaleElementReferenceException):
                    pass
            else:
                # Unknown field — ask user
                question = label or name or eid
                if not question or question in skipped_labels:
                    continue
                skipped_labels.add(question)

                answer = get_or_ask(question, cache)
                if answer:
                    try:
                        if tag == "select":
                            fill_select(el, answer)
                        else:
                            fill_text(el, answer)
                        filled += 1
                    except (ElementNotInteractableException, StaleElementReferenceException):
                        pass

        except StaleElementReferenceException:
            continue

    print(f"\n  Filled {filled} field(s).")


def run(url: str, resume_path: str):
    raw_url = url
    url = normalize_job_url(url)
    if url != raw_url.strip():
        print(f"\n[NOTE] Normalized URL (removed duplicate scheme / whitespace).")

    print(f"\nParsing resume: {resume_path}")
    resume = parse_resume(resume_path)
    cache = load_cache()

    print(f"\nOpening: {url}")
    driver = make_driver()
    driver.get(url)

    input("\n[ACTION REQUIRED] Log in / pass any CAPTCHA, then press Enter to start filling...\n")

    print("\nScanning and filling fields...")
    process_fields(driver, resume, cache)

    input("\n[REVIEW] Check the form. Press Enter when ready to submit (or close the browser to cancel)...\n")

    # Try to click the primary submit button
    try:
        submit_btn = driver.find_element(
            By.CSS_SELECTOR,
            "button[type=submit], input[type=submit], button.submit, button.apply"
        )
        submit_btn.click()
        print("\n[SUBMITTED] Form submitted.")
        time.sleep(3)
    except NoSuchElementException:
        print("\n[MANUAL SUBMIT] Could not find a submit button. Please submit manually.")

    input("\nPress Enter to close the browser...")
    driver.quit()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python automator.py <job_url> <resume.pdf|resume.docx>")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])
