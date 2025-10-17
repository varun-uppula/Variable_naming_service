# app/api/routes.py
from fastapi import APIRouter, Query, HTTPException, Request, Body
from app.services.naming_service import NamingService
from app.services.maab_validator import MaabValidator
import os
import json
from pydantic import BaseModel
from typing import Dict, List, Optional
from fastapi.responses import FileResponse,JSONResponse
# Request Models
# -----------------------------
class AbsVariableInput(BaseModel):
    module: str
    data_type: str
    data_size: str
    unit: str 
    description: str

class NameInput(BaseModel):
    name: str

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

@router.get("/fields/{format}")
def get_format_fields(format: str):
    base_path = os.path.join(os.getcwd(), f"data/naming_conventions/{format}")

    format_path = os.path.join(base_path, "format.json")
    if not os.path.exists(format_path):
        raise HTTPException(status_code=404, detail="Format not found")

    with open(format_path, "r") as f:
        format_config = json.load(f)

    fields = format_config.get("fields", [])
    response = {}

    for field in fields:
        options_file = os.path.join(base_path, f"{field}s.json")
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


# -----------------------------
# Variable Name Generation
# -----------------------------
@router.post("/generate-variable-name/{format}/{standard}")
async def gen_var_name(format: str, standard: str, request: Request):
    try:
        user_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input format. Must be JSON.")

    service = NamingService(format=format, standard=standard)

    try:
        variable_name = service.gen_var_name(**user_data)
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field: {e}")

    # Save to pending.json for this standard
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    pending = load_json(pending_path)
    pending[variable_name] = user_data.get("description", "")
    save_json(pending_path, pending)

    return {"variable_name": variable_name, "status": "pending"}


# -----------------------------
# Admin: Approval (JSON-based)
# -----------------------------
@router.get("/pending/{standard}")
def get_pending_variables(standard: str):
    """Return all variables awaiting approval"""
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    return load_json(pending_path)


@router.post("/admin/actions/{standard}")
async def admin_actions(
    standard: str,
    data: dict = Body(...)
):
    variables = data.get("variables", [])
    action = data.get("action", "")

    service = NamingService(standard=standard)

    if action == "approve":
        approved_items = service._approve_pending_abbreviations(standard, variables)
        if approved_items:
            return {"status": "approved", "approved": approved_items}
        else:
            return {"status": "error", "message": "No variables approved"}

    elif action == "delete":
        service._delete_pending_abbreviations(standard, variables)
        return {"status": "deleted", "deleted": variables}

    else:
        return {"status": "error", "message": "Invalid action"}
    


# -----------------------------
# MAAB Validation Routes
# -----------------------------

# 1. List available components


@router.get("/components")
def get_components():
    """Load components dynamically from components.json"""
    base_path = os.path.join(os.getcwd(), "data", "maab")
    components_path = os.path.join(base_path, "components.json")

    if not os.path.exists(components_path):
        raise HTTPException(status_code=404, detail="components.json not found")

    try:
        with open(components_path, "r") as f:
            components = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading components: {e}")

    return JSONResponse(content={"standards": components})

# 3. Validate a name for a given component
@router.post("/validate/{component}")
def validate_name(component: str, body: NameInput):
    """Validate name based on MAAB rules for the selected component."""
    name = body.name

    try:
        validator = MaabValidator(component)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No rules found for component '{component}'")

    results = validator.validate(name)
    return {
        "component": component,
        "name": name,
        "results": results
    }

