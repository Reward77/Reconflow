from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.column_mapping import ColumnMapping
from app.models.job import JobStatus, ReconciliationJob
from app.models.upload import Upload, UploadType

router = APIRouter()


@router.post("/mapping")
def save_mapping(payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        if not payload or "job_id" not in payload:
            raise HTTPException(status_code=400, detail="Missing job_id in mapping payload.")

        job_id = UUID(str(payload["job_id"]))
        company_file_id = UUID(str(payload.get("company_file_id")))
        processor_file_id = UUID(str(payload.get("processor_file_id")))

        company_mapping = payload.get("company") or {}
        processor_mapping = payload.get("processor") or {}
        required_fields = ("transaction_id", "amount", "status")

        for side, mapping in (("company", company_mapping), ("processor", processor_mapping)):
            missing = [field for field in required_fields if not mapping.get(field)]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required {side} mappings: {', '.join(missing)}."
                )

        job = db.query(ReconciliationJob).filter(
            ReconciliationJob.id == job_id,
            ReconciliationJob.company_id == current_user.company_id
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Reconciliation job not found.")

        company_upload = db.query(Upload).filter(
            Upload.id == company_file_id,
            Upload.job_id == job_id,
            Upload.company_id == current_user.company_id,
            Upload.upload_type == UploadType.COMPANY
        ).first()
        processor_upload = db.query(Upload).filter(
            Upload.id == processor_file_id,
            Upload.job_id == job_id,
            Upload.company_id == current_user.company_id,
            Upload.upload_type == UploadType.PROCESSOR
        ).first()

        if not company_upload or not processor_upload or not processor_upload.processor_id:
            raise HTTPException(status_code=400, detail="Select valid company and processor files for this job.")

        db.query(ColumnMapping).filter(
            ColumnMapping.company_id == current_user.company_id,
            ColumnMapping.job_id == job_id
        ).delete(synchronize_session=False)

        for canonical_column in ("transaction_id", "amount", "status", "date", "reference"):
            company_column = company_mapping.get(canonical_column)
            processor_column = processor_mapping.get(canonical_column)
            if company_column and processor_column:
                db.add(ColumnMapping(
                    company_id=current_user.company_id,
                    job_id=job_id,
                    processor_id=processor_upload.processor_id,
                    company_column=company_column,
                    processor_column=processor_column,
                    canonical_column=canonical_column
                ))

        job.status = JobStatus.READY_TO_RECONCILE
        db.commit()

        return {"status": "ok", "message": "Mapping saved."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
