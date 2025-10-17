import os
import json
import re

class MaabValidator:
    def __init__(self, component: str):
        self.component = component
        self.rules = self._load_rules(component)
    
    def _load_rules(self, component: str):
        path = os.path.join(os.getcwd(), f"data/maab/rules/{component}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Rules file for component '{component}' not found.")
        with open(path, "r") as f:
            return json.load(f)
    
    def validate(self, name: str) -> dict:
        results = {}
        for rule_key, rule in self.rules.items():
            if "pattern" in rule:
                # Regex validation
                match_pattern = rule.get("match", True)
                pattern = rule["pattern"]
                # Does name match the pattern?
                is_match = bool(re.search(pattern, name))
                # If rule.match==True, name should match pattern; else it should NOT match pattern
                passed = is_match == match_pattern
                results[rule_key] = {
                    "description": rule["description"],
                    "passed": passed,
                    "value": name,
                    "rule_match_expected": match_pattern,
                    "pattern": pattern
                }
            elif "function" in rule:
                # Call dedicated function
                func_name = rule["function"]
                params = rule.get("params", {})
                func = getattr(self, func_name, None)
                if func is None:
                    results[rule_key] = {
                        "description": rule["description"],
                        "passed": False,
                        "error": f"Validation function '{func_name}' not implemented."
                    }
                else:
                    passed = func(name, **params)
                    results[rule_key] = {
                        "description": rule["description"],
                        "passed": passed,
                        "value": name,
                        "params": params
                    }
            else:
                results[rule_key] = {
                    "description": rule["description"],
                    "passed": False,
                    "error": "Invalid rule format, missing pattern or function."
                }
        return results
    
    # Example validation functions:

    def validate_not_reserved_matlab_word(self, name: str) -> bool:
        reserved_words = {"end", "if", "else", "for", "while"}  # Add more or load dynamically
        return name.lower() not in reserved_words

    def validate_max_length(self, name: str, max_length: int) -> bool:
        return len(name) <= max_length

