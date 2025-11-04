import subprocess
import shutil
import sys
import logging
logger = logging.getLogger(__name__)


def start_livekit_dev():
	"""
	Starts the LiveKit server in development mode.
	Raises an error if LiveKit is not installed.
	"""
	# Check if livekit-server is installed
	if shutil.which("livekit-server") is None:
		raise RuntimeError(
			"LiveKit is not installed. Please follow the installation guide here: "
			"https://docs.livekit.io/home/self-hosting/local/"
		)

	# Try to start LiveKit
	try:
		lk_process = subprocess.Popen(
			["livekit-server", "--dev"],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL
		)
		return lk_process
	except Exception as e:
		logger.error(f"Failed to start LiveKit: {e}")
		raise RuntimeError(f"Failed to start LiveKit: {e}")
