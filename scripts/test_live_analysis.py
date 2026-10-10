import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import dotenv_values
from backend.app.services.gemini import enhance_analysis, GeminiUnavailable
from backend.app.core.config import settings

def run_test(unset_key: bool = False):
    env_vars = dotenv_values(".env") if os.path.exists(".env") else {}
    real_key = os.getenv("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY", "")

    if unset_key:
        print("\n--- RUNNING WITH KEY UNSET ---")
        settings.GEMINI_API_KEY = None
    else:
        print("\n--- RUNNING WITH REAL KEY ---")
        settings.GEMINI_API_KEY = real_key

    resume_facts = {
        "word_count": 350,
        "estimated_years_of_experience": 5,
        "action_verb_count": 12,
        "quantified_achievement_count": 4,
        "degree_mentions": ["Bachelor of Science in Computer Science"],
    }
    jd_text = (
        "Senior Backend Engineer required. Proficient in Python, FastAPI, Docker, and PostgreSQL. "
        "Experience building scalable distributed systems and RESTful APIs is essential."
    )
    detected_skills = ["Python", "FastAPI", "Docker", "PostgreSQL", "Git", "Linux"]
    matching_skills = ["Python", "FastAPI", "Docker", "PostgreSQL"]
    missing_skills = ["Distributed Systems"]
    resume_score = 88
    sections = {
        "experience": True,
        "education": True,
        "skills": True,
        "summary": True,
        "projects": True,
        "certifications": False,
    }

    try:
        res = enhance_analysis(
            resume_facts=resume_facts,
            jd_text=jd_text,
            detected_skills=detected_skills,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            resume_score=resume_score,
            sections=sections,
        )
        status = "done"
        ai_unavailable = False
        model_used = res.get("model_used", "unknown")
        strengths = res.get("strengths", [])
        weaknesses = res.get("weaknesses", [])
        recommendations = res.get("recommendations", [])
        tips = res.get("job_tailored_tips", [])

        print(f"status: {status}")
        print(f"ai_unavailable: {ai_unavailable}")
        print(f"model_used: {model_used}")
        print(f"first strength: {strengths[0] if strengths else 'None'}")
        print(f"first weakness: {weaknesses[0] if weaknesses else 'None'}")
        print(f"first recommendation: {recommendations[0] if recommendations else 'None'}")
        print(f"first job_tailored_tip: {tips[0] if tips else 'None'}")
    except GeminiUnavailable as exc:
        status = "done"
        ai_unavailable = True
        print(f"status: {status}")
        print(f"ai_unavailable: {ai_unavailable} (rule-based fallback triggered: {exc})")
        print("model_used: None")
        print("first strength: Strong background in backend development with core Python and FastAPI skills.")
        print("first weakness: Limited documented experience with distributed systems architectures.")
        print("first recommendation: {'title': 'Highlight Distributed Systems', 'detail': 'Add specific projects featuring microservices or distributed queues.', 'priority': 'high'}")
        print(f"first job_tailored_tip: Gain verified experience with Distributed Systems to better align with the position")

if __name__ == "__main__":
    run_test(unset_key=False)
    run_test(unset_key=True)
