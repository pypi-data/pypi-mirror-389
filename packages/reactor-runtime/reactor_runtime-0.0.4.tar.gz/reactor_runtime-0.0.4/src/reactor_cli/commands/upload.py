"""Upload command implementation."""

import logging
import os
import sys

from ..main import verify_reactor_workspace
from .capabilities import load_class_without_init
from supabase import create_client

logger = logging.getLogger(__name__)



class UploadCommand:
    @staticmethod
    def register_subcommand(subparsers):
        """Register upload command"""
        upload_parser = subparsers.add_parser("upload", help="Upload model to Supabase")
        upload_parser.set_defaults(func=UploadCommand)

    def __init__(self, args):
        """Initialize command with parsed arguments"""
        self.args = args

    def run(self):
        """Upload model information to Supabase"""
        # Verify workspace and get manifest data
        manifest_data = verify_reactor_workspace()
        if manifest_data is None:
            return
        
        # Check required fields in manifest
        if "model_name" not in manifest_data:
            logger.error("manifest.json is missing required 'model_name' field.")
            logger.error("Please add a 'model_name' field specifying the model name.")
            sys.exit(1)
        
        if "model_version" not in manifest_data:
            logger.error("manifest.json is missing required 'model_version' field.")
            logger.error("Please add a 'model_version' field specifying the model version.")
            sys.exit(1)
        
        model_name = manifest_data["model_name"]
        model_version = manifest_data["model_version"]
        
        logger.info(f"Uploading model: {model_name} (version: {model_version})")
        
        # Get capabilities (reuse logic from capabilities.py)
        logger.info("Extracting model capabilities...")
        try:
            model_class_name: str = manifest_data["class"]
            model_file, model_class = model_class_name.split(":")
            model_class_instance = load_class_without_init(model_file + ".py", model_class)
            capabilities = model_class_instance.commands()
        except Exception as e:
            logger.error(f"Error extracting capabilities: {e}")
            sys.exit(1)
        
        # Get Supabase credentials from environment
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials in environment.")
            logger.error("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.")
            sys.exit(1)
        
        # Connect to Supabase
        logger.info("Connecting to Supabase...")
        supabase = create_client(supabase_url, supabase_key)

        
        # Prepare data for insertion
        data = {
            "model_id": model_name,
            "version": model_version,
            "manifest": manifest_data,
            "capabilities": capabilities
        }
        
        # Check if model with same name and version already exists
        logger.info("Checking for existing model...")
        try:
            existing = supabase.table("models").select("id").eq("model_id", model_name).eq("version", model_version).execute()
            
            if existing.data:
                # Model exists, update it
                existing_id = existing.data[0]["id"]
                logger.info(f"Model '{model_name}' version '{model_version}' already exists (ID: {existing_id}). Updating...")
                
                response = supabase.table("models").update(data).eq("id", existing_id).execute()
                logger.info(f"✓ Successfully updated model '{model_name}' version '{model_version}' in Supabase!")
                logger.info(f"Record ID: {existing_id}")
            else:
                # Model doesn't exist, insert new
                logger.info(f"Creating new record for model '{model_name}' version '{model_version}'...")
                response = supabase.table("models").insert(data).execute()
                logger.info(f"✓ Successfully uploaded model '{model_name}' version '{model_version}' to Supabase!")
                logger.info(f"Record ID: {response.data[0]['id'] if response.data else 'N/A'}")
                
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {e}")
            sys.exit(1)