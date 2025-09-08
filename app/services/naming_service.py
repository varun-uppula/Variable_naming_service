import json
import os
import re

# Make sure imports work when script is run directly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.models.database import SessionLocal, VariableName
from app.services.llm_abbreviator import get_abbreviation_from_llm

import json
import os
from app.services.llm_abbreviator import get_abbreviation_from_llm

class NamingService:
    def __init__(self, format: str = "abs", standard: str = "autosar"):
        self.format = format
        self.standard = standard

        self.base_path = os.path.join(os.getcwd(), f"data/naming_conventions/{self.format}")
        self.config = self._load_json("format.json")

        self.fields = self.config["fields"]
        self.template = self.config["template"]
        self.mappings = self._load_all_mappings()

        # Load abbreviations for the given standard
        self.abbreviation = self._load_abbreviation()

    def _load_json(self, relative_path: str):
        full_path = os.path.join(self.base_path, relative_path)
        with open(full_path, "r") as f:
            return json.load(f)

    def _load_all_mappings(self):
        mappings = {}
        for field in self.fields:
            file_path = os.path.join(self.base_path, f"{field}s.json")
            if os.path.exists(file_path):
                mappings[field] = self._load_json(f"{field}s.json")
        return mappings

    def _load_abbreviation(self, standard: str = None):
        """Load abbreviation from the JSON file for the selected standard"""
        # If no standard is passed, use the default one (self.standard)
        standard = standard or self.standard

        if "description" not in self.fields:
            return {}

        abbr_path = os.path.join(os.getcwd(), f"data/standards/{standard}/abbreviation.json")
        
        
        if os.path.exists(abbr_path):
            with open(abbr_path, "r") as f:
                return {k.lower(): v for k, v in json.load(f).items()}
        
        print(f"Abbreviation file for {standard} not found.")
        return {}

    def _save_abbreviation(self):
        """Save the updated abbreviation to the JSON file"""
        abbr_path = os.path.join(os.getcwd(), f"data/standards/{self.standard}/pending.json")
        with open(abbr_path, "w") as f:
            json.dump(self.abbreviation, f, indent=4)

    def generate_variable_name(self, **kwargs):
        # Optionally accept a standard to override the default one
        standard = kwargs.get('standard', self.standard)
        self.abbreviation = self._load_abbreviation(standard)

        values = {}

        for field in self.fields:
            user_input = kwargs.get(field, "")

            if field == "description":
                tokens = user_input.split()
                abbr_tokens = []

                for token in tokens:
                    token_lower = token.lower()
                    # Check local abbreviation dict first
                    abbr = self.abbreviation.get(token_lower)

                    if abbr:
                        # Use local dictionary abbreviation
                        abbr_tokens.append(abbr)
                    else:
                        # If not found, use LLM abbreviation and cache it
                        print("searching for", token_lower)
                        abbr = get_abbreviation_from_llm(token_lower)
                        self.abbreviation[token_lower] = abbr
                        abbr_tokens.append(abbr)
                        # Save the new abbreviation to the file
                        self._save_abbreviation()  # This will write the updated dict to the file

                # Join all abbreviation with no spaces (or choose your delimiter)
                values[field] = "".join(abbr_tokens)

            else:
                mapping = self.mappings.get(field, {})
                values[field] = mapping.get(user_input, user_input)

        return self.template.format(**values)

    def check_existing(self, name: str):
        db = SessionLocal()
        existing = db.query(VariableName).filter(VariableName.name == name).first()
        db.close()
        return existing

    def save_variable(self, name: str, standard: str, **kwargs):
        db = SessionLocal()
        var = VariableName(
            name=name,
            description=kwargs.get("description", ""),
            module_key=kwargs.get("module", ""),
            dtype_key=kwargs.get("data_type", ""),
            dsize_key=kwargs.get("data_size", ""),
            unit_key=kwargs.get("unit", ""),
            standard=standard,
        )
        db.add(var)
        db.commit()
        db.refresh(var)
        db.close()
        return var
