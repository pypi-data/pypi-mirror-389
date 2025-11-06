"""Init command implementation."""

import pathlib
import importlib.resources


class InitCommand:
    @staticmethod
    def register_subcommand(subparsers):
        """Register init command"""
        init_parser = subparsers.add_parser("init", help="Initialize a new reactor model workspace")
        init_parser.add_argument("name", help="Name of the model (will create directory with this name)")
        init_parser.set_defaults(func=InitCommand)

    def __init__(self, args):
        """Initialize with parsed arguments"""
        self.args = args

    def run(self):
        """Initialize a new reactor model workspace in a directory with the given name."""
        model_name = self.args.name
        current_dir = pathlib.Path.cwd()
        target_dir = current_dir / model_name

        # Check if directory already exists
        if target_dir.exists():
            print(f"Error: Directory '{model_name}' already exists")
            print(f"Please choose a different name or remove the existing directory")
            return

        # Create the model directory
        try:
            target_dir.mkdir()
            print(f"Created directory: {model_name}")
        except Exception as e:
            print(f"Error creating directory '{model_name}': {e}")
            return

        print(f"Initializing reactor workspace in {target_dir}")

        # Copy template files from the installed package
        try:
            import template as template_package
            template_files = [
                "model_template.py",
                "manifest.json",
                "requirements.txt",
                "README.md"
            ]

            for filename in template_files:
                dest_path = target_dir / filename
                if dest_path.exists():
                    print(f"Warning: {filename} already exists, skipping...")
                    continue

                # Read template file from package resources
                try:
                    with importlib.resources.open_text(template_package, filename) as f:
                        content = f.read()

                    # Write to destination
                    with open(dest_path, 'w') as f:
                        f.write(content)

                    print(f"Created: {filename}")
                except FileNotFoundError:
                    print(f"Warning: Template file {filename} not found in package")
                    continue

            print(f"\nReactor workspace '{model_name}' initialized successfully!")
            print(f"\nNext steps:")
            print(f"1. cd {model_name}")
            print("2. Edit model_template.py to implement your video model")
            print("3. Update manifest.json with your model class, parameters, and reactor-runtime version")
            print("4. Add any additional dependencies to requirements.txt")
            print("5. Run 'reactor run' to start your model")

        except ImportError:
            print("Error: reactor_runtime package not found. Make sure it's properly installed.")
            return
        except Exception as e:
            print(f"Error initializing workspace: {e}")
            return