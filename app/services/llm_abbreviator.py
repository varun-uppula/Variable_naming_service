import cohere
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()

# Access your Hugging Face API key
CO_API_KEY = os.getenv("CO_API_KEY")


co = cohere.Client(CO_API_KEY)  


def get_abbreviation_from_llm(desc, known_dict):


    prompt = f"""
You are an expert in generating short, human-readable abbreviations 
and acronyms for embedded automotive systems (e.g., AUTOSAR).

Task:
- Create a concise variable name for the description: "{desc}".
- Ignore non-technical function words (articles, stopwords, prepositions, auxiliary verbs, pronouns).
- Always use the provided known abbreviations if available.
- For unknown words, create short abbreviations (≤4 letters) or acronyms for compound words (e.g., "stateofcharge" → "SoC").
- Ensure the final variable name is readable and self-explanatory.

Known abbreviations (must be used as-is):
{json.dumps(known_dict, indent=2)}

Required Output:
Respond ONLY in valid JSON, in the following format:

{{
  "final_variable": "GeneratedVariableName",
  "new_abbreviations": {{
    "word1": "abbr1",
    "word2": "abbr2"
  }}
}}
"""


    prompt1 = f"""
You are an expert in generating short, human-readable abbreviations and acronyms 
for embedded automotive systems (e.g., AUTOSAR).

Input description: "{desc}"

Rules:
- Ignore non-technical function words such as articles, stop words, prepositions, auxiliary verbs, and pronouns 
  (e.g., of, is, the, that, it, in, on, at, with, a, an).
- For compound technical terms (e.g., "stateofcharge"), generate an acronym (e.g., "SoC").
- For single technical words, generate a short abbreviation (max 4 letters) 
  (e.g., "Battery" → "Batt", "Controller" → "Ctrl").
- Combine these acronyms and abbreviations into a single shortened version that is **readable and self-explanatory**, 
  not just initials. Example: "Battery Management System" → "BattMgmtSys".
- The final result should be concise (max 12 characters), camel-case style, and easy to understand.
- Never output plain acronyms of every word (like "BMS" or "BVS") unless that is the common industry standard.
- Respond only with the final shortened version — no quotes, no explanations.
"""



    prompt1 = f"""
You are an expert in generating short, human-readable abbreviations and acronyms 
for embedded automotive systems (e.g., AUTOSAR).

Input: "{desc}"

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
            model="command-r-plus",
            message=prompt,
            temperature=0.2,
            max_tokens=100
        )

        # Clean and parse JSON
        text = response.text.strip()
        data = json.loads(text)
        final_variable = data.get("final_variable", "")
        new_abbreviations = data.get("new_abbreviations", {})

        return final_variable, new_abbreviations

    except Exception as e:
        print(f"Error from Cohere Chat API: {e}")
        return None, {}



'''       response = co.chat(
            model="command-r-plus",  # Recommended current model
            message=prompt,
            temperature=0.2,
            max_tokens=20
        )
        abbr = response.text.strip().split()[0]
        return abbr
    except Exception as e:
        print(f"Error from Cohere Chat API: {e}")
        return word
'''





























