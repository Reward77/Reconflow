import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from app.models.job import ReconciliationJob
from app.models.processor import Processor
from app.models.upload import Upload
from app.models.column_mapping import ColumnMapping
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.core.database import Base, engine
from app.api.jobs import router as jobs_router
from app.api.users import router as users_router
from app.api.uploads import router as uploads_router
from app.api.processors import router as processors_router
from app.api.mapping import router as mapping_router
# Import all models
from app.models.company import Company
from app.models.user import User,UserRole



Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ReconFlow API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(uploads_router)
app.include_router(processors_router)
app.include_router(mapping_router)

@app.get("/")
def home():

    return {

        "message": "ReconFlow API is running."

    }


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.reconciliation_service import ReconciliationService
from app.models.reconciliation_result import ReconciliationResult, ReconciliationStatus

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])

@router.post("/{job_id}/run")
def run_reconciliation(job_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return ReconciliationService.run(db, current_user.company_id, job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/results")
def get_reconciliation_results(job_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        results = db.query(ReconciliationResult).filter(
            ReconciliationResult.job_id == job_id,
            ReconciliationResult.company_id == current_user.company_id
        ).all()

        total = len(results)
        matched = sum(1 for r in results if r.status == ReconciliationStatus.MATCHED)
        mismatched = sum(1 for r in results if r.status == ReconciliationStatus.AMOUNT_MISMATCH)
        missing = sum(1 for r in results if r.status in [
            ReconciliationStatus.MISSING_IN_COMPANY,
            ReconciliationStatus.MISSING_IN_PROCESSOR
        ])

        return {
            "total": total,
            "matched": matched,
            "mismatched": mismatched,
            "missing": missing,
            "results": [
                {
                    "id": str(result.id),
                    "transaction_id": result.transaction_id,
                    "company_amount": result.company_amount,
                    "processor_amount": result.processor_amount,
                    "company_status": result.company_status,
                    "processor_status": result.processor_status,
                    "status": result.status.value
                }
                for result in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.include_router(router)
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://lucilla-unvisionary-unadmissibly.ngrok-free.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

