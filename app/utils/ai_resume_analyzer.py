"""
Lightweight, dependency-minimal 'AI' Resume Analyzer & ATS Scoring engine.

This performs rule-based / NLP-lite analysis (no external API calls, works
fully offline which is ideal for an academic project and for grading/demo
purposes without needing API keys):

  1. Extracts raw text from an uploaded PDF resume (pdfplumber).
  2. Checks for structural sections an ATS parser looks for.
  3. Scores keyword / skill density against a target role or general
     technical keyword bank.
  4. Flags formatting issues that commonly break real-world ATS parsers.
  5. Produces an overall ATS score (0-100) + actionable suggestions.
"""

import re

SECTION_KEYWORDS = {
    "contact": ["email", "phone", "linkedin", "github", "@"],
    "education": ["education", "b.tech", "btech", "cgpa", "university", "college", "rgukt"],
    "skills": ["skills", "technical skills", "programming languages", "tools"],
    "experience": ["experience", "internship", "work experience", "employment"],
    "projects": ["project", "projects"],
    "achievements": ["achievement", "certification", "certificate", "award"],
}

TECH_KEYWORD_BANK = [
    "python", "java", "javascript", "c++", "c programming", "react", "node.js",
    "flask", "django", "sql", "mysql", "mongodb", "html", "css", "git", "github",
    "machine learning", "deep learning", "data structures", "algorithms",
    "aws", "cloud", "docker", "kubernetes", "rest api", "api", "linux",
    "tensorflow", "pandas", "numpy", "excel", "power bi", "tableau",
    "communication", "leadership", "teamwork", "problem solving",
    "android", "kotlin", "swift", "typescript", "spring boot", "figma",
]

ACTION_VERBS = [
    "developed", "designed", "built", "implemented", "created", "led",
    "managed", "optimized", "improved", "automated", "analyzed", "deployed",
    "collaborated", "achieved", "reduced", "increased", "engineered",
]


def extract_text_from_pdf(filepath):
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        return text
    except Exception as e:
        return ""


def analyze_resume(text, target_keywords=None):
    """
    Returns a dict with ats_score, section_checks, keyword matches,
    matched/missing keywords and improvement suggestions.
    """
    if not text or len(text.strip()) < 30:
        return {
            "ats_score": 0,
            "word_count": 0,
            "sections_found": {},
            "matched_keywords": [],
            "missing_keywords": [],
            "action_verb_count": 0,
            "suggestions": [
                "We couldn't read enough text from this file. Upload a text-based PDF "
                "(not a scanned image) for accurate ATS analysis."
            ],
        }

    lower = text.lower()
    word_count = len(re.findall(r"\w+", text))

    # 1. Section presence check (30 points)
    sections_found = {}
    for section, keys in SECTION_KEYWORDS.items():
        sections_found[section] = any(k in lower for k in keys)
    section_score = sum(1 for v in sections_found.values() if v) / len(sections_found) * 30

    # 2. Keyword density check (40 points)
    keyword_bank = target_keywords if target_keywords else TECH_KEYWORD_BANK
    matched_keywords = [k for k in keyword_bank if k.lower() in lower]
    missing_keywords = [k for k in keyword_bank if k.lower() not in lower][:8]
    keyword_score = min(len(matched_keywords) / max(len(keyword_bank), 1), 1) * 40

    # 3. Action verbs / impact language (15 points)
    action_hits = [v for v in ACTION_VERBS if v in lower]
    action_score = min(len(action_hits) / 6, 1) * 15

    # 4. Length / formatting sanity (15 points)
    length_score = 15
    suggestions = []
    if word_count < 150:
        length_score = 4
        suggestions.append("Your resume looks too short. Aim for at least 300-500 words covering skills, projects, and education.")
    elif word_count > 1200:
        length_score = 8
        suggestions.append("Your resume is quite long for a fresher/entry-level role. Try to keep it to 1-2 pages.")

    ats_score = round(section_score + keyword_score + action_score + length_score)
    ats_score = max(0, min(100, ats_score))

    if not sections_found.get("contact"):
        suggestions.append("Add a clear contact section with email, phone number, LinkedIn and GitHub links.")
    if not sections_found.get("skills"):
        suggestions.append("Add a dedicated 'Skills' section listing your technical skills — ATS systems specifically scan for this section.")
    if not sections_found.get("projects"):
        suggestions.append("Add a 'Projects' section. Recruiters and ATS both weigh hands-on projects heavily for freshers.")
    if not sections_found.get("education"):
        suggestions.append("Add an 'Education' section with your degree, college (RGUKT Ongole), branch and CGPA.")
    if len(action_hits) < 3:
        suggestions.append("Use more action verbs (Developed, Built, Implemented, Led) to describe your work — it reads stronger to both ATS and recruiters.")
    if missing_keywords:
        suggestions.append(f"Consider adding relevant keywords if applicable to you: {', '.join(missing_keywords[:6])}.")
    if not suggestions:
        suggestions.append("Great job! Your resume covers the key sections and keywords ATS systems look for.")

    return {
        "ats_score": ats_score,
        "word_count": word_count,
        "sections_found": sections_found,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "action_verb_count": len(action_hits),
        "suggestions": suggestions[:6],
    }


def extract_skills(text):
    """Return a comma separated skills string inferred from resume text."""
    if not text:
        return ""
    lower = text.lower()
    found = [k for k in TECH_KEYWORD_BANK if k.lower() in lower]
    return ", ".join(s.title() for s in found[:15])
