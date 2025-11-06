from fastapi import APIRouter

from mosaygent.routes.environment import router as environment_router
from mosaygent.routes.firebase import router as firebase_router
from mosaygent.routes.flutter import router as flutter_router
from mosaygent.routes.github import router as github_router
from mosaygent.routes.supabase import router as supabase_router

router = APIRouter(
    prefix='/mosaygent',
    tags=['Mosaygent Routes'],
    include_in_schema=False
)


router.include_router(environment_router)
router.include_router(firebase_router)
router.include_router(flutter_router)
router.include_router(github_router)
router.include_router(supabase_router)
