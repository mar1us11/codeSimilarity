"""HTTP routers, aggregated onto a single API router."""

from fastapi import APIRouter

from app.api.routes import analysis, comparisons, health, labs, submissions

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(comparisons.router, prefix="/comparisons", tags=["comparisons"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(labs.router, prefix="/labs", tags=["labs"])

__all__ = ["api_router"]
