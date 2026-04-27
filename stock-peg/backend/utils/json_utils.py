"""JSON utilities for handling datetime and other non-serializable types"""
from datetime import datetime
from typing import Any, Dict


def serialize_for_json(obj: Any) -> Any:
    """Recursively convert datetime objects to ISO format strings
    
    Args:
        obj: Object to serialize (can be dict, list, datetime, or primitive type)
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj


def model_to_json_dict(model) -> Dict[str, Any]:
    """Convert Pydantic model to JSON-serializable dict
    
    Args:
        model: Pydantic model instance
        
    Returns:
        Dict with datetime objects converted to ISO strings
    """
    if hasattr(model, 'model_dump'):
        # Pydantic v2
        return model.model_dump(mode='json')
    elif hasattr(model, 'dict'):
        # Pydantic v1
        return serialize_for_json(model.dict())
    else:
        raise ValueError(f"Object {type(model)} is not a Pydantic model")
