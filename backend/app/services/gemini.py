import json
import logging
import re
import time
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel, ValidationError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_CACHED_AUTO_MODEL: Optional[str] = None


class GeminiUnavailable(Exception):
    pass


class _GeminiRecommendation(BaseModel):
    title: str
    detail: str
    priority: str = "medium"


class _GeminiOutput(BaseModel):
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[_GeminiRecommendation] = []
    summary_feedback: str = ""
    job_tailored_tips: List[str] = []


_SYSTEM_PROMPT = (
    "You are an expert ATS (Applicant Tracking System) and career coach. "
    "Analyze the provided resume facts and job description objectively. "
    "Be direct, specific, and actionable. "
    "Do not invent facts. Return only the requested JSON."
)


def _sanitize_prompt_input(text: Optional[str]) -> str:
    if not text:
        return ""
    cleaned = text.replace("</JOB_DESCRIPTION>", "").replace("</RESUME_FACTS>", "")
    cleaned = cleaned.replace("<JOB_DESCRIPTION>", "").replace("<RESUME_FACTS>", "")
    return cleaned


def _build_user_prompt(
    resume_facts: Dict[str, Any],
    jd_text: Optional[str],
    detected_skills: List[str],
    matching_skills: List[str],
    missing_skills: List[str],
    resume_score: int,
    sections: Dict[str, bool],
) -> str:
    active_sections = [k for k, v in sections.items() if v]
    facts_block = json.dumps({
        "word_count": resume_facts.get("word_count", 0),
        "estimated_years_of_experience": resume_facts.get("estimated_years_of_experience", 0),
        "detected_skills": detected_skills[:30],
        "active_sections": active_sections,
        "action_verb_count": resume_facts.get("action_verb_count", 0),
        "quantified_achievement_count": resume_facts.get("quantified_achievement_count", 0),
        "degree_mentions": resume_facts.get("degree_mentions", []),
    }, indent=2)

    safe_jd = _sanitize_prompt_input(jd_text)
    jd_block = safe_jd[:2000] if safe_jd else "Not provided."

    schema = (
        '{"strengths":["string",...],'
        '"weaknesses":["string",...],'
        '"recommendations":[{"title":"string","detail":"string","priority":"high|medium|low"},...],'
        '"summary_feedback":"string",'
        '"job_tailored_tips":["string",...]}'
    )

    return (
        f"<RESUME_FACTS>\n{facts_block}\n</RESUME_FACTS>\n\n"
        f"<JOB_DESCRIPTION>\n{jd_block}\n</JOB_DESCRIPTION>\n\n"
        f"Matching skills: {', '.join(matching_skills[:20]) or 'none'}\n"
        f"Missing skills: {', '.join(missing_skills[:20]) or 'none'}\n"
        f"Resume score: {resume_score}/100\n\n"
        f"Return ONLY valid JSON matching this exact schema:\n{schema}\n\n"
        f"Rules:\n"
        f"- strengths: 3-5 specific observations\n"
        f"- weaknesses: 3-5 improvement areas\n"
        f"- recommendations: 4-6 actionable items ordered by priority\n"
        f"- summary_feedback: 2-3 sentence assessment\n"
        f"- job_tailored_tips: 2-4 concrete tips tailored to the job description\n"
        f"- Do NOT include markdown, code fences, or extra keys"
    )


def _cap_str(s: Any, max_len: int = 500) -> str:
    if not isinstance(s, str):
        s = str(s)
    return s[:max_len]


def _sanitize_gemini_output(data: Dict[str, Any]) -> Dict[str, Any]:
    allowed_keys = {"strengths", "weaknesses", "recommendations", "summary_feedback", "job_tailored_tips"}
    filtered = {k: v for k, v in data.items() if k in allowed_keys}

    raw_strengths = filtered.get("strengths") or []
    if isinstance(raw_strengths, list):
        strengths = [_cap_str(s, 500) for s in raw_strengths[:8]]
    else:
        strengths = []

    raw_weaknesses = filtered.get("weaknesses") or []
    if isinstance(raw_weaknesses, list):
        weaknesses = [_cap_str(w, 500) for w in raw_weaknesses[:8]]
    else:
        weaknesses = []

    raw_tips = filtered.get("job_tailored_tips") or []
    if isinstance(raw_tips, list):
        tips = [_cap_str(t, 500) for t in raw_tips[:8]]
    else:
        tips = []

    raw_recs = filtered.get("recommendations") or []
    recs = []
    if isinstance(raw_recs, list):
        for r in raw_recs[:8]:
            if isinstance(r, dict):
                title = _cap_str(r.get("title", ""), 500)
                detail = _cap_str(r.get("detail", ""), 500)
                priority = r.get("priority", "medium")
                if priority not in ("high", "medium", "low"):
                    priority = "medium"
                recs.append({"title": title, "detail": detail, "priority": priority, "source": "ai"})
            elif isinstance(r, str):
                recs.append({"title": _cap_str(r, 500), "detail": "", "priority": "medium", "source": "ai"})

    raw_summary = filtered.get("summary_feedback") or ""
    summary = _cap_str(raw_summary, 600)

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recs,
        "summary_feedback": summary,
        "job_tailored_tips": tips,
    }


def _parse_response(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(line for line in lines if not line.startswith("```")).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    text = text[start : end + 1]
    data = json.loads(text)
    _GeminiOutput.model_validate(data)
    return _sanitize_gemini_output(data)


def _get_candidate_text_models(client: genai.Client) -> List[str]:
    all_models = list(client.models.list())
    gen_models = []
    for m in all_models:
        actions = getattr(m, "supported_actions", []) or []
        if "generateContent" in actions:
            clean_name = m.name
            if clean_name.startswith("models/"):
                clean_name = clean_name[len("models/"):]
            gen_models.append(clean_name)
    excluded = [
        "image", "tts", "transcribe", "lyria", "robotics",
        "computer-use", "antigravity", "deep-research", "nano-banana", "omni"
    ]
    included = ["flash", "flash-lite", "pro", "gemma"]
    text_models = []
    for m in gen_models:
        lower = m.lower()
        if any(ex in lower for ex in excluded):
            continue
        if any(inc in lower for inc in included):
            text_models.append(m)
    return text_models


def resolve_auto_model(client: genai.Client) -> str:
    global _CACHED_AUTO_MODEL
    if _CACHED_AUTO_MODEL is not None:
        return _CACHED_AUTO_MODEL

    candidates = _get_candidate_text_models(client)
    for model_name in candidates:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents="Reply with the single word OK",
            )
            if resp and getattr(resp, "text", None):
                _CACHED_AUTO_MODEL = model_name
                logger.info(f"Auto-selected Gemini model: {_CACHED_AUTO_MODEL}")
                return _CACHED_AUTO_MODEL
        except Exception:
            continue

    raise GeminiUnavailable("Auto model selection failed: no working text models found")


def get_models_to_try(client: genai.Client) -> List[str]:
    configured = settings.GEMINI_MODEL.strip()
    if configured.lower() == "auto":
        auto_model = resolve_auto_model(client)
        models = [auto_model]
        if settings.GEMINI_MODEL_FALLBACKS:
            for item in settings.GEMINI_MODEL_FALLBACKS.split(","):
                fb = item.strip()
                if fb and fb not in models:
                    models.append(fb)
        return models
    return settings.candidate_gemini_models


def enhance_analysis(
    resume_facts: Dict[str, Any],
    jd_text: Optional[str],
    detected_skills: List[str],
    matching_skills: List[str],
    missing_skills: List[str],
    resume_score: int,
    sections: Dict[str, bool],
    client_factory=None,
) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise GeminiUnavailable("GEMINI_API_KEY is not configured")

    start_time = time.time()
    overall_deadline = 60.0

    if client_factory:
        client = client_factory()
    else:
        http_opts = genai_types.HttpOptions(timeout=20000)
        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options=http_opts)

    user_prompt = _build_user_prompt(
        resume_facts, jd_text, detected_skills, matching_skills, missing_skills,
        resume_score, sections,
    )

    models_to_try = get_models_to_try(client)
    last_exc: Exception = GeminiUnavailable("Unknown error")

    for model_name in models_to_try:
        if time.time() - start_time >= overall_deadline:
            raise GeminiUnavailable("Gemini request deadline exceeded (60s)")

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    genai_types.Content(
                        role="user",
                        parts=[
                            genai_types.Part(text=_SYSTEM_PROMPT + "\n\n" + user_prompt)
                        ],
                    )
                ],
                config=genai_types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                ),
            )
            raw_text = getattr(response, "text", "") or ""
            sanitized = _parse_response(raw_text)
            logger.info(f"Analysis served by Gemini model: {model_name}")
            tips = sanitized["job_tailored_tips"]
            if not tips and missing_skills:
                tips = [f"Gain verified experience with {skill} to better align with the position" for skill in missing_skills[:3]]
            return {
                "strengths": sanitized["strengths"],
                "weaknesses": sanitized["weaknesses"],
                "recommendations": sanitized["recommendations"],
                "summary_feedback": sanitized["summary_feedback"],
                "job_tailored_tips": tips,
                "model_used": model_name,
            }
        except (json.JSONDecodeError, ValidationError, KeyError) as exc:
            logger.warning(f"Gemini model {model_name} response failed parsing/schema validation: {exc}, trying next model")
            last_exc = exc
            continue
        except Exception as exc:
            last_exc = exc
            err_str = str(exc)
            code_match = re.search(r"\b([45]\d\d)\b", err_str)
            status_code = code_match.group(1) if code_match else exc.__class__.__name__
            logger.warning(f"Gemini model {model_name} failed with status {status_code}: {exc}")
            continue

    if time.time() - start_time >= overall_deadline:
        raise GeminiUnavailable("Gemini request deadline exceeded (60s)")

    raise GeminiUnavailable(f"All Gemini models failed: {last_exc}") from last_exc


def is_available() -> bool:
    return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")
