import importlib
import inspect
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Type

from reactor_runtime.model_api import VideoModel

logger = logging.getLogger(__name__)


def add_import_paths(paths: List[str]) -> None:
    """
    Prepend provided directories to sys.path if they exist.
    """
    for p in paths:
        if not p:
            continue
        ap = os.path.abspath(p)
        if os.path.isdir(ap) and ap not in sys.path:
            sys.path.insert(0, ap)
            logger.info(f"Added to sys.path: {ap}")


def parse_spec(spec: str) -> Tuple[str, str]:
    """
    Parse a 'module:ClassName' string into (module, class_name).
    """
    if not spec or ":" not in spec:
        raise ValueError(f"Invalid spec '{spec}'. Expected 'module:ClassName'.")
    module, class_name = spec.split(":", 1)
    module = module.strip()
    class_name = class_name.strip()
    if not module or not class_name:
        raise ValueError(f"Invalid spec '{spec}'. Expected 'module:ClassName'.")
    return module, class_name


def load_class(spec: str) -> type:
    """
    Dynamically import and return a class from 'module:ClassName'.
    Automatically adds the current working directory to sys.path (since reactor run 
    requires manifest.json to be in the current directory).
    """
    module_name, class_name = parse_spec(spec)
    
    # Add current working directory to sys.path (where manifest.json is located)
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
        logger.info(f"Added current directory to sys.path: {cwd}")
    
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Module '{module_name}' not found in current directory '{cwd}'") from e
    
    try:
        cls = getattr(module, class_name)
    except AttributeError:
        raise ImportError(f"Class '{class_name}' not found in module '{module_name}'")
    if not inspect.isclass(cls):
        raise TypeError(f"'{class_name}' in module '{module_name}' is not a class")
    return cls


def build_model(model_spec: str, model_args_json: dict) -> VideoModel:
    """
    Instantiate a VideoModel from spec and constructor kwargs.
    """
    cls = load_class(model_spec)
    if not issubclass(cls, VideoModel):
        raise TypeError(f"Loaded class '{cls.__name__}' is not a subclass of VideoModel")

    kwargs: Dict[str, Any] = {}
    if model_args_json:
        kwargs.update(model_args_json)
    try:
        instance = cls(**kwargs)  # type: ignore[arg-type]
    except TypeError as e:
        raise TypeError(f"Failed constructing model '{cls.__name__}' with kwargs {kwargs}: {e}") from e

    return instance


