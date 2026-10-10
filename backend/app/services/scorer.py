from typing import List, Dict, Any


_SECTION_WEIGHTS: Dict[str, int] = {
    "contact": 5,
    "summary": 10,
    "experience": 25,
    "education": 15,
    "skills": 20,
    "projects": 10,
    "certifications": 5,
    "awards": 3,
    "publications": 2,
    "languages": 2,
    "volunteer": 2,
    "interests": 1,
}

_OPTIMAL_WORD_COUNT_LOW = 300
_OPTIMAL_WORD_COUNT_HIGH = 800
_WORD_COUNT_MAX_SCORE = 5

_SKILLS_BONUS_THRESHOLDS = [(20, 15), (10, 10), (5, 6), (2, 3), (0, 0)]
_EXP_SCORE_TABLE = [(10, 15), (5, 10), (2, 5), (1, 3), (0, 0)]
_ACTION_VERB_THRESHOLDS = [(10, 5), (5, 3), (2, 1), (0, 0)]
_QUANTIFIED_THRESHOLDS = [(5, 5), (2, 3), (1, 1), (0, 0)]


def _section_score(sections: Dict[str, bool]) -> int:
    total = sum(
        _SECTION_WEIGHTS.get(section, 1)
        for section, present in sections.items()
        if present
    )
    return min(total, 45)


def _word_count_score(word_count: int) -> int:
    if _OPTIMAL_WORD_COUNT_LOW <= word_count <= _OPTIMAL_WORD_COUNT_HIGH:
        return _WORD_COUNT_MAX_SCORE
    if word_count < _OPTIMAL_WORD_COUNT_LOW:
        ratio = word_count / _OPTIMAL_WORD_COUNT_LOW
        return max(0, round(ratio * _WORD_COUNT_MAX_SCORE))
    ratio = _OPTIMAL_WORD_COUNT_HIGH / word_count
    return max(1, round(ratio * _WORD_COUNT_MAX_SCORE))


def _skills_score(skill_count: int) -> int:
    for threshold, score in _SKILLS_BONUS_THRESHOLDS:
        if skill_count > threshold:
            return score
    return 0


def _experience_score(years: int) -> int:
    for threshold, score in _EXP_SCORE_TABLE:
        if years >= threshold:
            return score
    return 0


def _contact_score(contact: Dict[str, Any]) -> int:
    score = 0
    if contact.get("emails"):
        score += 5
    if contact.get("phones"):
        score += 3
    if contact.get("urls"):
        score += 2
    return min(score, 10)


def _action_verb_score(count: int) -> int:
    for threshold, score in _ACTION_VERB_THRESHOLDS:
        if count > threshold:
            return score
    return 0


def _quantified_score(count: int) -> int:
    for threshold, score in _QUANTIFIED_THRESHOLDS:
        if count >= threshold:
            return score
    return 0


def score_resume(
    sections: Dict[str, bool],
    detected_skills: List[str],
    contact: Dict[str, Any],
    word_count: int,
    estimated_years_of_experience: int,
    action_verb_count: int = 0,
    quantified_achievement_count: int = 0,
) -> int:
    total = 0
    total += _section_score(sections)
    total += _word_count_score(word_count)
    total += _skills_score(len(detected_skills))
    total += _experience_score(estimated_years_of_experience)
    total += _contact_score(contact)
    total += _action_verb_score(action_verb_count)
    total += _quantified_score(quantified_achievement_count)
    return min(max(total, 0), 100)


def generate_strengths(
    sections: Dict[str, bool],
    detected_skills: List[str],
    estimated_years_of_experience: int,
    matching_skills: List[str],
    action_verb_count: int = 0,
    quantified_achievement_count: int = 0,
) -> List[str]:
    strengths = []
    if sections.get("experience"):
        if estimated_years_of_experience >= 5:
            strengths.append(
                f"Strong professional background with {estimated_years_of_experience}+ years of experience"
            )
        elif estimated_years_of_experience >= 2:
            strengths.append("Solid work experience included in the resume")
    if len(detected_skills) >= 10:
        strengths.append(
            f"Diverse technical skill set with {len(detected_skills)} identified skills"
        )
    elif len(detected_skills) >= 5:
        strengths.append("Relevant technical skills clearly demonstrated")
    if matching_skills:
        strengths.append(
            f"Good alignment with job requirements: {', '.join(matching_skills[:5])}"
        )
    if sections.get("projects"):
        strengths.append("Portfolio of projects demonstrates practical application of skills")
    if sections.get("certifications"):
        strengths.append("Professional certifications validate technical expertise")
    if sections.get("education"):
        strengths.append("Formal education credentials included")
    if quantified_achievement_count >= 3:
        strengths.append(
            f"Resume includes {quantified_achievement_count} quantified achievements — strong evidence of impact"
        )
    if action_verb_count >= 8:
        strengths.append("Strong use of action verbs conveys initiative and ownership")
    return strengths[:6]


def generate_weaknesses(
    sections: Dict[str, bool],
    word_count: int,
    contact: Dict[str, Any],
    missing_skills: List[str],
    action_verb_count: int = 0,
    quantified_achievement_count: int = 0,
) -> List[str]:
    weaknesses = []
    if not sections.get("summary"):
        weaknesses.append("No professional summary or objective statement found")
    if not contact.get("emails"):
        weaknesses.append("Email address not detected — ensure contact info is clearly visible")
    if not contact.get("phones"):
        weaknesses.append("Phone number not found — add contact details for recruiters")
    if word_count < 200:
        weaknesses.append(
            "Resume appears too brief — consider adding more detail about experience and achievements"
        )
    elif word_count > 1200:
        weaknesses.append(
            "Resume may be too lengthy — aim for conciseness to hold recruiter attention"
        )
    if missing_skills:
        weaknesses.append(f"Missing skills required by the job: {', '.join(missing_skills[:5])}")
    if not sections.get("experience"):
        weaknesses.append("No work experience section detected")
    if quantified_achievement_count == 0:
        weaknesses.append("No quantified achievements found — add metrics like percentages, revenue, or scale")
    if action_verb_count < 3:
        weaknesses.append("Few action verbs detected — use strong verbs like 'built', 'led', 'optimized'")
    return weaknesses[:6]


def generate_recommendations(
    sections: Dict[str, bool],
    detected_skills: List[str],
    missing_skills: List[str],
    word_count: int,
    contact: Dict[str, Any],
    resume_score: int,
    quantified_achievement_count: int = 0,
) -> List[Dict[str, str]]:
    recommendations = []

    if not sections.get("summary"):
        recommendations.append({
            "title": "Add a Professional Summary",
            "detail": "Include a 2-4 sentence summary at the top highlighting your key skills, experience, and career goals.",
            "priority": "high",
        })

    if missing_skills:
        recommendations.append({
            "title": "Acquire Missing Skills",
            "detail": f"The job requires: {', '.join(missing_skills[:5])}. Consider online courses or projects to demonstrate these.",
            "priority": "high",
        })

    if quantified_achievement_count == 0:
        recommendations.append({
            "title": "Add Quantified Achievements",
            "detail": "Quantify your impact with numbers: 'Reduced latency by 40%', 'Managed team of 8', 'Scaled service to 1M users'.",
            "priority": "high",
        })

    if not contact.get("urls"):
        recommendations.append({
            "title": "Add LinkedIn or GitHub Profile",
            "detail": "Include your LinkedIn and/or GitHub URL to showcase your professional network and code portfolio.",
            "priority": "medium",
        })

    if not sections.get("projects"):
        recommendations.append({
            "title": "Add a Projects Section",
            "detail": "Include 2-4 relevant projects with descriptions of your role, technologies used, and measurable outcomes.",
            "priority": "medium",
        })

    if word_count < 300:
        recommendations.append({
            "title": "Expand Resume Content",
            "detail": "Add detail about job responsibilities, achievements, and quantifiable results to reach 300-800 words.",
            "priority": "high",
        })

    if len(detected_skills) < 5:
        recommendations.append({
            "title": "List Technical Skills Explicitly",
            "detail": "Add a dedicated skills section listing programming languages, frameworks, tools, and technologies.",
            "priority": "high",
        })

    if not sections.get("certifications") and resume_score < 70:
        recommendations.append({
            "title": "Consider Adding Certifications",
            "detail": "Relevant certifications (AWS, Google Cloud, etc.) can significantly strengthen your resume.",
            "priority": "low",
        })

    if not sections.get("education"):
        recommendations.append({
            "title": "Include Education Details",
            "detail": "Add your educational background including degree, institution, and graduation year.",
            "priority": "medium",
        })

    return recommendations[:6]
