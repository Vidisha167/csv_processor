import uuid

from app import storage
from app.analysis import analyze_csv
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, JobStatus


@celery_app.task(name="process_csv")
def process_csv(job_id: str):
    db = SessionLocal()
    try:
        job = db.get(Job, uuid.UUID(job_id))
        if job is None:
            return

        job.status = JobStatus.PROCESSING.value
        db.commit()

        fileobj = storage.download_file(job.storage_key)
        job.result = analyze_csv(fileobj)

        job.status = JobStatus.COMPLETED.value
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(Job, uuid.UUID(job_id))
        if job:
            job.status = JobStatus.FAILED.value
            job.error = str(exc)
            db.commit()
        raise
    finally:
        db.close()