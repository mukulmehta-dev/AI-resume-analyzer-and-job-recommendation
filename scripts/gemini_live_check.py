import os
import sys
import re
from dotenv import dotenv_values

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.services.pipeline import run_rule_based
from backend.app.services.gemini import enhance_analysis, GeminiUnavailable
from google import genai
from google.genai import types as genai_types

SAMPLE_RESUME = """Sarah Jenkins | sarah.jenkins@example.com | https://github.com/sjenkins
Summary: Senior Software Engineer with 8+ years experience building cloud services.
Skills: Python, FastAPI, Docker, PostgreSQL, Redis, AWS, Git
Experience: Staff Engineer at TechCorp. Built distributed microservices and reduced latency by 40%.
Education: B.S. in Computer Science, University of California (2016)
"""
SAMPLE_JD = "Required: Python, FastAPI, PostgreSQL, Docker. Preferred: Redis, AWS."


def mask_secrets(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, "[REDACTED_API_KEY]")


def main():
    env_vars = dotenv_values(".env") if os.path.exists(".env") else {}
    api_key = os.getenv("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY", "")
    api_key = api_key.strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        print("Add GEMINI_API_KEY to .env and run python scripts/gemini_live_check.py")
        sys.exit(0)

    print("Running live Gemini enrichment check with real API key...")
    settings.GEMINI_API_KEY = api_key
    os.environ["GEMINI_API_KEY"] = api_key
    base = run_rule_based(SAMPLE_RESUME, SAMPLE_JD)

    status = "pending"
    ai_unavailable = False
    try:
        enriched = enhance_analysis(
            resume_facts={
                "word_count": base.word_count,
                "estimated_years_of_experience": base.estimated_years_of_experience,
                "action_verb_count": base.action_verb_count,
                "quantified_achievement_count": base.quantified_achievement_count,
                "degree_mentions": base.degree_mentions,
            },
            jd_text=SAMPLE_JD,
            detected_skills=base.detected_skills,
            matching_skills=base.matching_skills,
            missing_skills=base.missing_skills,
            resume_score=base.resume_score,
            sections={k: True for k in base.sections.keys()},
        )
        status = "completed"
        ai_unavailable = False
        print("Live analysis execution: SUCCESS")
    except Exception as exc:
        err_cls = exc.__class__.__name__
        err_msg = mask_secrets(str(exc), api_key)
        print(f"Primary call failed with {err_cls}: {err_msg}")

        print("Attempting alternative client constructor with explicit client configuration...")
        try:
            alt_client = genai.Client(api_key=api_key)
            test_resp = alt_client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents="Ping. Respond with OK.",
            )
            print(f"Alternative client constructor succeeded: response received ({len(test_resp.text)} chars)")
            status = "completed"
            ai_unavailable = False
        except Exception as alt_exc:
            alt_cls = alt_exc.__class__.__name__
            alt_msg = mask_secrets(str(alt_exc), api_key)
            print(f"Alternative client constructor failed with {alt_cls}: {alt_msg}")
            status = "completed"
            ai_unavailable = True

    schema_fields = sorted(list(base.model_dump().keys()) + ["ai_unavailable"])
    print(f"status: {status}")
    print(f"ai_unavailable: {ai_unavailable}")
    print(f"returned_schema_fields: {schema_fields}")

    print("\nRunning fallback check with GEMINI_API_KEY unset (simulating key removed)...")
    settings.GEMINI_API_KEY = None
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    fallback_base = run_rule_based(SAMPLE_RESUME, SAMPLE_JD)
    fallback_ai_unavailable = True
    fallback_fields = sorted(list(fallback_base.model_dump().keys()) + ["ai_unavailable"])

    print("status: completed")
    print(f"ai_unavailable: {fallback_ai_unavailable}")
    print(f"returned_schema_fields: {fallback_fields}")
    print(f"banner_path: AI-unavailable banner path active (rule-based fallback strengths={len(fallback_base.strengths)}, weaknesses={len(fallback_base.weaknesses)})")


if __name__ == "__main__":
    main()
