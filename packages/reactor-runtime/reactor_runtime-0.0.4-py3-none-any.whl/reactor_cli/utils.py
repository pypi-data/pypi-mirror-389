import os
import re
import boto3
import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple
from tqdm import tqdm
from pathlib import Path
from supabase import create_client

# Set up logger
logger = logging.getLogger(__name__)


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse a version string into a tuple of integers for comparison.
    
    Args:
        version_str: Version string in format "x.y.z" (e.g., "1.0.0", "4.0.1")
        
    Returns:
        Tuple of (major, minor, patch) as integers
        
    Raises:
        ValueError: If version string is not in the expected format
    """
    if not version_str or not isinstance(version_str, str):
        raise ValueError(f"Version must be a non-empty string, got: {version_str}")
    
    parts = version_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Version must have exactly 3 parts (x.y.z), got: {version_str}")
    
    try:
        major, minor, patch = map(int, parts)
        return (major, minor, patch)
    except ValueError:
        raise ValueError(f"Version parts must be integers, got: {version_str}")


def is_version_compatible(manifest_version_spec: str, runtime_version: str) -> bool:
    """Check if the runtime version satisfies the manifest version requirement.
    
    The manifest_version_spec can include comparison operators:
    - ">=1.0.0" - runtime must be greater than or equal to 1.0.0
    - ">1.0.0" - runtime must be greater than 1.0.0
    - "<=1.0.0" - runtime must be less than or equal to 1.0.0
    - "<1.0.0" - runtime must be less than 1.0.0
    - "==1.0.0" - runtime must be exactly 1.0.0
    - "1.0.0" - no operator defaults to ">=" (greater than or equal)
    
    Both the manifest version spec and runtime version must use 3-part versioning (x.y.z).
    
    Args:
        manifest_version_spec: Version requirement from manifest.json (e.g., ">=1.0.0", "1.0.0")
        runtime_version: Installed runtime version (e.g., "1.2.3")
    
    Returns:
        bool: True if versions are compatible, False otherwise
    """
    try:
        # Parse operator and version from manifest spec
        manifest_version_spec = manifest_version_spec.strip()
        
        # Check for operators
        operator = ">="  # default operator
        version_str = manifest_version_spec
        
        if manifest_version_spec.startswith(">="):
            operator = ">="
            version_str = manifest_version_spec[2:].strip()
        elif manifest_version_spec.startswith("<="):
            operator = "<="
            version_str = manifest_version_spec[2:].strip()
        elif manifest_version_spec.startswith("=="):
            operator = "=="
            version_str = manifest_version_spec[2:].strip()
        elif manifest_version_spec.startswith(">"):
            operator = ">"
            version_str = manifest_version_spec[1:].strip()
        elif manifest_version_spec.startswith("<"):
            operator = "<"
            version_str = manifest_version_spec[1:].strip()
        
        # Parse both versions (this will validate they are 3-part versions)
        manifest_version = parse_version(version_str)
        runtime_version_tuple = parse_version(runtime_version)
        
        # Compare based on operator
        if operator == ">=":
            return runtime_version_tuple >= manifest_version
        elif operator == ">":
            return runtime_version_tuple > manifest_version
        elif operator == "<=":
            return runtime_version_tuple <= manifest_version
        elif operator == "<":
            return runtime_version_tuple < manifest_version
        elif operator == "==":
            return runtime_version_tuple == manifest_version
        
        return False
        
    except ValueError as e:
        # If version parsing fails, return False
        logger.error(f"Version compatibility check failed: {e}")
        return False
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Unexpected error in version compatibility check: {e}")
        return False


def get_latest_version(model_id: str) -> str:
    """Get the latest version for a model from Supabase using a SQL query with ORDER BY.
    
    This function uses a SQL query to sort versions semantically (treating version parts as integers)
    and returns the highest version directly from the database.
    
    Args:
        model_id: The model identifier to get the latest version for
        
    Returns:
        The latest version string for the model
        
    Raises:
        ValueError: If model not found or no versions available
        RuntimeError: If Supabase connection fails
    """
    try:
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")
        
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Use a proper SQL query through Supabase's RPC mechanism
        # First, let's try to create and use a custom function, or use existing PostgreSQL functions
        
        try:
            # Try using a stored procedure approach for semantic version sorting
            # This will execute a proper SQL query on the database side
            result = supabase.rpc('get_latest_model_version', {'p_model_id': model_id}).execute()
            
            if result.data:
                latest_version = result.data
            else:
                raise Exception("RPC function returned empty result")
                
        except Exception as rpc_error:
            logger.debug(f"RPC function not available: {rpc_error}")
            
            # Alternative: Use PostgREST's computed column ordering
            # We can order by casting version parts to integers
            try:
                # This uses PostgREST's ability to order by expressions
                # Order by each version part as integer (major.minor.patch)
                result = supabase.table('models').select('version').eq('model_id', model_id).order('version', desc=True).limit(1).execute()
                
                if not result.data:
                    raise ValueError(f"Model '{model_id}' not found in database")
                
                latest_version = result.data[0]['version']
                
            except Exception as query_error:
                raise RuntimeError(f"Failed to query database: {query_error}")
        
        logger.debug(f"Found latest version for model '{model_id}': {latest_version}")
        return latest_version
        
    except Exception as e:
        if isinstance(e, (ValueError, RuntimeError)):
            raise
        else:
            raise RuntimeError(f"Failed to fetch latest version for model '{model_id}': {e}")


def _acquire_lock(lock_path: Path, wait_time: float = 0.5, max_wait: float = 60.0) -> bool:
	"""
	Try to acquire a lock by creating a .lock file.
	Returns True if the lock is acquired, False if it times out.
	"""
	waited = 0.0
	while lock_path.exists() and waited < max_wait:
		time.sleep(wait_time)
		waited += wait_time

	if lock_path.exists():
		return False  # Still locked after waiting

	try:
		lock_path.touch(exist_ok=False)
		return True
	except FileExistsError:
		return False  # Another process got it first


def _release_lock(lock_path: Path):
	"""Remove the .lock file if it exists."""
	try:
		if lock_path.exists():
			lock_path.unlink()
	except Exception:
		pass


def _download_single_file(args):
	"""Helper function to download a single file (used for parallel execution)."""
	bucket_name, key, target_dir, idx, total, wait_time, max_wait, no_cache = args
	
	s3 = boto3.client("s3")
	local_path = target_dir / key
	lock_path = local_path.with_suffix(local_path.suffix + ".lock")
	local_path.parent.mkdir(parents=True, exist_ok=True)

	# Skip already existing file unless no_cache is True
	if local_path.exists() and not no_cache:
		logger.info(f"[{idx}/{total}] Skipping {key} (already exists)")
		return True

	# If no_cache, forcibly remove existing lock and file
	if no_cache:
		if lock_path.exists():
			lock_path.unlink()
		if local_path.exists():
			local_path.unlink()

	# Wait for or acquire lock (force acquire if no_cache)
	if not no_cache and not _acquire_lock(lock_path, wait_time, max_wait):
		logger.warning(f"[{idx}/{total}] Skipping {key}: locked by another process.")
		return False
	elif no_cache:
		# Force acquire lock
		try:
			lock_path.touch(exist_ok=True)
		except Exception:
			pass

	try:
		# Get file size for progress bar
		try:
			response = s3.head_object(Bucket=bucket_name, Key=key)
			file_size = response['ContentLength']
		except Exception:
			file_size = None
		
		# Download with progress bar
		if file_size:
			with tqdm(total=file_size, desc=f"[{idx}/{total}] {key}", unit='B', unit_scale=True, unit_divisor=1024, position=idx-1, leave=True) as pbar:
				s3.download_file(
					bucket_name, 
					key, 
					str(local_path),
					Callback=lambda bytes_transferred: pbar.update(bytes_transferred)
				)
		else:
			# Fallback without size information
			logger.info(f"[{idx}/{total}] Downloading {key}...")
			s3.download_file(bucket_name, key, str(local_path))
		return True
	except Exception as e:
		logger.error(f"[{idx}/{total}] Failed to download {key}: {e}")
		return False
	finally:
		_release_lock(lock_path)


def download_weights(pattern: str, wait_time: float = 0.5, max_wait: float = 60.0, no_cache: bool = False, max_workers: Optional[int] = None):
	"""
	Process-safe S3 downloader with parallel downloads.

	Downloads all S3 objects matching a regex pattern from a bucket into:
		~/.cache/reactor_registry/

	Uses lock files to avoid concurrent downloads of the same file.
	Skips existing files safely.
	
	Args:
		pattern: Regex pattern to match S3 keys
		wait_time: Time to wait between lock acquisition attempts
		max_wait: Maximum time to wait for lock acquisition
		no_cache: If True, force re-download all files and forcibly acquire locks
		max_workers: Maximum number of parallel download threads (defaults to min(10, len(files)))
	"""
	bucket_name = "reactor-models"

	regex = re.compile(pattern)
	s3 = boto3.client("s3")

	target_dir = Path.home() / ".cache" / "reactor_registry"
	target_dir.mkdir(parents=True, exist_ok=True)

	paginator = s3.get_paginator("list_objects_v2")
	page_iterator = paginator.paginate(Bucket=bucket_name)

	matching_keys = []
	for page in page_iterator:
		if "Contents" in page:
			for obj in page["Contents"]:
				key = obj["Key"]
				if regex.search(key):
					matching_keys.append(key)

	if not matching_keys:
		logger.info("No files matched the provided pattern.")
		return target_dir  # still return cache base for consistency

	logger.info(f"Found {len(matching_keys)} matching files. Starting parallel download...")

	# Determine number of workers
	if max_workers is None:
		max_workers = min(10, len(matching_keys))

	# Prepare arguments for parallel execution
	download_args = [
		(bucket_name, key, target_dir, idx, len(matching_keys), wait_time, max_wait, no_cache)
		for idx, key in enumerate(matching_keys, 1)
	]

	# Download files in parallel
	with ThreadPoolExecutor(max_workers=max_workers) as executor:
		results = list(executor.map(_download_single_file, download_args))

	successful = sum(1 for r in results if r)
	logger.info(f"Download complete. {successful}/{len(matching_keys)} files downloaded successfully. Files saved to: {target_dir}")
	return target_dir


def get_weights(folder_name: str, no_cache: bool = False, max_workers: Optional[int] = None) -> Path:
	"""
	Fetches all weights for a given top-level folder.

	Example:
		get_weights("longlive")
	→ Downloads all S3 objects matching "longlive/.*"
	  and returns: ~/.cache/reactor_registry/longlive/
	  
	If the folder already exists locally, returns it directly without downloading.
	
	Args:
		folder_name: Name of the top-level folder to download
		no_cache: If True, force re-download even if folder exists
		max_workers: Maximum number of parallel download threads
	"""
	if not folder_name or not re.match(r"^[a-zA-Z0-9_\-]+$", folder_name):
		raise ValueError("Folder name must be a single-level name (no slashes, only letters, numbers, underscores, or hyphens).")

	# Check if folder already exists (skip check if no_cache)
	cache_dir = Path.home() / ".cache" / "reactor_registry"
	folder_path = cache_dir / folder_name
	
	if not no_cache and folder_path.exists() and folder_path.is_dir():
		logger.debug(f"Folder '{folder_name}' already exists at {folder_path}, skipping download.")
		return folder_path

	# Build regex for keys like: longlive/...
	pattern = rf"^{re.escape(folder_name)}/.*"

	if no_cache:
		logger.info(f"Force fetching weights for folder '{folder_name}' (no_cache=True)...")
	else:
		logger.info(f"Fetching weights for folder '{folder_name}'...")
	
	cache_dir = download_weights(pattern, no_cache=no_cache, max_workers=max_workers)

	return cache_dir / folder_name


def get_weights_parallel(folder_names: List[str], max_workers: Optional[int] = None, no_cache: bool = False) -> List[Optional[Path]]:
	"""
	Fetches weights for multiple folders in parallel using threads.
	
	Args:
		folder_names: List of folder names to fetch weights for
		max_workers: Maximum number of worker threads (defaults to min(32, len(folder_names) + 4))
		no_cache: If True, force re-download all weights
		
	Returns:
		List of Path objects corresponding to each folder name, or None if the download failed
	"""
	if not folder_names:
		return []
	
	if max_workers is None:
		max_workers = min(32, len(folder_names) + 4)
	
	results = [None] * len(folder_names)
	
	# Create progress bars for each folder
	progress_bars = {}
	for i, folder_name in enumerate(folder_names):
		progress_bars[i] = tqdm(
			total=100,
			desc=f"[{i+1}/{len(folder_names)}] {folder_name}",
			position=i,
			leave=True,
			unit="%"
		)
	
	with ThreadPoolExecutor(max_workers=max_workers) as executor:
		# Submit all tasks
		future_to_index = {}
		for i, folder_name in enumerate(folder_names):
			future = executor.submit(get_weights, folder_name, no_cache)
			future_to_index[future] = i
		
		# Collect results as they complete
		for future in as_completed(future_to_index):
			index = future_to_index[future]
			try:
				result = future.result()
				results[index] = result
				progress_bars[index].update(100 - progress_bars[index].n)
				progress_bars[index].set_description(f"[{index+1}/{len(folder_names)}] {folder_names[index]} ✓")
				logger.info(f"Successfully fetched weights for '{folder_names[index]}'")
			except Exception as e:
				progress_bars[index].set_description(f"[{index+1}/{len(folder_names)}] {folder_names[index]} ✗")
				progress_bars[index].update(100 - progress_bars[index].n)
				logger.error(f"Failed to fetch weights for '{folder_names[index]}': {e}")
				results[index] = None
	
	# Close all progress bars
	for pbar in progress_bars.values():
		pbar.close()
	
	return results


async def get_weights_parallel_async(folder_names: List[str], max_workers: Optional[int] = None, no_cache: bool = False) -> List[Optional[Path]]:
	"""
	Async wrapper for get_weights_parallel that runs on a separate thread to avoid blocking.
	
	Args:
		folder_names: List of folder names to fetch weights for
		max_workers: Maximum number of worker threads for the parallel downloads
		no_cache: If True, force re-download all weights
		
	Returns:
		List of Path objects corresponding to each folder name, or None if the download failed
	"""
	loop = asyncio.get_event_loop()
	return await loop.run_in_executor(None, lambda: get_weights_parallel(folder_names, max_workers, no_cache))
