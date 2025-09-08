from fastapi import APIRouter, Query, HTTPException, Request
from app.services.naming_service import NamingService
import os
import json
from pydantic import BaseModel


class AbsVariableInput(BaseModel):
    module: str
    data_type: str
    data_size: str
    unit: str 
    description: str
# init naming service with "autosar" for now, can be dynamic
naming_service = NamingService(standard="autosar")
service = NamingService(format="abs", standard="autosar")

router = APIRouter()

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
            # Provide options for dropdown/select fields
            response[field] = {
                "type": "select",
                "options": list(options_data.keys())
            }
        else:
            # If no options file, treat as free text input
            response[field] = {
                "type": "string",
                "description": f"Enter {field}"
            }

    return {"format": format, "fields": response}

@router.post("/generate-variable-name/{format}/{standard}")
async def generate_variable_name(format: str, standard: str, request: Request):
    try:
        # Get user-submitted data (query params or body as JSON)
        user_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input format. Must be JSON.")

    # Initialize naming service with selected format and standard
    service = NamingService(format=format, standard=standard)

    # Generate the variable name
    try:
        variable_name = service.generate_variable_name(**user_data)
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field: {e}")

    # Optional: Save it in DB if not already there
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