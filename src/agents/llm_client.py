import os
import json
import urllib.request
import urllib.error

class LLMClient:
    """Client wrapper for calling Groq / OpenAI compatible API with llama-3.1-8b-instant."""
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.model_name = model_name
        self.api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def chat_completion(self, system_prompt, user_prompt, temperature=0.1):
        if not self.api_key or self.api_key.startswith("gsk_your_"):
            # Fallback mock/offline indicator if key not set
            return {
                "status": "offline_mode",
                "content": f"[Offline Mode: Groq API Key missing] Processed prompt for model {self.model_name}"
            }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
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
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "content": None
            }
