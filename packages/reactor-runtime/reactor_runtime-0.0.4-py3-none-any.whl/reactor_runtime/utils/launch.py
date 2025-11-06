#!/usr/bin/env python3
import asyncio
import logging
from typing import Callable, Optional

from reactor_runtime.utils.loader import add_import_paths


# Defaults
DEFAULT_APP_SPEC = "reactor_runtime._runtime.app_passthrough:PassthroughApp"


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    # Reduce noise from aiortc/av unless debugging
    if level.upper() != "DEBUG":
        logging.getLogger("aiortc").setLevel(logging.WARNING)
        logging.getLogger("av").setLevel(logging.WARNING)




async def run_reactor_runtime(
    runtime_serve_fn: Callable,
    model: str,
    model_name: str,
    model_version: str,
    model_root: Optional[str] = None,
    model_args: Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8081,
    log_level: str = "INFO"
) -> None:
    """
    Run the Cloud Runtime with the specified parameters.
    
    Args:
        model: Python import path to the VideoModel class (module:Class)
        app_root: Directory to add to sys.path for resolving the app module:Class
        model_root: Directory to add to sys.path for resolving the model module:Class
        app: Python import path to the ReactorApp class (module:Class)
        model_args: JSON object of kwargs to pass to the model constructor
        weights: Directory where model weights/checkpoints are available
        host: Host to bind the FastAPI control server
        port: FastAPI control port
        log_level: Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG)
    """
    configure_logging(log_level)

    # Add user-provided module roots for app and model resolution
    add_import_paths([model_root])


    logging.info(f"Launching Cloud Runtime with "
                 f"model={model} host={host} port={port}")

    await runtime_serve_fn(
        model_spec=model,
        model_args=model_args,
        host=host, 
        port=port,
        model_name=model_name,
        model_version=model_version
    )


def run_reactor_runtime_sync(
    runtime_serve_fn: Callable,
    model: str,
    model_name: str,
    model_version: str,
    model_root: Optional[str] = None,
    model_args: Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8081,
    log_level: str = "INFO"
) -> None:
    """
    Synchronous wrapper for run_reactor_runtime.
    
    Args:
        model: Python import path to the VideoModel class (module:Class)
        app_root: Directory to add to sys.path for resolving the app module:Class
        model_root: Directory to add to sys.path for resolving the model module:Class
        app: Python import path to the ReactorApp class (module:Class)
        model_args: JSON object of kwargs to pass to the model constructor
        weights: Directory where model weights/checkpoints are available
        host: Host to bind the FastAPI control server
        port: FastAPI control port
        log_level: Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG)
    """
    asyncio.run(run_reactor_runtime(
        runtime_serve_fn=runtime_serve_fn,
        model=model,
        model_root=model_root,
        model_args=model_args,
        model_name=model_name,
        model_version=model_version,
        host=host,
        port=port,
        log_level=log_level
    ))
