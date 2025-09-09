from fastapi import APIRouter, Query, HTTPException, Request
from app.services.naming_service import NamingService
import os
import json
from pydantic import BaseModel
from typing import Dict

# -----------------------------
# Request Models
# -----------------------------
class AbsVariableInput(BaseModel):
    module: str
    data_type: str
    data_size: str
    unit: str 
    description: str

class GenerateRequest(BaseModel):
    format: str
    standard: str
    fields: Dict[str, str]

class ApproveRequest(BaseModel):
    approvals: Dict[str, str]  # { "word": "abbr", ... }

# -----------------------------
# Router Init
# -----------------------------
router = APIRouter()

# -----------------------------
# Helpers
# -----------------------------
def load_json(path: str):
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# -----------------------------
# Formats & Standards
# -----------------------------
@router.get("/formats")
def get_formats():
    """Return all available formats and their required fields."""
    base_path = os.path.join(os.getcwd(), "data/naming_conventions")
    formats = {}
    for fmt in os.listdir(base_path):
        fmt_path = os.path.join(base_path, fmt, "format.json")
        if os.path.exists(fmt_path):
            with open(fmt_path, "r") as f:
                config = json.load(f)
            formats[fmt] = config.get("fields", [])
    return formats

@router.get("/standards")
def get_standards():
    """Return all available standards."""
    base_path = os.path.join(os.getcwd(), "data/standards")
    if not os.path.exists(base_path):
        return {"standards": []}
    return {"standards": os.listdir(base_path)}

# -----------------------------
# Variable Name Generation
# -----------------------------
@router.get("/fields/{format}")
def get_format_fields(format: str):
    base_path = os.path.join(os.getcwd(), f"data/naming_conventions/{format}")

    format_path = os.path.join(base_path, "format.json")
    if not os.path.exists(format_path):
        raise HTTPException(status_code=404, detail="Format not found")

    # Load format.json (expects keys: fields, template)
    with open(format_path, "r") as f:
        format_config = json.load(f)

    fields = format_config.get("fields", [])
    response = {}

    for field in fields:
        # For each field, try to load options from corresponding JSON file
        options_file = os.path.join(base_path, f"{field}s.json")  # e.g., modules.json, data_types.json
        if os.path.exists(options_file):
            with open(options_file, "r") as f:
                options_data = json.load(f)
            response[field] = {
                "type": "select",
                "options": list(options_data.keys())
            }
        else:
            response[field] = {
                "type": "string",
                "description": f"Enter {field}"
            }

    return {"format": format, "fields": response}

@router.post("/generate-variable-name/{format}/{standard}")
async def generate_variable_name(format: str, standard: str, request: Request):
    try:
        user_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input format. Must be JSON.")

    service = NamingService(format=format, standard=standard)

    try:
        variable_name = service.generate_variable_name(**user_data)
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field: {e}")

    if not service.check_existing(variable_name):
        service.save_variable(name=variable_name, standard=standard, **user_data)

    return {"variable_name": variable_name}

@router.post("/generate-variable-name/abs/autosar")
def generate_variable_name_abs_autosar(input_data: AbsVariableInput):
    service = NamingService(format="abs", standard="autosar")
    
    variable_name = service.generate_variable_name(
        module=input_data.module,
        data_type=input_data.data_type,
        data_size=input_data.data_size,
        unit=input_data.unit,
        description=input_data.description,
    )
    
    return {"variable_name": variable_name}

# -----------------------------
# Abbreviation Review & Approval
# -----------------------------
@router.get("/abbreviations/pending/{standard}")
def get_pending_abbreviations(standard: str):
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    return load_json(pending_path)

@router.post("/abbreviations/approve/{standard}")
def approve_abbreviation(standard: str, word: str, abbr: str):
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    approved_path = os.path.join(os.getcwd(), f"data/standards/{standard}/abbreviations.json")

    pending = load_json(pending_path)
    approved = load_json(approved_path)

    if word in pending and pending[word] == abbr:
        approved[word] = abbr
        del pending[word]
        save_json(approved_path, approved)
        save_json(pending_path, pending)
        return {"status": "approved", "word": word, "abbr": abbr}

    raise HTTPException(status_code=404, detail="Word not found in pending list")

@router.post("/abbreviations/approve-multiple/{standard}")
def approve_multiple_abbreviations(standard: str, req: ApproveRequest):
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    approved_path = os.path.join(os.getcwd(), f"data/standards/{standard}/abbreviations.json")

    pending = load_json(pending_path)
    approved = load_json(approved_path)

    approved_items = {}
    for word, abbr in req.approvals.items():
        if word in pending and pending[word] == abbr:
            approved[word] = abbr
            approved_items[word] = abbr
            del pending[word]

    save_json(approved_path, approved)
    save_json(pending_path, pending)

    return {"status": "approved_multiple", "approved": approved_items}

@router.post("/abbreviations/reject/{standard}")
def reject_abbreviation(standard: str, word: str):
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    pending = load_json(pending_path)

    if word in pending:
        del pending[word]
        save_json(pending_path, pending)
        return {"status": "rejected", "word": word}

    raise HTTPException(status_code=404, detail="Word not found in pending list")
