"""Run command implementation."""

import importlib
import json
from reactor_runtime.model_api import VideoModel, command
import ast
from pathlib import Path

def load_class_without_init(file_path: str, class_name: str):
	"""
	Load only the subclass definition from a Python file (without executing imports or __init__),
	recreate it with CommandBase as its parent, and call its inherited commands() method.
	All imports from the source file are detected via AST and replicated in the namespace.
	"""
	source = Path(file_path).read_text(encoding="utf-8")
	tree = ast.parse(source, filename=file_path)

	def extract_imports(tree):
		"""Return a dict of {imported_name: module_object or attribute} from the AST."""
		imports = {}

		for node in tree.body:
			if isinstance(node, ast.Import):
				for alias in node.names:
					mod_name = alias.name
					as_name = alias.asname or mod_name.split(".")[0]
					try:
						imports[as_name] = importlib.import_module(mod_name)
					except ImportError:
						pass  # Skip missing modules safely

			elif isinstance(node, ast.ImportFrom):
				if node.module is None:
					continue
				try:
					mod = importlib.import_module(node.module)
				except ImportError:
					continue
				for alias in node.names:
					as_name = alias.asname or alias.name
					if alias.name == "*":
						# Handle "from X import *" by copying all public symbols
						for name in dir(mod):
							if not name.startswith("_"):
								imports[name] = getattr(mod, name)
					else:
						try:
							imports[as_name] = getattr(mod, alias.name)
						except AttributeError:
							pass

		return imports

	# Detect and import all modules referenced in the source
	imported_symbols = extract_imports(tree)

	for node in tree.body:
		if isinstance(node, ast.ClassDef) and node.name == class_name:
			# Replace base classes with CommandBase
			node.bases = [ast.Name(id='CommandBase', ctx=ast.Load())]
			ast.fix_missing_locations(node)

			# Compile a module containing only that class
			class_module = ast.Module(body=[node], type_ignores=[])
			ast.fix_missing_locations(class_module)
			code = compile(class_module, filename=file_path, mode="exec")

			# Build isolated namespace
			ns = {
				"CommandBase": VideoModel,
				"command": command,
				**imported_symbols
			}

			exec(code, ns)
			subcls = ns[class_name]
			obj = subcls.__new__(subcls)
			return obj

	raise ValueError(f"Class '{class_name}' not found in {file_path}")


class CapabilitiesCommand:
    @staticmethod
    def register_subcommand(subparsers):
        """Register capabilities command"""
        run_parser = subparsers.add_parser("capabilities", help="Print the capabilities of a reactor VideoModel.")
        run_parser.set_defaults(func=CapabilitiesCommand)

    def __init__(self, args):
        """Initialize with parsed arguments"""
        self.args = args

    def run(self):
        """Print the capabilities of a reactor VideoModel."""
        from ..main import verify_reactor_workspace

        # Verify workspace and get manifest data
        manifest_data = verify_reactor_workspace()
        if manifest_data is None:
            return

        # Extract model information from manifest
        model_class_name: str = manifest_data["class"]
        model_file, model_class = model_class_name.split(":")
        model_class: VideoModel = load_class_without_init(model_file+".py", model_class)

        if "model_name" not in manifest_data.keys():
            print("Error: manifest.json is missing required 'model_name' field.")
            print("Please add a 'model_name' field specifying the model name.")
            return
        if "model_version" not in manifest_data.keys():
            print("Error: manifest.json is missing required 'model_version' field.")
            print("Please add a 'model_version' field specifying the model version.")
            return


        print(json.dumps(model_class.commands(), indent=4))