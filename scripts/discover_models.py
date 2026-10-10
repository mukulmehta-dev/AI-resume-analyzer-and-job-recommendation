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
        print("GEMINI_API_KEY is unset in .env")
        sys.exit(1)

    try:
        client = genai.Client(api_key=api_key)
        all_models = list(client.models.list())
    except Exception as exc:
        err_msg = mask_secrets(str(exc), api_key)
        print(f"Listing models failed with {exc.__class__.__name__}: {err_msg}")
        sys.exit(1)

    gen_models = []
    print("Models supporting generateContent:")
    for m in all_models:
        actions = getattr(m, "supported_actions", []) or []
        if "generateContent" in actions:
            clean_name = m.name
            if clean_name.startswith("models/"):
                clean_name = clean_name[len("models/"):]
            gen_models.append(clean_name)
            print(f"- {clean_name}")

    flash_or_lite = [m for m in gen_models if "flash" in m.lower() or "lite" in m.lower()]
    others = [m for m in gen_models if m not in flash_or_lite and not any(x in m.lower() for x in ["embedding", "imagen", "veo", "tts", "robotics"])]
    ordered_models = flash_or_lite + others

    print(f"\nTesting candidate models (timeout: 15s)...")
    succeeded_model = None
    failure_count = 0

    for model_name in ordered_models:
        try:
            http_opts = genai_types.HttpOptions(timeout=15000)
            test_client = genai.Client(api_key=api_key, http_options=http_opts)
            resp = test_client.models.generate_content(
                model=model_name,
                contents="Reply with the single word OK",
            )
            reply = resp.text.strip().replace("\n", " ") if resp.text else "OK"
            print(f"Model: {model_name} | Status: 200 SUCCESS | Response: {reply[:30]}")
            succeeded_model = model_name
            break
        except Exception as exc:
            failure_count += 1
            err_cls = exc.__class__.__name__
            err_str = mask_secrets(str(exc), api_key)
            status_match = re.search(r"(\d{3})\s+([A-Z_]+)", err_str)
            status_code = status_match.group(0) if status_match else err_cls

            clean_err = err_str.replace("\n", " ")
            if "message" in clean_err:
                msg_match = re.search(r"'message':\s*'([^']+)'", clean_err)
                if msg_match:
                    clean_err = msg_match.group(1)
            print(f"Model: {model_name} | Error: {status_code} | Message: {clean_err[:120]}")

            if failure_count >= 6:
                print("Stopped testing after 6 consecutive failures. No candidate model succeeded.")
                break

    if succeeded_model:
        print(f"\nFIRST_WORKING_MODEL={succeeded_model}")
    else:
        print("\nALL_TESTED_MODELS_FAILED")


if __name__ == "__main__":
    main()
