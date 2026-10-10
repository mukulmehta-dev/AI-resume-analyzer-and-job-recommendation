from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.services.nlp import analyze_resume_text
from backend.app.services.skills import extract_skills, get_all_skills
from backend.app.services.scorer import (
    score_resume,
    compute_section_subscores,
    generate_strengths,
    generate_weaknesses,
    generate_recommendations,
)
from backend.app.services.matcher import match_skills, compute_compatibility


class RecommendationItem(BaseModel):
    title: str
    detail: str
    priority: str = Field(pattern=r"^(high|medium|low)$")


class SkillInfo(BaseModel):
    name: str
    category: str


class PipelineResult(BaseModel):
    resume_score: int
    compatibility_score: Optional[int]
    detected_skills: List[str]
    detected_skills_with_category: List[SkillInfo]
    matching_skills: List[str]
    missing_skills: List[str]
    sections: Dict[str, Any]
    word_count: int
    estimated_years_of_experience: int
    action_verb_count: int
    quantified_achievement_count: int
    degree_mentions: List[str]
    links: List[str]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[RecommendationItem]
    summary_feedback: str = ""


def _build_skill_map() -> Dict[str, str]:
    return {s["canonical"]: s["category"] for s in get_all_skills()}


_SKILL_CATEGORY_MAP: Dict[str, str] = _build_skill_map()


def run_rule_based(
    text: str,
    job_description: Optional[str] = None,
) -> PipelineResult:
    safe_text = text if isinstance(text, str) else ""
    safe_jd = job_description if isinstance(job_description, str) and job_description.strip() else None

    try:
        nlp = analyze_resume_text(safe_text)
    except Exception:
        nlp = {
            "sections": {},
            "contact": {"emails": [], "phones": [], "urls": []},
            "word_count": 0,
            "estimated_years_of_experience": 0,
            "links": [],
            "degree_mentions": [],
            "action_verb_count": 0,
            "quantified_achievement_count": 0,
        }

    sections = nlp.get("sections", {})
    contact = nlp.get("contact", {"emails": [], "phones": [], "urls": []})
    word_count = nlp.get("word_count", 0)
    years_exp = nlp.get("estimated_years_of_experience", 0)
    action_verb_count = nlp.get("action_verb_count", 0)
    quantified_count = nlp.get("quantified_achievement_count", 0)
    degree_mentions = nlp.get("degree_mentions", [])
    links = nlp.get("links", [])

    try:
        detected_skills = extract_skills(safe_text)
    except Exception:
        detected_skills = []

    matching_skills: List[str] = []
    missing_skills: List[str] = []
    if safe_jd:
        try:
            matching_skills, missing_skills = match_skills(detected_skills, safe_jd)
        except Exception:
            matching_skills, missing_skills = [], []

    try:
        subscores = compute_section_subscores(
            sections=sections,
            detected_skills=detected_skills,
            contact=contact,
            word_count=word_count,
            estimated_years_of_experience=years_exp,
            action_verb_count=action_verb_count,
            quantified_achievement_count=quantified_count,
            degree_mentions=degree_mentions,
            links=links,
        )
        resume_score = score_resume(
            sections=sections,
            detected_skills=detected_skills,
            contact=contact,
            word_count=word_count,
            estimated_years_of_experience=years_exp,
            action_verb_count=action_verb_count,
            quantified_achievement_count=quantified_count,
            degree_mentions=degree_mentions,
            links=links,
        )
    except Exception:
        subscores = {}
        resume_score = 0

    compatibility_score: Optional[int] = None
    if safe_jd:
        try:
            compatibility_score = compute_compatibility(
                resume_text=safe_text,
                jd_text=safe_jd,
                resume_skills=detected_skills,
                matching_skills=matching_skills,
                missing_skills=missing_skills,
            )
        except Exception:
            compatibility_score = None

    try:
        strengths = generate_strengths(
            sections=sections,
            detected_skills=detected_skills,
            estimated_years_of_experience=years_exp,
            matching_skills=matching_skills,
            action_verb_count=action_verb_count,
            quantified_achievement_count=quantified_count,
        )
    except Exception:
        strengths = []

    try:
        weaknesses = generate_weaknesses(
            sections=sections,
            word_count=word_count,
            contact=contact,
            missing_skills=missing_skills,
            action_verb_count=action_verb_count,
            quantified_achievement_count=quantified_count,
        )
    except Exception:
        weaknesses = []

    try:
        raw_recs = generate_recommendations(
            sections=sections,
            detected_skills=detected_skills,
            missing_skills=missing_skills,
            word_count=word_count,
            contact=contact,
            resume_score=resume_score,
            quantified_achievement_count=quantified_count,
        )
    except Exception:
        raw_recs = []

    recommendations = [
        RecommendationItem(
            title=r.get("title", ""),
            detail=r.get("detail", ""),
            priority=r.get("priority", "medium") if r.get("priority") in ("high", "medium", "low") else "medium",
        )
        for r in raw_recs
    ]

    detected_with_category = [
        SkillInfo(name=s, category=_SKILL_CATEGORY_MAP.get(s, "other"))
        for s in detected_skills
    ]

    return PipelineResult(
        resume_score=resume_score,
        compatibility_score=compatibility_score,
        detected_skills=detected_skills,
        detected_skills_with_category=detected_with_category,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        sections=subscores,
        word_count=word_count,
        estimated_years_of_experience=years_exp,
        action_verb_count=action_verb_count,
        quantified_achievement_count=quantified_count,
        degree_mentions=degree_mentions,
        links=links,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        summary_feedback="",
    )
