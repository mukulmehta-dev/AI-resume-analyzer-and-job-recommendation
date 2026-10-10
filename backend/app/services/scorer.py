from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP


def round_half_up(val: float) -> int:
    return int(Decimal(str(float(val))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


SECTION_WEIGHTS: Dict[str, float] = {
    "skills": 0.35,
    "experience": 0.20,
    "education": 0.15,
    "projects": 0.15,
    "certifications": 0.05,
    "structure": 0.10,
}


def compute_section_subscores(
    sections: Dict[str, Any],
    detected_skills: List[str],
    contact: Dict[str, Any],
    word_count: int,
    estimated_years_of_experience: int,
    action_verb_count: int = 0,
    quantified_achievement_count: int = 0,
    degree_mentions: Optional[List[str]] = None,
    links: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    skill_count = len(detected_skills)
    if skill_count >= 15:
        skill_score = 100
        skill_expl = f"Extensive skill profile with {skill_count} detected competencies."
    elif skill_count >= 10:
        skill_score = 90
        skill_expl = f"Strong skill breadth with {skill_count} detected skills."
    elif skill_count >= 6:
        skill_score = 75
        skill_expl = f"Good technical core with {skill_count} skills."
    elif skill_count >= 3:
        skill_score = 55
        skill_expl = f"Moderate skill coverage with {skill_count} skills."
    elif skill_count >= 1:
        skill_score = 30
        skill_expl = f"Limited skill presence with {skill_count} identified skill(s)."
    else:
        skill_score = 0
        skill_expl = "No industry-standard skills detected in the document."

    exp_present = bool(sections.get("experience"))
    exp_score = 0
    if exp_present:
        exp_score += 40
    if estimated_years_of_experience >= 10:
        exp_score += 30
    elif estimated_years_of_experience >= 5:
        exp_score += 25
    elif estimated_years_of_experience >= 2:
        exp_score += 15
    elif estimated_years_of_experience >= 1:
        exp_score += 10

    if action_verb_count >= 8:
        exp_score += 15
    elif action_verb_count >= 4:
        exp_score += 10
    elif action_verb_count >= 1:
        exp_score += 5

    if quantified_achievement_count >= 3:
        exp_score += 15
    elif quantified_achievement_count >= 1:
        exp_score += 10

    exp_score = min(exp_score, 100)
    exp_expl = (
        f"Work experience present with {estimated_years_of_experience}+ estimated years, "
        f"{action_verb_count} action verbs, and {quantified_achievement_count} quantified metric(s)."
        if exp_present
        else "No formal work experience section detected."
    )

    edu_present = bool(sections.get("education"))
    degrees = degree_mentions or []
    if edu_present and degrees:
        edu_score = 100
        edu_expl = f"Formal education verified with degree credential(s): {', '.join(degrees)}."
    elif edu_present:
        edu_score = 75
        edu_expl = "Education section detected without explicit degree title keywords."
    elif degrees:
        edu_score = 50
        edu_expl = f"Degree mention(s) identified ({', '.join(degrees)}), but dedicated section is missing."
    else:
        edu_score = 0
        edu_expl = "No education section or academic degree credentials found."

    proj_present = bool(sections.get("projects"))
    url_links = links or (contact.get("urls") if contact else [])
    if proj_present and url_links:
        proj_score = 100
        proj_expl = f"Project section present with {len(url_links)} portfolio/repository link(s)."
    elif proj_present:
        proj_score = 80
        proj_expl = "Projects section identified with demonstrable deliverables."
    elif url_links:
        proj_score = 40
        proj_expl = "Portfolio links detected without dedicated projects header."
    else:
        proj_score = 0
        proj_expl = "No project portfolio or code repositories referenced."

    cert_present = bool(sections.get("certifications"))
    cert_score = 100 if cert_present else 0
    cert_expl = (
        "Professional credentials and industry certifications validated."
        if cert_present
        else "No certifications or licensing section detected."
    )

    has_email = bool(contact and contact.get("emails"))
    has_phone = bool(contact and contact.get("phones"))
    has_urls = bool(contact and contact.get("urls"))
    has_summary = bool(sections.get("summary"))

    struct_score = 0
    if has_email:
        struct_score += 30
    if has_phone:
        struct_score += 20
    if has_urls:
        struct_score += 10
    if has_summary:
        struct_score += 20

    if 300 <= word_count <= 800:
        struct_score += 20
    elif 200 <= word_count <= 1100:
        struct_score += 10
    elif word_count > 0:
        struct_score += 5

    struct_score = min(struct_score, 100)
    struct_expl = (
        f"Document length: {word_count} words. Summary: {'present' if has_summary else 'missing'}. "
        f"Contact: {'complete' if has_email and has_phone else 'partial'}."
    )

    return {
        "skills": {
            "score": skill_score,
            "weight": SECTION_WEIGHTS["skills"],
            "explanation": skill_expl,
        },
        "experience": {
            "score": exp_score,
            "weight": SECTION_WEIGHTS["experience"],
            "explanation": exp_expl,
        },
        "education": {
            "score": edu_score,
            "weight": SECTION_WEIGHTS["education"],
            "explanation": edu_expl,
        },
        "projects": {
            "score": proj_score,
            "weight": SECTION_WEIGHTS["projects"],
            "explanation": proj_expl,
        },
        "certifications": {
            "score": cert_score,
            "weight": SECTION_WEIGHTS["certifications"],
            "explanation": cert_expl,
        },
        "structure": {
            "score": struct_score,
            "weight": SECTION_WEIGHTS["structure"],
            "explanation": struct_expl,
        },
    }


class ScoreResult(int):
    score: int
    subscores: Dict[str, Dict[str, Any]]

    def __new__(cls, score: int, subscores: Dict[str, Dict[str, Any]]):
        instance = super().__new__(cls, score)
        instance.score = score
        instance.subscores = subscores
        return instance

    def __iter__(self):
        return iter((self.score, self.subscores))


score_sections = compute_section_subscores


def score_resume(
    sections: Dict[str, Any],
    detected_skills: List[str],
    contact: Dict[str, Any],
    word_count: int,
    estimated_years_of_experience: int,
    action_verb_count: int = 0,
    quantified_achievement_count: int = 0,
    degree_mentions: Optional[List[str]] = None,
    links: Optional[List[str]] = None,
) -> ScoreResult:
    subscores = compute_section_subscores(
        sections=sections,
        detected_skills=detected_skills,
        contact=contact,
        word_count=word_count,
        estimated_years_of_experience=estimated_years_of_experience,
        action_verb_count=action_verb_count,
        quantified_achievement_count=quantified_achievement_count,
        degree_mentions=degree_mentions,
        links=links,
    )
    final_score = round_half_up(sum(item["score"] * item["weight"] for item in subscores.values()))
    return ScoreResult(final_score, subscores)


def generate_strengths(
    sections: Dict[str, Any],
    detected_skills: List[str],
    estimated_years_of_experience: int,
    matching_skills: List[str],
    action_verb_count: int = 0,
    quantified_achievement_count: int = 0,
    word_count: int = 0,
) -> List[str]:
    strengths = []
    if word_count >= 150 and len(detected_skills) >= 3:
        if sections.get("experience") and sections.get("education") and sections.get("skills"):
            strengths.append("Foundational sections complete")
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
    sections: Dict[str, Any],
    word_count: int,
    contact: Dict[str, Any],
    missing_skills: List[str],
    action_verb_count: int = 0,
    quantified_achievement_count: int = 0,
    detected_skills: Optional[List[str]] = None,
) -> List[str]:
    weaknesses = []
    if not sections.get("summary"):
        weaknesses.append("No professional summary or objective statement found")
    if not (contact and contact.get("emails")):
        weaknesses.append("Email address not detected — ensure contact info is clearly visible")
    if not (contact and contact.get("phones")):
        weaknesses.append("Phone number not found — add contact details for recruiters")
    if word_count < 200:
        weaknesses.append(
            "Resume appears too brief — consider adding more detail about experience and achievements"
        )
    elif word_count > 1200:
        weaknesses.append(
            "Resume may be too lengthy — aim for conciseness to hold recruiter attention"
        )
    if not sections.get("experience"):
        weaknesses.append("No work experience section detected")
    if detected_skills is not None and len(detected_skills) < 3:
        weaknesses.append("Very few or no technical skills detected — add a dedicated skills section")
    if not sections.get("education"):
        weaknesses.append("No formal education credentials detected")
    if missing_skills:
        weaknesses.append(f"Missing skills required by the job: {', '.join(missing_skills[:5])}")
    if quantified_achievement_count == 0:
        weaknesses.append("No quantified achievements found — add metrics like percentages, revenue, or scale")
    if action_verb_count < 3:
        weaknesses.append("Few action verbs detected — use strong verbs like 'built', 'led', 'optimized'")
    return weaknesses[:6]


def generate_recommendations(
    sections: Dict[str, Any],
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

    if not (contact and contact.get("urls")):
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
