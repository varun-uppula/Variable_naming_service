import json
import re

import os
from app.models.database import SessionLocal, VariableName
from app.services.llm_abbreviator import get_abbreviation_from_llm

class NamingService:

    # Add this at the top, right after class definition
    STOPWORDS = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves","used","in",    "of", "for", "with", "from", "to", "by", "on", "in", "at", "as", "into", "over", 
    "under", "between", "through", "via", "about", "per", "within", "without", "along", 
    "across", "among", "behind", "against", "toward", "up", "down", "around", "near", 
    "inside", "outside"    "of", "for", "with", "from", "to", "by", "on", "in", "at", "as", "into", "over", 
    "under", "between", "through", "via", "about", "per", "within", "without", "along", 
    "across", "among", "behind", "against", "toward", "up", "down", "around", "near", 
    "inside", "outside",
    "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having","of", "for", "with", "from", "to", "by", "on", "in", "at", "as", "into", "over", 
    "under", "between", "through", "via", "about", "per", "within", "without", "along", 
    "across", "among", "behind", "against", "toward", "up", "down", "around", "near", 
    "inside", "outside"   
    ]

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


    def _add_new_abbreviations(self, standard: str, new_abbrs: dict):
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



    def _approve_abbreviations(self, standard: str, to_approve: list):
        """
        Move entries from pending.json to abbreviation.json (approved),
        then delete those entries from pending.json
        """
        pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
        approved_path = os.path.join(os.getcwd(), f"data/standards/{standard}/abbreviation.json")

        # Load pending
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                try:
                    pending = json.load(f)
                except json.JSONDecodeError:
                    pending = {}
        else:
            pending = {}

        # Load approved
        if os.path.exists(approved_path):
            with open(approved_path, "r") as f:
                try:
                    approved = json.load(f)
                except json.JSONDecodeError:
                    approved = {}
        else:
            approved = {}

        approved_items = {}
        updated = False

        for word in to_approve:
            if word in pending:
                approved[word] = pending[word]
                approved_items[word] = pending[word]
                del pending[word]
                updated = True

        if updated:
            # Save updated approved
            with open(approved_path, "w") as f:
                json.dump(approved, f, indent=4)

            # Save updated pending
            with open(pending_path, "w") as f:
                json.dump(pending, f, indent=4)

        return approved_items



    def _delete_pending_abbreviations(self, standard: str, to_delete: list):
        """Delete multiple entries from pending.json"""
        pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")

        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                try:
                    pending = json.load(f)
                except json.JSONDecodeError:
                    pending = {}
        else:
            pending = {}

        updated = False
        for word in to_delete:
            if word in pending:
                del pending[word]
                updated = True

        if updated:
            with open(pending_path, "w") as f:
                json.dump(pending, f, indent=4)









    def gen_var_name(self, standard: str = None, **kwargs):
        """
        Generate PascalCase variable name based on description.
        Uses known abbreviations, ignores stopwords, and generates abbreviations for unknown words.
        Compatible with your previous API call.
        """
        standard = standard or self.standard
        abbreviations = self._load_abbreviation(standard)

        values = {}

        for field in self.fields:
            user_input = kwargs.get(field, "")

            if field == "description":
                tokens = user_input.split()
                final_tokens = []
                new_abbreviations = {}

                for token in tokens:
                    token_lower = token.lower()
                    if token_lower in abbreviations:
                        abbr = abbreviations[token_lower]
                    elif token_lower in self.STOPWORDS:
                        abbr = ""  # ignore stopwords
                    else:
                        # Generate abbreviation
                        first = token_lower[0]
                        rest = re.sub(r'[aeiou]', '', token_lower[1:])
                        rest = re.sub(r'(.)\1+', r'\1', rest)  # remove repeated letters
                        abbr = (first + rest)[:4].capitalize()
                        new_abbreviations[token_lower] = abbr
                    final_tokens.append(abbr)

                final_variable = "".join([t for t in final_tokens if t])

                # Save newly generated abbreviations if needed
                if new_abbreviations:
                    self._add_new_abbreviations(standard, new_abbreviations)

                values[field] = final_variable

            else:
                mapping = self.mappings.get(field, {})
                values[field] = mapping.get(user_input, user_input)

        return self.template.format(**values)
    

