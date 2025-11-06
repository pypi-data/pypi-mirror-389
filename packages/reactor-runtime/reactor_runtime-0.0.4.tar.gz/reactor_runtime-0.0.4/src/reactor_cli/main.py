import pathlib
import json
import argparse
import sys
import importlib.resources
import shutil
from .utils import is_version_compatible

def get_installed_runtime_version():
	"""Get the version of the installed reactor-runtime package."""
	try:
		import reactor_runtime
		if hasattr(reactor_runtime, '__version__'):
			return reactor_runtime.__version__
		else:
			# Try to get version from package metadata
			try:
				import importlib.metadata
				return importlib.metadata.version('reactor-runtime')
			except ImportError:
				# Fallback for older Python versions
				try:
					import pkg_resources
					return pkg_resources.get_distribution('reactor-runtime').version
				except ImportError:
					raise RuntimeError("Could not import package metadata tools")
	except Exception as e:
		raise RuntimeError(f"Could not determine installed reactor-runtime version: {e}")

def verify_reactor_workspace():
	"""Verify the current directory is a reactor model workspace and return manifest data.
	
	Returns:
		dict: The manifest data if valid, None if invalid or error occurred.
	"""
	current_dir = pathlib.Path.cwd()
	manifest_path = current_dir / "manifest.json"
	
	# Check if current directory is a reactor model workspace
	if not manifest_path.exists():
		print("Error: No manifest.json found in current directory.")
		print("This directory does not appear to be a reactor model workspace.")
		print("Run 'reactor init' to initialize a new workspace, or navigate to an existing one.")
		return None
	
	# Validate manifest.json content
	try:
		with open(manifest_path, "r") as f:
			manifest_data = json.load(f)
		
		# Check required fields
		if "class" not in manifest_data:
			print("Error: manifest.json is missing required 'class' field.")
			print("Please ensure your manifest.json specifies the model class to use.")
			return None
		
		if "reactor-runtime" not in manifest_data:
			print("Error: manifest.json is missing required 'reactor-runtime' version field.")
			print("Please add a 'reactor-runtime' field specifying the required version.")
			print("Example: \"reactor-runtime\": \"0.1.0\"")
			return None
		
		manifest_version = manifest_data["reactor-runtime"]
		
		# Get the installed runtime version
		try:
			runtime_version = get_installed_runtime_version()
		except RuntimeError as e:
			print(f"Error: {e}")
			return None
		
		# Check version compatibility
		if not is_version_compatible(manifest_version, runtime_version):
			print(f"Error: Version mismatch!")
			print(f"  Manifest requires reactor-runtime version: {manifest_version}")
			print(f"  Installed reactor-runtime version: {runtime_version}")
			print(f"Please update the 'reactor-runtime' version in manifest.json to match {runtime_version}")
			return None
		
		print(f"Found valid manifest.json")
		print(f"Model class: {manifest_data['class']}")
		print(f"Reactor-runtime version: {runtime_version}")
		
		return manifest_data
		
	except json.JSONDecodeError as e:
		print(f"Error: manifest.json contains invalid JSON: {e}")
		return None
	except Exception as e:
		print(f"Error reading manifest.json: {e}")
		return None


def main():
	parser = argparse.ArgumentParser(prog="reactor")
	subparsers = parser.add_subparsers(dest="command")

	# Import and register commands
	from .commands import RunCommand, InitCommand, DownloadCommand, UploadCommand, SetupCommand, CapabilitiesCommand

	RunCommand.register_subcommand(subparsers)
	InitCommand.register_subcommand(subparsers)
	DownloadCommand.register_subcommand(subparsers)
	UploadCommand.register_subcommand(subparsers)
	SetupCommand.register_subcommand(subparsers)
	CapabilitiesCommand.register_subcommand(subparsers)

	args = parser.parse_args()
	if hasattr(args, "func"):
		command = args.func(args)  # Create command instance
		command.run()              # Run the command
	else:
		parser.print_help()
		sys.exit(1)
