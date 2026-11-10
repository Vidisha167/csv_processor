from prometheus_client import REGISTRY, Counter
from prometheus_client.core import GaugeMetricFamily
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Job, JobStatus

UPLOADS_TOTAL = Counter("csv_uploads_total", "CSV files accepted for processing")


class JobStatusCollector:
    """Runs on every scrape and reports how many jobs are in each status."""

    def collect(self):
        gauge = GaugeMetricFamily(
            "csv_jobs", "Number of jobs by status", labels=["status"]
        )
        db = SessionLocal()
        try:
            rows = dict(
                db.execute(select(Job.status, func.count()).group_by(Job.status)).all()
            )
        finally:
            db.close()
        for status in JobStatus:
            gauge.add_metric([status.value], rows.get(status.value, 0))
        yield gauge


REGISTRY.register(JobStatusCollector())