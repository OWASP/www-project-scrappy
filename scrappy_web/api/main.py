from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import shutil
import os
import uuid
from datetime import datetime, timedelta

from .config import settings
from .auth import (
    create_access_token, get_current_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES, FAKE_USERS_DB, verify_password
)
from .models import Token, JobResponse, JobResult, JobStatus, ScrapMode
from .worker import run_scrappy_job, JOBS

# Setup Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="ScrapPY Web API",
    description="Secure, decoupled REST API for ScrapPY",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (Restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount UI
ui_path = os.path.join(os.path.dirname(__file__), "../ui")
app.mount("/ui", StaticFiles(directory=ui_path, html=True), name="ui")

# Temp storage
UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return RedirectResponse(url="/ui/")

@app.post("/api/v1/auth/token", response_model=Token)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/jobs", response_model=JobResponse)
@limiter.limit(settings.JOB_RATE_LIMIT)
async def create_job(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: ScrapMode = Form(...),
    consent_acknowledged: bool = Form(...),
    current_user: dict = Depends(get_current_user)
):
    if not consent_acknowledged:
        raise HTTPException(status_code=400, detail="Explicit consent required")
    
    # Validate content type
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Validate PDF magic bytes
    header = await file.read(5)
    await file.seek(0)
    if header != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = str(uuid.uuid4())
    file_location = os.path.join(UPLOAD_DIR, f"{job_id}.pdf")
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Initialize Job
    JOBS[job_id] = {
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "created_at": datetime.utcnow(),
        "mode": mode,
        "filename": file.filename,
        "user": current_user['username']
    }
    
    # Schedule Background Task
    background_tasks.add_task(run_scrappy_job, job_id, file_location, mode)
    
    return JOBS[job_id]

@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS[job_id]

@app.get("/api/v1/jobs/{job_id}/result", response_model=JobResult)
async def get_job_result(job_id: str, current_user: dict = Depends(get_current_user)):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = JOBS[job_id]
    if job["status"] != JobStatus.COMPLETED and job["status"] != JobStatus.FAILED:
        raise HTTPException(status_code=400, detail="Job not finished")
        
    return JobResult(
        job_id=job_id,
        status=job["status"],
        output=job.get("output", []),
        error=job.get("error")
    )