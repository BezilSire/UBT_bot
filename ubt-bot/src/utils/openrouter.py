import os
import openai

def get_openrouter_response(prompt, model="openchat/openchat-7b-v3.2"):
    """
    Gets a response from the OpenRouter API.
    """
    openai.api_key = os.environ.get("OPENROUTER_API_KEY")
    openai.api_base = "https://openrouter.ai/api/v1"

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
