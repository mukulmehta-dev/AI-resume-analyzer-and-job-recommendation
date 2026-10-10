import re
from typing import Dict, List, Any

_SECTION_PATTERNS: Dict[str, List[re.Pattern]] = {
    "contact": [
        re.compile(r"contact(\s+information|\s+details)?", re.IGNORECASE),
        re.compile(r"personal\s+information", re.IGNORECASE),
    ],
    "summary": [
        re.compile(r"(professional\s+)?(summary|profile|objective|about\s+me)", re.IGNORECASE),
        re.compile(r"career\s+(objective|summary|profile)", re.IGNORECASE),
    ],
    "experience": [
        re.compile(r"(work|professional|employment|job)?\s*experience", re.IGNORECASE),
        re.compile(r"work\s+history", re.IGNORECASE),
    ],
    "education": [
        re.compile(r"education(\s+and\s+training)?", re.IGNORECASE),
        re.compile(r"academic\s+(background|qualifications)", re.IGNORECASE),
        re.compile(r"qualifications", re.IGNORECASE),
    ],
    "skills": [
        re.compile(r"(technical\s+)?(skills?|competencies|expertise|proficiencies)", re.IGNORECASE),
        re.compile(r"core\s+competencies", re.IGNORECASE),
    ],
    "projects": [
        re.compile(r"(personal\s+|side\s+|open.?source\s+)?projects?", re.IGNORECASE),
        re.compile(r"portfolio", re.IGNORECASE),
    ],
    "certifications": [
        re.compile(r"certifications?", re.IGNORECASE),
        re.compile(r"certificates?", re.IGNORECASE),
        re.compile(r"licenses?\s+and\s+certifications?", re.IGNORECASE),
    ],
    "awards": [
        re.compile(r"awards?(\s+and\s+honors?)?", re.IGNORECASE),
        re.compile(r"honors?(\s+and\s+awards?)?", re.IGNORECASE),
        re.compile(r"achievements?", re.IGNORECASE),
    ],
    "publications": [
        re.compile(r"publications?", re.IGNORECASE),
        re.compile(r"research(\s+papers?)?", re.IGNORECASE),
    ],
    "languages": [
        re.compile(r"languages?(\s+spoken)?", re.IGNORECASE),
    ],
    "volunteer": [
        re.compile(r"volunteer(\s+experience)?", re.IGNORECASE),
        re.compile(r"community\s+service", re.IGNORECASE),
    ],
    "interests": [
        re.compile(r"interests?", re.IGNORECASE),
        re.compile(r"hobbies?", re.IGNORECASE),
    ],
}

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s./0-9]{6,14}[0-9]")
_URL_RE = re.compile(
    r"https?://[^\s]+"
    r"|www\.[^\s]+"
    r"|linkedin\.com/in/[^\s]+"
    r"|github\.com/[^\s]+"
    r"|[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?"
)

_ALLOWED_PLATFORMS = (
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "linkedin.com",
    "kaggle.com",
    "huggingface.co",
    "behance.net",
)
_SPAM_TLDS = (".xyz", ".top", ".click")

_DEGREE_PATTERNS = [
    re.compile(r"\b(B\.?S\.?|B\.?E\.?|B\.?Tech\.?|Bachelor(?:\'?s)?(?:\s+of\s+\w+)?)\b", re.IGNORECASE),
    re.compile(r"\b(M\.?S\.?|M\.?E\.?|M\.?Tech\.?|Master(?:\'?s)?(?:\s+of\s+\w+)?)\b", re.IGNORECASE),
    re.compile(r"\b(Ph\.?D\.?|Doctorate)\b", re.IGNORECASE),
    re.compile(r"\b(M\.?B\.?A\.?)\b", re.IGNORECASE),
    re.compile(r"\b(Associate(?:\'?s)?(?:\s+degree)?)\b", re.IGNORECASE),
    re.compile(r"\b(High\s+School\s+Diploma|GED)\b", re.IGNORECASE),
    re.compile(r"\b(A\.?A\.?|A\.?S\.?)\b"),
]

_ACTION_VERBS = {
    "achieved", "accelerated", "architected", "automated", "built", "collaborated",
    "coordinated", "created", "delivered", "deployed", "designed", "developed",
    "drove", "enabled", "engineered", "enhanced", "established", "executed",
    "expanded", "facilitated", "generated", "implemented", "improved", "increased",
    "initiated", "integrated", "launched", "led", "managed", "mentored", "migrated",
    "modernized", "optimized", "orchestrated", "oversaw", "partnered", "pioneered",
    "prioritized", "produced", "reduced", "refactored", "resolved", "scaled",
    "shipped", "simplified", "spearheaded", "streamlined", "transformed", "unified",
}

_QUANTIFIED_RE = re.compile(
    r"(?:"
    r"\d+\s*%"
    r"|\d+x\b"
    r"|\d+\s*(?:million|billion|thousand|k\b|M\b)"
    r"|\$\d+"
    r"|(?:reduced|increased|improved|grew|decreased|saved|generated|processed)\s+(?:by\s+)?\d+"
    r"|\d+\s*(?:users|customers|clients|engineers|teams?|systems?|services?|requests?|transactions?|repos?)"
    r")",
    re.IGNORECASE,
)


def is_valid_portfolio_link(url: str) -> bool:
    clean = url.lower().strip().rstrip(".,;:!?)'\"")
    clean = re.sub(r"^https?://", "", clean)
    clean = re.sub(r"^www\.", "", clean)
    host = clean.split("/")[0].split("?")[0].split(":")[0]
    if not host or "@" in host:
        return False
    if any(host == p or host.endswith("." + p) for p in _ALLOWED_PLATFORMS):
        return True
    if any(host.endswith(tld) for tld in _SPAM_TLDS):
        return False
    parts = host.split(".")
    if len(parts) >= 2 and len(parts[-1]) >= 2:
        return True
    return False


def detect_sections(text: str) -> Dict[str, bool]:
    result: Dict[str, bool] = {key: False for key in _SECTION_PATTERNS}
    for section_key, patterns in _SECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                result[section_key] = True
                break
    return result


def extract_links(text: str) -> List[str]:
    raw_urls = _URL_RE.findall(text)
    valid = set()
    for u in raw_urls:
        cleaned = u.strip().rstrip(".,;:!?)'\"")
        if is_valid_portfolio_link(cleaned):
            valid.add(cleaned)
    return sorted(list(valid))


def extract_contact_info(text: str) -> Dict[str, Any]:
    emails = _EMAIL_RE.findall(text)
    phones = _PHONE_RE.findall(text)
    urls = extract_links(text)
    return {
        "emails": list(set(emails)),
        "phones": list(set(phones)),
        "urls": urls,
    }


def count_words(text: str) -> int:
    return len(text.split())


def extract_degree_mentions(text: str) -> List[str]:
    found = set()
    for pattern in _DEGREE_PATTERNS:
        for m in pattern.finditer(text):
            found.add(m.group(0).strip())
    return sorted(found)


def count_action_verbs(text: str) -> int:
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    return sum(1 for w in words if w.lower() in _ACTION_VERBS)


def count_quantified_achievements(text: str) -> int:
    return len(_QUANTIFIED_RE.findall(text))


def estimate_years_of_experience(text: str) -> int:
    patterns = [
        re.compile(r"(\d+)\+?\s+years?\s+of\s+experience", re.IGNORECASE),
        re.compile(r"(\d+)\+?\s+years?\s+experience", re.IGNORECASE),
        re.compile(r"over\s+(\d+)\s+years?", re.IGNORECASE),
    ]
    years_found = []
    for p in patterns:
        for m in p.finditer(text):
            try:
                val = int(m.group(1))
                if 0 < val < 50:
                    years_found.append(val)
            except (ValueError, IndexError):
                pass
    if years_found:
        return max(years_found)
    date_re = re.compile(r"\b((?:19|20)\d{2})\b")
    years = [int(m) for m in date_re.findall(text)]
    if len(years) >= 2:
        span = max(years) - min(years)
        if 0 < span < 50:
            return span
    return 0


def analyze_resume_text(text: str) -> Dict[str, Any]:
    sections = detect_sections(text)
    contact = extract_contact_info(text)
    word_count = count_words(text)
    estimated_exp = estimate_years_of_experience(text)
    links = extract_links(text)
    degrees = extract_degree_mentions(text)
    action_verb_count = count_action_verbs(text)
    quantified_count = count_quantified_achievements(text)
    return {
        "sections": sections,
        "contact": contact,
        "word_count": word_count,
        "estimated_years_of_experience": estimated_exp,
        "links": links,
        "degree_mentions": degrees,
        "action_verb_count": action_verb_count,
        "quantified_achievement_count": quantified_count,
    }
