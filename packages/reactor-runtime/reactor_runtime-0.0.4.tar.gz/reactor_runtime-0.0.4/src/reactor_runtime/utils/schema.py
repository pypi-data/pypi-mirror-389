from typing import Dict, Any, Type
from pydantic import BaseModel

def simplify_schema(model: Type[BaseModel]) -> Dict[str, Any]:
	# Get the raw JSON Schema from Pydantic
	raw_schema = model.model_json_schema()

	# Pull only the properties and required keys
	properties = raw_schema.get("properties", {})
	required = set(raw_schema.get("required", []))

	# Build cleaned schema
	schema: Dict[str, Any] = {}
	for name, details in properties.items():
		# Copy all constraints exactly as-is
		field_schema = {k: v for k, v in details.items() if k != "title"}

		# Mark required if needed
		if name in required:
			field_schema["required"] = True

		schema[name] = field_schema

	return schema
