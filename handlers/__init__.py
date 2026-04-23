from aiogram import Router
from .common import router as common_router
from .admin import router as admin_router
from .social import router as social_router
from .info import router as info_router
from .games.guess_number import router as guess_game_router
from .games.rps import router as rps_router
from .games.mafia import router as mafia_router

router = Router()
router.include_router(common_router)
router.include_router(admin_router)
router.include_router(info_router)
router.include_router(guess_game_router)
router.include_router(rps_router)
router.include_router(mafia_router)
router.include_router(social_router)
