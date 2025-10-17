import os
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from app.services.maab_validator import MaabValidator

router = APIRouter(prefix="/maab", tags=["MAAB Validation"])

# 1. List available components
@router.get("/components")
def get_components():
    """Return available components with MAAB rules."""
    base_path = os.path.join(os.getcwd(), "data/maab")
    if not os.path.exists(base_path):
        return {"components": []}

    components = [
        f.replace(".json", "")
        for f in os.listdir(base_path)
        if f.endswith(".json")
    ]
    return {"components": components}


# 2. Input model for validation
class NameInput(BaseModel):
    name: str


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
