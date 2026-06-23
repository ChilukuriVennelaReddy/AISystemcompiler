import os
import json
import httpx
from typing import Optional, Dict, Any

class LLMClient:
    @staticmethod
    def generate_json(system_instruction: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        if gemini_key:
            return LLMClient.call_gemini(gemini_key, system_instruction, user_prompt)
        elif openai_key:
            return LLMClient.call_openai(openai_key, system_instruction, user_prompt)
        return None

    @staticmethod
    def call_gemini(api_key: str, system_instruction: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_instruction}\n\nUser Input/Context:\n{user_prompt}"
                }]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if response.status_code != 200:
                    print(f"[LLM WARNING] Gemini HTTP Error: {response.status_code} - {response.text}")
                    return None
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            print(f"[LLM WARNING] Gemini exception: {str(e)}")
            return None

    @staticmethod
    def call_openai(api_key: str, system_instruction: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url, 
                    json=payload, 
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    }
                )
                if response.status_code != 200:
                    print(f"[LLM WARNING] OpenAI HTTP Error: {response.status_code} - {response.text}")
                    return None
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return json.loads(text)
        except Exception as e:
            print(f"[LLM WARNING] OpenAI exception: {str(e)}")
            return None
