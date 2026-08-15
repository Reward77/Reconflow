from sqlalchemy.orm import Session

from app.models.upload import Upload, UploadType
from app.models.job import ReconciliationJob, JobStatus
from app.models.column_mapping import ColumnMapping
from app.models.reconciliation_result import ReconciliationResult, ReconciliationStatus

from app.services.dataframe_service import DataFrameService
from app.services.canonical_service import CanonicalService
from app.services.reconciliation_engine import ReconciliationEngine

class ReconciliationService:

    @staticmethod
    def apply_mapping(df, mappings, source):
        rename_map = {
            getattr(mapping, f"{source}_column").strip().lower().replace(" ", "_"): mapping.canonical_column
            for mapping in mappings
        }
        normalized_columns = {
            column: column.strip().lower().replace(" ", "_")
            for column in df.columns
        }
        return df.rename(columns=normalized_columns).rename(columns=rename_map)

    @staticmethod
    def run(db: Session, company_id, job_id):

        company_upload = (
            db.query(Upload)
            .filter(
                Upload.job_id == job_id,
                Upload.company_id == company_id,
                Upload.upload_type == UploadType.COMPANY
            )
            .first()
        )

        processor_upload = (
            db.query(Upload)
            .filter(
                Upload.job_id == job_id,
                Upload.company_id == company_id,
                Upload.upload_type == UploadType.PROCESSOR
            )
            .first()
        )

        if not company_upload or not processor_upload:
            raise Exception("Both company and processor files are required.")

        job = db.query(ReconciliationJob).filter(ReconciliationJob.id == job_id).first()
        job.status = JobStatus.PROCESSING
        db.commit()

        company_df = DataFrameService.load_file(company_upload.storage_path)
        processor_df = DataFrameService.load_file(processor_upload.storage_path)

        mappings = db.query(ColumnMapping).filter(
            ColumnMapping.company_id == company_id,
            ColumnMapping.job_id == job_id,
            ColumnMapping.processor_id == processor_upload.processor_id
        ).all()
        if not mappings:
            raise Exception("No column mapping has been saved for this job. Map both files before running reconciliation.")

        company_df = ReconciliationService.apply_mapping(company_df, mappings, "company")
        processor_df = ReconciliationService.apply_mapping(processor_df, mappings, "processor")

        company_df = CanonicalService.prepare(company_df)
        processor_df = CanonicalService.prepare(processor_df)

        results = ReconciliationEngine.reconcile(company_df, processor_df)

        # A re-run must replace the previous run's output, otherwise the results
        # page shows stale or duplicated transactions.
        db.query(ReconciliationResult).filter(
            ReconciliationResult.company_id == company_id,
            ReconciliationResult.job_id == job_id,
        ).delete(synchronize_session=False)

        objects = []
        for row in results:
            objects.append(ReconciliationResult( company_id=company_id, job_id=job_id, transaction_id=row["transaction_id"], company_amount=row["company_amount"], processor_amount=row["processor_amount"], company_status=row["company_status"], processor_status=row["processor_status"], status=row["status"] ))

        db.bulk_save_objects(objects)
        job.status = JobStatus.COMPLETED
        db.commit()

        matched = sum(row["status"] == ReconciliationStatus.MATCHED for row in results)
        mismatched = sum(
            row["status"] in {
                ReconciliationStatus.AMOUNT_MISMATCH,
                ReconciliationStatus.STATUS_MISMATCH,
            }
            for row in results
        )
        missing = sum(
            row["status"] in {
                ReconciliationStatus.MISSING_IN_COMPANY,
                ReconciliationStatus.MISSING_IN_PROCESSOR,
            }
            for row in results
        )

        return {
            "message": "Reconciliation completed.",
            "total": len(results),
            "matched": matched,
            "mismatched": mismatched,
            "missing": missing,
        }
