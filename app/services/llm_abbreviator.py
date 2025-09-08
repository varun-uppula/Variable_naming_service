import cohere
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Access your Hugging Face API key
CO_API_KEY = os.getenv("CO_API_KEY")


co = cohere.Client(CO_API_KEY)  
def get_abbreviation_from_llm(word):
    prompt = f"""
You are an expert in generating short, human-readable abbreviations and acronyms 
for embedded automotive systems (e.g., AUTOSAR).

Input: "{word}"

Rules:
- If the word is a non-technical function word such as an article,stoping word, preposition, auxiliary verb, or pronoun 
  (e.g., of, is, the, that, it, in, on, at, with, a, an), return "" nothing.
- Do not invent or replace with another word. Only abbreviate the given input.
- If it is a compound term (camelCase, PascalCase, snake_case, or concatenated words like "stateofcharge"),
  return an acronym (e.g., "stateofcharge" → "SoC").
- If it is a single technical word then, return a short abbreviation (≤4 letters), starting with a capital letter
  (e.g., "Battery" → "Batt").
- Never return single ambiguous letters.
- Respond only with the abbreviation/acronym itself — no quotes, no explanations.
"""


    try:
        response = co.chat(
            model="command-r-plus",  # Recommended current model
            message=prompt,
            temperature=0.2,
            max_tokens=10
        )
        abbr = response.text.strip().split()[0]
        return abbr
    except Exception as e:
        print(f"Error from Cohere Chat API: {e}")
        return word






























