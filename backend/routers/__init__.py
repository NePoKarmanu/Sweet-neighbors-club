from .exit import router as exit_router
from .listing import router as listing_router
from .notifications import router as notifications_router
from .profile import router as profile_router
from .refresh import router as refresh_router
from .scraping import router as scraping_router
from .signin import router as signin_router
from .signup import router as signup_router

from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["auth"])
auth_router.include_router(signup_router)
auth_router.include_router(signin_router)
auth_router.include_router(exit_router)
auth_router.include_router(refresh_router)
auth_router.include_router(profile_router)

__all__ = ["listing_router", "auth_router", "scraping_router", "notifications_router"]
