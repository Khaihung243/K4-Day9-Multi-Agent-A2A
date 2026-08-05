import os
import json
import time
import threading
import urllib.request
import urllib.error

def load_env():
    """Load key-value pairs from .env file into os.environ if present."""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and val:
                        os.environ[key] = val

_llm_lock = threading.Lock()
_last_request_time = 0.0

def rate_limit_pacing(min_delay_seconds=0.7):
    """Optimized pacing delay to maximize execution speed while respecting Groq API limits."""
    global _last_request_time
    with _llm_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < min_delay_seconds:
            time.sleep(min_delay_seconds - elapsed)
        _last_request_time = time.time()

class LLMClient:
    """Client wrapper for calling Groq / OpenAI compatible API with llama-3.1-8b-instant."""
    def __init__(self, model_name="llama-3.1-8b-instant"):
        load_env()
        self.model_name = model_name
        self.api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def chat_completion(self, system_prompt, user_prompt, temperature=0.1, max_retries=5):
        if not self.api_key or self.api_key.startswith("gsk_your_"):
            return {
                "status": "offline_mode",
                "content": f"[Offline Mode: Groq API Key missing] Processed prompt for model {self.model_name}"
            }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        for attempt in range(max_retries):
            # Fast pacing delay (0.7s)
            rate_limit_pacing(min_delay_seconds=0.7)

            try:
                req = urllib.request.Request(
                    self.api_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    content = result["choices"][0]["message"]["content"]
                    return {
                        "status": "success",
                        "content": content,
                        "usage": result.get("usage", {})
                    }
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8", errors="ignore")
                if e.code == 429: # Rate limit hit
                    backoff = 2 * (attempt + 1)
                    time.sleep(backoff)
                    continue
                return {
                    "status": "error",
                    "error": f"HTTP {e.code}: {error_body}",
                    "content": None
                }
            except Exception as e:
                backoff = 2 * (attempt + 1)
                time.sleep(backoff)
                if attempt == max_retries - 1:
                    return {
                        "status": "error",
                        "error": str(e),
                        "content": None
                    }

        return {
            "status": "error",
            "error": "Max retries exceeded (Rate limit 429)",
            "content": None
        }
