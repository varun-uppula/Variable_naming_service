import json
import os
from app.models.database import SessionLocal, VariableName
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


    def _load_abbreviation(self, standard: str):
        """Load abbreviation from the JSON file for the selected standard"""
        abbr_path = os.path.join(os.getcwd(), f"data/standards/{standard}/abbreviation.json")
        if os.path.exists(abbr_path):
            with open(abbr_path, "r") as f:
                return {k.lower(): v for k, v in json.load(f).items()}
        return {}


    def _save_pending_abbreviations(self, standard: str, new_abbrs: dict):
        """Append multiple newly generated LLM entries to pending.json as key-value pairs"""
        pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")

        # Load existing pending entries
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                try:
                    pending = json.load(f)
                except json.JSONDecodeError:
                    pending = {}
        else:
            pending = {}

        # Add only entries that are not already present
        updated = False
        for word, abbr in new_abbrs.items():
            if word not in pending:
                pending[word] = abbr
                updated = True

        # Save only if something new was added
        if updated:
            with open(pending_path, "w") as f:
                json.dump(pending, f, indent=4)


    def generate_variable_name(self, standard: str = None, **kwargs):
        standard = standard or self.standard
        abbreviations = self._load_abbreviation(standard)

        values = {}

        for field in self.fields:
            user_input = kwargs.get(field, "")

            if field == "description":
                # Step 1: Split into words
                tokens = user_input.split()

                # Step 2: Collect known abbreviations
                known_dict = {}
                for token in tokens:
                    token_lower = token.lower()
                    if token_lower in abbreviations:
                        known_dict[token_lower] = abbreviations[token_lower]

                # Step 3: Call LLM with description + known_dict
                final_variable, new_abbrs = get_abbreviation_from_llm(user_input, known_dict)

                # Step 4: Save newly generated ones to pending.json
                if new_abbrs:
                    self._save_pending_abbreviations(standard, new_abbrs)

                values[field] = final_variable

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
