import os
import sys
import re
from dotenv import dotenv_values
from google import genai
from google.genai import types as genai_types


def mask_secrets(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, "[REDACTED]")


def main():
    env_vars = dotenv_values(".env") if os.path.exists(".env") else {}
    api_key = os.getenv("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY", "")
    api_key = api_key.strip()

    if not api_key:
        print("GEMINI_API_KEY is unset in .env", flush=True)
        sys.exit(1)

    try:
        client = genai.Client(api_key=api_key)
        all_models = list(client.models.list())
    except Exception as exc:
        err_msg = mask_secrets(str(exc), api_key)
        print(f"Listing models failed with {exc.__class__.__name__}: {err_msg}", flush=True)
        sys.exit(1)

    gen_models = []
    for m in all_models:
        actions = getattr(m, "supported_actions", []) or []
        if "generateContent" in actions:
            clean_name = m.name
            if clean_name.startswith("models/"):
                clean_name = clean_name[len("models/"):]
            gen_models.append(clean_name)

    excluded_keywords = [
        "image", "tts", "transcribe", "lyria", "robotics",
        "computer-use", "antigravity", "deep-research", "nano-banana", "omni"
    ]
    included_keywords = ["flash", "flash-lite", "pro", "gemma"]

    text_models = []
    for m in gen_models:
        lower = m.lower()
        if any(ex in lower for ex in excluded_keywords):
            continue
        if any(inc in lower for inc in included_keywords):
            text_models.append(m)

    print(f"Filtered {len(text_models)} candidate text models to probe:", flush=True)
    for m in text_models:
        print(f"- {m}", flush=True)
    print("\nProbing each text model with prompt 'Reply with the single word OK' (15s timeout)...", flush=True)

    results_by_outcome = {}
    working_models = []

    for model_name in text_models:
        try:
            http_opts = genai_types.HttpOptions(timeout=15000)
            test_client = genai.Client(api_key=api_key, http_options=http_opts)
            resp = test_client.models.generate_content(
                model=model_name,
                contents="Reply with the single word OK",
            )
            reply = resp.text.strip().replace("\n", " ") if resp.text else "OK"
            print(f"{model_name} | OK | {reply[:120]}", flush=True)
            working_models.append(model_name)
            results_by_outcome.setdefault("OK", []).append(model_name)
        except Exception as exc:
            err_str = mask_secrets(str(exc), api_key).replace("\n", " ")
            status_match = re.search(r"\b(4\d\d)\b", err_str)
            http_code = status_match.group(1) if status_match else exc.__class__.__name__

            msg_match = re.search(r"'message':\s*'([^']+)'", err_str)
            if msg_match:
                clean_msg = msg_match.group(1)
            else:
                clean_msg = err_str

            print(f"{model_name} | {http_code} | {clean_msg[:120]}", flush=True)
            results_by_outcome.setdefault(http_code, []).append((model_name, clean_msg[:120]))

    print("\n=== SUMMARY TABLE GROUPED BY RESULT ===", flush=True)
    for outcome, items in results_by_outcome.items():
        print(f"\nResult: {outcome} ({len(items)} models)", flush=True)
        if outcome == "OK":
            for m in items:
                print(f"  - {m}", flush=True)
        else:
            for m, msg in items:
                print(f"  - {m}: {msg}", flush=True)

    if working_models:
        print(f"\nWORKING_MODELS={','.join(working_models)}", flush=True)
    else:
        print("\nWORKING_MODELS=NONE", flush=True)


if __name__ == "__main__":
    main()
