import re
from typing import List, Tuple, Optional, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.services.skills import extract_skills
from backend.app.core.config import settings


_REQUIRED_MARKERS = re.compile(
    r"\b(required?|must\s+have?|mandatory|essential)\b",
    re.IGNORECASE,
)
_PREFERRED_MARKERS = re.compile(
    r"\b(preferred?|nice\s+to\s+have?|bonus|plus|advantageous|desired?)\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?\n])\s+")


def _classify_jd_sentences(jd_text: str) -> Tuple[str, str]:
    sentences = _SENTENCE_SPLIT.split(jd_text)
    required_parts = []
    preferred_parts = []
    for s in sentences:
        if _PREFERRED_MARKERS.search(s):
            preferred_parts.append(s)
        elif _REQUIRED_MARKERS.search(s):
            required_parts.append(s)
        else:
            required_parts.append(s)
    return " ".join(required_parts), " ".join(preferred_parts)


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        matrix = vec.fit_transform([text_a, text_b])
        score = float(cosine_similarity(matrix[0], matrix[1])[0][0])
        return round(min(max(score, 0.0), 1.0), 4)
    except Exception:
        return 0.0


def match_skills(
    resume_skills: List[str],
    jd_text: str,
) -> Tuple[List[str], List[str]]:
    required_text, preferred_text = _classify_jd_sentences(jd_text)
    required_skills = set(extract_skills(required_text))
    preferred_skills = set(extract_skills(preferred_text))
    all_jd_skills = required_skills | preferred_skills
    resume_set = set(resume_skills)
    matching = sorted(resume_set & all_jd_skills)
    missing = sorted(all_jd_skills - resume_set)
    return matching, missing


def compute_compatibility(
    resume_text: str,
    jd_text: str,
    resume_skills: List[str],
    matching_skills: List[str],
    missing_skills: List[str],
) -> Optional[int]:
    if not jd_text or not jd_text.strip():
        return None

    required_text, preferred_text = _classify_jd_sentences(jd_text)
    required_skills = set(extract_skills(required_text))
    preferred_skills = set(extract_skills(preferred_text))
    resume_set = set(resume_skills)

    required_match = len(resume_set & required_skills)
    preferred_match = len(resume_set & preferred_skills)

    required_total = len(required_skills)
    preferred_total = len(preferred_skills)

    if required_total + preferred_total == 0:
        weighted_overlap = 0.5
    else:
        required_score = (required_match / required_total) if required_total else 0.0
        preferred_score = (preferred_match / preferred_total) if preferred_total else 0.0
        weighted_overlap = (2 * required_score + 1 * preferred_score) / 3

    if settings.USE_EMBEDDINGS:
        similarity = _tfidf_similarity(resume_text, jd_text)
    else:
        similarity = _tfidf_similarity(
            " ".join(resume_skills),
            " ".join(set(extract_skills(jd_text))),
        )

    compatibility = round(100 * (0.6 * weighted_overlap + 0.4 * similarity))
    return min(max(compatibility, 0), 100)
