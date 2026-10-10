import re
from typing import List, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.services.skills import extract_skills

_REQUIRED_MARKERS = re.compile(
    r"\b(required?|must\s+have?|mandatory|essential)\b",
    re.IGNORECASE,
)
_PREFERRED_MARKERS = re.compile(
    r"\b(preferred?|nice\s+to\s+have?|bonus|plus|advantageous|desired?)\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"[\r\n]+|(?<=[.!?])\s+")


def round_half_up(val: float) -> int:
    return int(Decimal(str(float(val))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class CompatibilityResult(int):
    skill_overlap: float
    semantic_similarity: float
    normalized_similarity: float
    compatibility: int

    def __new__(cls, compatibility: int, skill_overlap: float, semantic_similarity: float, normalized_similarity: float = 0.0):
        instance = super().__new__(cls, compatibility)
        instance.compatibility = compatibility
        instance.skill_overlap = skill_overlap
        instance.semantic_similarity = semantic_similarity
        instance.normalized_similarity = normalized_similarity
        return instance

    def __iter__(self):
        return iter((self.skill_overlap, self.semantic_similarity, self.compatibility))



def _classify_jd_sentences(jd_text: str) -> Tuple[str, str]:
    sentences = _SENTENCE_SPLIT.split(jd_text)
    required_parts = []
    preferred_parts = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if _PREFERRED_MARKERS.search(s_clean):
            preferred_parts.append(s_clean)
        elif _REQUIRED_MARKERS.search(s_clean):
            required_parts.append(s_clean)
        else:
            required_parts.append(s_clean)
    return " ".join(required_parts), " ".join(preferred_parts)


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
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
) -> Optional[CompatibilityResult]:
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
        all_skills = set(extract_skills(jd_text))
        if not all_skills:
            weighted_overlap = 0.0
        else:
            weighted_overlap = len(resume_set & all_skills) / len(all_skills)
    else:
        required_score = (required_match / required_total) if required_total else 0.0
        preferred_score = (preferred_match / preferred_total) if preferred_total else 0.0
        if required_total > 0 and preferred_total > 0:
            weighted_overlap = (2 * required_score + 1 * preferred_score) / 3
        elif required_total > 0:
            weighted_overlap = required_score
        else:
            weighted_overlap = preferred_score

    similarity = _tfidf_similarity(resume_text, jd_text)

    weighted_overlap_val = round(min(max(weighted_overlap, 0.0), 1.0), 4)
    similarity_val = round(min(max(similarity, 0.0), 1.0), 4)
    normalized_similarity_val = round(min(1.0, similarity_val / 0.2), 4)
    compatibility = round_half_up(100 * (0.75 * weighted_overlap_val + 0.25 * normalized_similarity_val))
    compatibility_clamped = min(max(compatibility, 0), 100)

    return CompatibilityResult(
        compatibility=compatibility_clamped,
        skill_overlap=weighted_overlap_val,
        semantic_similarity=similarity_val,
        normalized_similarity=normalized_similarity_val,
    )
