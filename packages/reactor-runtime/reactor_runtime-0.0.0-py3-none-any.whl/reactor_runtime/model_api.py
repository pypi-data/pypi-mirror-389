from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, get_type_hints
from pydantic import BaseModel, create_model
import json
import os
import inspect
from reactor_runtime.utils.schema import simplify_schema
from reactor_cli.utils import get_weights
import numpy as np

#This section is used for declaration and storage of annotated commands.
#Annotated commands are registered to this registry, which stores each command and their declared capabilities.
command_registry: Dict[str, Dict] = {}


def _create_pydantic_model_from_signature(func: Callable, command_name: str) -> Type[BaseModel]:
	"""Create a Pydantic model from a function signature with type annotations."""
	sig = inspect.signature(func)
	type_hints = get_type_hints(func)
	
	fields = {}
	for param_name, param in sig.parameters.items():
		# Skip 'self' parameter
		if param_name == 'self':
			continue
			
		param_type = type_hints.get(param_name, Any)
		
		# Handle default values - check if it's a Pydantic Field
		if param.default != inspect.Parameter.empty:
			if hasattr(param.default, '__class__') and param.default.__class__.__name__ == 'FieldInfo':
				# This is a Pydantic Field() - use it directly
				fields[param_name] = (param_type, param.default)
			else:
				# Regular default value
				fields[param_name] = (param_type, param.default)
		else:
			# Required parameter
			fields[param_name] = (param_type, ...)
	
	# Create dynamic Pydantic model
	model_name = f"{command_name.title()}CommandModel"
	return create_model(model_name, **fields)


def command(name: str, description: str = ""):
	"""Decorator for defining commands on VideoModel methods with automatic schema generation."""
	def decorator(func: Callable):
		if not (inspect.isfunction(func) or inspect.ismethod(func)):
			raise ValueError(f"@command can only decorate methods, got {type(func)}")
		
		pydantic_model = _create_pydantic_model_from_signature(func, name)
		command_registry[name] = {
			"model": pydantic_model,
			"description": description,
			"handler": func
		}
		return func
	return decorator


class VideoModel(ABC):
	"""
	A model that PRODUCES video frames and accepts command messages.

	Runtime contract:
	  - The runtime will call `start(ctx, emit_frame)` in a background task.
	  - The model should repeatedly call: `await emit_frame(frame)` to push frames.
	  - The model should return from `start` only when stopped or on error.
	  - The runtime may call `send(command, data)` at any time to control the model.
	  - The runtime will call `stop()` on session teardown.

	Notes:
	  - `frame` should be a NumPy ndarray (H, W, 3) in RGB.
	"""

	name: str = "video-model"
	_manifest_cache: Optional[Dict[str, Any]] = None

	@staticmethod
	def manifest() -> Dict[str, Any]:
		"""
		Load and return the manifest.json file from the current execution directory.
		
		Like package.json in Node.js, manifest.json defines the model configuration:
		- Model location and entry point
		- Required runtime arguments
		- Runtime version requirements
		- Future extensibility for additional metadata
		
		The manifest is loaded once and cached for subsequent calls.
		"""
		if VideoModel._manifest_cache is not None:
			return VideoModel._manifest_cache
		
		manifest_path = os.path.join(os.getcwd(), "manifest.json")
		try:
			with open(manifest_path, "r", encoding="utf-8") as f:
				VideoModel._manifest_cache = json.load(f)
				return VideoModel._manifest_cache
		except FileNotFoundError:
			raise FileNotFoundError(f"manifest.json not found at {manifest_path}")
		except json.JSONDecodeError as e:
			raise ValueError(f"Invalid JSON in manifest.json: {e}")

	@abstractmethod
	def start_session(self) -> None:
		"""
		Start producing frames and invoke `await emit_frame(frame)` for each frame.
		This method should return when the model is stopped.
		This method should NOT load from memory the model, but instead should take the already
		existing model reference (loaded in __init__) and run it.
		"""
		raise NotImplementedError

	def on_frame(self, frame: np.ndarray):
		"""
		Called for each frame arriving to the model from the client stream.
		"""
		pass

	def send(self, cmd_name: str, args: Optional[dict] = None):
		"""Dispatch a command to the model using the decorator-based command system."""
		if cmd_name not in command_registry:
			raise ValueError(f"Unknown command: {cmd_name}")

		cmd = command_registry[cmd_name]
		model_cls = cmd["model"]
		handler = cmd["handler"]

		# Validate arguments using the Pydantic model
		if args is None:
			args = {}
		validated_obj = model_cls(**args)

		# Extract validated values as kwargs
		validated_kwargs = {
			k: getattr(validated_obj, k) 
			for k in validated_obj.model_fields.keys()
		}
		
		# Call the method with validated arguments
		result = handler(self, **validated_kwargs)
		
		return result

	def commands(self) -> dict:
		"""
		This method is used to retrieve the model commands dynamically. It returns a simple schema with
		all the commands and the arguments they accept.
		"""
		return {
			"commands": {
				name: {
					"description": meta["description"],
					"schema": simplify_schema(meta["model"])
				}
				for name, meta in command_registry.items()
			}
		}

	@staticmethod
	def weights(weight: str) -> Path:
		"""
		Returns the path to the weights for the model. If a weight is not present, it will return None for that weight.
		"""
		weights_list = VideoModel.manifest()["weights"] or []
		if weight not in weights_list:
			weights_list_str = "\n- " + "\n- ".join(weights_list)
			logging.info(f"Available weights:\n {weights_list_str}")
			raise ValueError(f"Weight {weight} not found in manifest. Please ensure all the weights used by the model are listed in the manifest.json file.")
		
		result = get_weights(weight)
		logging.debug(f"Weight {weight} found at {result}")
		return result
