from fastapi import APIRouter
from app.features.{domain}.presentation.routes.{domain} import {domain}_router

# Main router with prefix for all {domain} routes
main_router = APIRouter(prefix="/{domain}")
main_router.include_router({domain}_router)
__all__ = ["main_router"]
