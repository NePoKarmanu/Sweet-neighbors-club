from .exit import router as exit_router
from .listing import router as listing_router
from .signin import router as signin_router
from .signup import router as signup_router

from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_router.include_router(signup_router)
auth_router.include_router(signin_router)
auth_router.include_router(exit_router)

__all__ = ["listing_router", "auth_router"]
