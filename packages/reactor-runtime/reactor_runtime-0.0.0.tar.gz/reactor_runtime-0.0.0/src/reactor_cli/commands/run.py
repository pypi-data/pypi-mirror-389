"""Run command implementation."""

import json
import os
from reactor_runtime.utils.launch import run_reactor_runtime_sync
import logging

logger = logging.getLogger(__name__)

class RunCommand:
    @staticmethod
    def register_subcommand(subparsers):
        """Register run command"""
        run_parser = subparsers.add_parser("run", help="Run reactor runtime with model from manifest.json")
        run_parser.add_argument(
            "--deploy",
            action="store_true",
            help="Run the model in a proper deployment mode."
        )
        run_parser.add_argument(
            "--debug","--headless",
            action="store_true",
            help="Run the model in a headless, debug mode."
        )
        run_parser.add_argument(
            "--host",
            type=str,
            default="0.0.0.0",
            help="Host to bind the FastAPI Server. Default: 0.0.0.0"
        )
        run_parser.add_argument(
            "--port",
            type=int,
            default=8081,
            help="FastAPI Server port. Default: 8081"
        )
        run_parser.add_argument(
            "--log-level",
            type=str,
            default="INFO",
            choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
            help="Logging level. Default: INFO"
        )
        run_parser.set_defaults(func=RunCommand)

    def __init__(self, args):
        """Initialize with parsed arguments"""
        self.args = args

    def run(self):
        """Run the reactor runtime with the model specified in manifest.json."""
        from ..main import verify_reactor_workspace

        # Verify workspace and get manifest data
        manifest_data = verify_reactor_workspace()
        if manifest_data is None:
            return

        # Extract model information from manifest
        model_class = manifest_data["class"]
        model_args = manifest_data.get("args", {})

        if "model_name" not in manifest_data.keys():
            print("Error: manifest.json is missing required 'model_name' field.")
            print("Please add a 'model_name' field specifying the model name.")
            return
        if "model_version" not in manifest_data.keys():
            print("Error: manifest.json is missing required 'model_version' field.")
            print("Please add a 'model_version' field specifying the model version.")
            return

        print(f"Starting reactor runtime...")
        print(f"Model: {model_class}")
        if model_args:
            print(f"Model args: {model_args}")

        runtime_serve_fn = None
        if self.args.deploy:
            try:
                from reactor_runtime.context._cloud.cloud_runtime import serve
                if os.getenv("REDIS_URL", None) is None:
                    raise KeyError("REDIS_URL environment variable is not set. Please set it to the Redis URL.")
                runtime_serve_fn = serve
            except KeyError as e:
                logger.error(f"Error starting reactor runtime: {e}")
                return
            except ModuleNotFoundError as e:
                logger.error("Deploy mode is not supported locally. Please use the command without --deploy.")
                return
        else:
            if self.args.debug:
                try:
                    from reactor_runtime.context.debug.debug_runtime import serve
                    runtime_serve_fn = serve
                except ModuleNotFoundError:
                    logger.error("Debug mode is not available. Please use the command without --debug/--headless.")
                    return
            else:
                from reactor_runtime.context.local.local_runtime import serve
                runtime_serve_fn = serve
        
        try:
            run_reactor_runtime_sync(
                runtime_serve_fn=runtime_serve_fn,
                model=model_class,
                model_args=json.dumps(model_args) if model_args else None,
                host=self.args.host,
                port=self.args.port,
                log_level=self.args.log_level,
                model_name=manifest_data["model_name"],
                model_version=manifest_data["model_version"],
            )

        except KeyboardInterrupt:
            print("\nReactor runtime stopped by user.")
        except Exception as e:
            print(f"Error running reactor runtime: {e}")
            raise