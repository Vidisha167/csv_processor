import os
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import metrics,models, storage
from app.database import Base, engine, get_db
from app.schemas import JobOut
from app.tasks import process_csv
from prometheus_fastapi_instrumentator import Instrumentator

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    storage.ensure_bucket()
    yield


app = FastAPI(title="CSV Processor", version="0.1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.post("/upload", status_code=202)
def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = os.path.basename(file.filename or "")
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    job_id = uuid.uuid4()
    storage_key = f"uploads/{job_id}/{filename}"

    # 1. Store the file in MinIO (streamed, so large files are fine)
    storage.upload_file(file.file, storage_key)

    # 2. Record the job in Postgres
    job = models.Job(
        id=job_id,
        filename=filename,
        storage_key=storage_key,
        status=models.JobStatus.PENDING.value,
    )
    db.add(job)
    db.commit()
    
    metrics.UPLOADS_TOTAL.inc()

    # Queue the background job (only after commit, so the worker can find the row)
    process_csv.delay(str(job_id))

    # 3. Return immediately. Processing will happen in the background (Step 5)
    return {"job_id": str(job_id), "status": job.status, "filename": filename}

@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs", response_model=list[JobOut])
def list_jobs(
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(models.Job).order_by(models.Job.created_at.desc()).limit(limit)
    if status:
        query = query.where(models.Job.status == status)
    return db.scalars(query).all()