from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json

# Load Mistral 3B locally
MODEL_NAME = "/home/navpc24/Desktop/llm-finetuning/Mistral-3B-Instruct-v0.2-init"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Load model with automatic device mapping to avoid OOM
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    dtype=torch.float16,      # FP16 to reduce memory
    device_map="auto"         # Automatically split model across GPU + CPU
)

# LLM call function
def get_abbreviation_from_llm(desc, known_dict):
    prompt = f"""
You are an expert in generating consistent, short, human-readable variable names for embedded automotive systems (e.g., AUTOSAR).

Your task is to:
- Create a PascalCase variable name for the following description: "{desc}".
- Ignore non-technical or functional language such as:
  - Articles (a, an, the)
  - Prepositions (of, for, with)
  - Generic descriptors (number, array, signal, module, value, data, info)
  - Functional/control terms (calculate, compute, read, write, send, receive, check, detect, process, monitor, control)
- DO NOT replace words with synonyms.
- DO NOT invent acronyms unless explicitly listed in the known abbreviations.
- Each technical word must be reduced to a short abbreviation (1–4 letters) by truncating or slightly shortening the word.
- The final variable must be a direct concatenation of these abbreviations in PascalCase.

⚠️ Consistency rules:
- "final_variable" MUST be built only from abbreviations listed in:
  1. the known abbreviations dictionary, OR
  2. the "new_abbreviations" dictionary.
- Every entry in "new_abbreviations" MUST appear in "final_variable" exactly as written.
- No synonyms or reinterpretations are allowed.

Known abbreviations (must be used exactly as-is):
{json.dumps(known_dict, indent=2)}

Expected Output:
Respond ONLY in valid JSON format:

{{
  "final_variable": "GeneratedVariableName",
  "new_abbreviations": {{}}
}}
"""

    # Tokenize and send inputs to same device as model
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=True,
            temperature=0.3,
            top_p=0.9
        )

    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\n====== RAW MODEL OUTPUT ======")
    print(raw_output)
    print("=================================\n")

    # Extract first JSON object
    def extract_first_json(text):
        brace_count = 0
        start = None
        for i, char in enumerate(text):
            if char == '{':
                if start is None:
                    start = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start is not None:
                    return text[start:i + 1]
        return None

    clean_json_str = extract_first_json(raw_output)
    if not clean_json_str:
        raise ValueError("No valid JSON object found in model response.")

    clean_json_str = clean_json_str.strip()
    print(f"Extracted JSON (length {len(clean_json_str)}):\n{repr(clean_json_str)}")

    data = json.loads(clean_json_str)

    final_variable = data.get("final_variable", "")
    new_abbreviations = data.get("new_abbreviations", {})

    return final_variable, new_abbreviations


# Example usage
if __name__ == "__main__":
    final_var, new_abbr = get_abbreviation_from_llm(
        "Positive Contactor Stuck Open",
        {"management": "Mgmt"}
    )
    print("Final Variable:", final_var)
    print("New Abbreviations:", new_abbr)
