import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


_SKILLS_PATH = Path(__file__).parent.parent / "data" / "skills.json"


def _load_skills() -> List[Dict[str, Any]]:
    with open(_SKILLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_SKILLS: List[Dict[str, Any]] = _load_skills()

_SHORT_NAMES: Dict[str, str] = {
    "go": "Go",
    "r": "R",
    "c": "C",
}

_SHORT_CONTEXT_PATTERNS: Dict[str, List[re.Pattern]] = {
    "go": [
        re.compile(r"\bGo\s+language\b", re.IGNORECASE),
        re.compile(r"\bGolang\b", re.IGNORECASE),
        re.compile(r"\bwrote?\s+in\s+Go\b", re.IGNORECASE),
        re.compile(r"\bGo\s+(?:developer|programming|services?|microservices?|backend|code|project)\b", re.IGNORECASE),
        re.compile(r"(?:skills?|experience|expert|proficient|using)\s*:?\s*(?:[A-Za-z,\s]*\s)?Go\b"),
    ],
    "r": [
        re.compile(r"\bR\s+programming\b", re.IGNORECASE),
        re.compile(r"\bR\s+language\b", re.IGNORECASE),
        re.compile(r"\bstatistical\s+analysis\s+(?:using\s+)?R\b", re.IGNORECASE),
        re.compile(r"\busing\s+R\b", re.IGNORECASE),
        re.compile(r"\bR\s+(?:package|script|studio|markdown|shiny|ggplot|tidyverse|cran)\b", re.IGNORECASE),
        re.compile(r"(?:skills?|experience|expert|proficient)\s*:?\s*(?:[A-Za-z,\s]*,\s*)?R(?:\s*,|\s*$)", re.MULTILINE),
    ],
    "c": [
        re.compile(r"\bC\s+language\b", re.IGNORECASE),
        re.compile(r"\bC\s+programming\b", re.IGNORECASE),
        re.compile(r"\bwritten\s+in\s+C\b", re.IGNORECASE),
        re.compile(r"\bembedded\s+C\b", re.IGNORECASE),
        re.compile(r"\bC\s+(?:code|project|library|compiler|standard)\b", re.IGNORECASE),
        re.compile(r"(?:skills?|experience|expert|proficient)\s*:?\s*(?:[A-Za-z+#,\s]*,\s*)?C(?:\s*,|\s*$)", re.MULTILINE),
    ],
}

_SKILLS_SECTION_RE = re.compile(
    r"(?:technical\s+)?skills?(?:\s+section)?[\s\S]{0,2000}",
    re.IGNORECASE,
)


def _extract_skills_section(text: str) -> Optional[str]:
    m = _SKILLS_SECTION_RE.search(text)
    return m.group(0) if m else None


def _make_pattern(canonical: str, aliases: List[str]) -> re.Pattern:
    terms = [canonical] + aliases
    escaped = sorted([re.escape(t) for t in terms], key=len, reverse=True)
    inner = "|".join(escaped)
    return re.compile(
        r"(?<![a-zA-Z0-9_])(" + inner + r")(?![a-zA-Z0-9_])",
        re.IGNORECASE,
    )


_COMPILED: List[tuple] = []
for _skill in _SKILLS:
    _c = _skill["canonical"]
    _a = _skill["aliases"]
    if _c.lower() in _SHORT_NAMES:
        continue
    _terms = [_c] + _a
    _escaped = sorted([re.escape(t) for t in _terms], key=len, reverse=True)
    _inner = "|".join(_escaped)
    _pat = re.compile(
        r"(?<![a-zA-Z0-9_])(" + _inner + r")(?![a-zA-Z0-9_])",
        re.IGNORECASE,
    )
    _COMPILED.append((_pat, _skill))


def _match_short_name(text: str, key: str) -> bool:
    for pat in _SHORT_CONTEXT_PATTERNS[key]:
        if pat.search(text):
            return True
    return False


def extract_skills(text: str) -> List[str]:
    found: set = set()
    for pattern, skill in _COMPILED:
        if pattern.search(text):
            found.add(skill["canonical"])
    for key, canonical in _SHORT_NAMES.items():
        if _match_short_name(text, key):
            found.add(canonical)
    return sorted(found)


def get_all_skills() -> List[Dict[str, Any]]:
    return [
        {"canonical": s["canonical"], "category": s["category"]}
        for s in _SKILLS
    ]
