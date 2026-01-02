import subprocess
import os
import uuid
import logging
from typing import Dict
from .models import JobStatus, ScrapMode

# In-memory job store (Replace with DB in production)
JOBS: Dict[str, dict] = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRAPPY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ScrapPY.py"))
PYTHON_PATH = os.sys.executable # Use the same python interpreter

def run_scrappy_job(job_id: str, file_path: str, mode: ScrapMode):
    """
    Executes ScrapPY as a subprocess to ensure isolation.
    """
    logger.info(f"Starting job {job_id} with mode {mode}")
    JOBS[job_id]["status"] = JobStatus.PROCESSING
    
    output_file = f"{file_path}.txt"
    
    try:
        # Construct command securely (no shell=True)
        cmd = [
            PYTHON_PATH,
            SCRAPPY_PATH,
            "-f", file_path,
            "-m", mode.value,
            "-o", output_file
        ]
        
        # Execute
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False, # We handle return codes manually
            timeout=300 # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Job {job_id} failed: {result.stderr}")
            JOBS[job_id]["status"] = JobStatus.FAILED
            JOBS[job_id]["error"] = result.stderr
            return

        # Read output
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                lines = f.read().splitlines()
            JOBS[job_id]["output"] = lines
            # Cleanup output file
            os.remove(output_file)
        else:
            # Metadata mode prints to stdout, not file
            if mode == ScrapMode.METADATA:
                 JOBS[job_id]["output"] = result.stdout.splitlines()
            else:
                JOBS[job_id]["output"] = []

        JOBS[job_id]["status"] = JobStatus.COMPLETED
        logger.info(f"Job {job_id} completed successfully")

    except subprocess.TimeoutExpired:
        logger.error(f"Job {job_id} timed out")
        JOBS[job_id]["status"] = JobStatus.FAILED
        JOBS[job_id]["error"] = "Job timed out"
    except Exception as e:
        logger.exception(f"Job {job_id} encountered an error")
        JOBS[job_id]["status"] = JobStatus.FAILED
        JOBS[job_id]["error"] = str(e)
    finally:
        # Cleanup input file
        if os.path.exists(file_path):
            os.remove(file_path)
