from fastapi import APIRouter

from creditflow.api.v1.routes import (
    assistant,
    cases,
    documents,
    evaluations,
    policies,
    reviews,
    underwriting,
)

router = APIRouter(prefix="/api/v1")
router.include_router(cases.router, prefix="/applications")
# Compatibility alias retained for existing clients while `/applications` is canonical.
router.include_router(cases.router, prefix="/cases", include_in_schema=False)
router.include_router(documents.router)
router.include_router(underwriting.router)
router.include_router(reviews.router)
router.include_router(policies.router)
router.include_router(assistant.router)
router.include_router(evaluations.router)
