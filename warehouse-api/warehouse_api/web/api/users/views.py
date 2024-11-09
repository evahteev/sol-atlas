from fastapi import APIRouter

from warehouse_api.db.models.users import UserCreate  # type: ignore
from warehouse_api.db.models.users import UserRead  # type: ignore
from warehouse_api.db.models.users import UserUpdate  # type: ignore
from warehouse_api.db.models.users import api_users  # type: ignore
# from warehouse_api.db.models.users import auth_cookie  # type: ignore
from warehouse_api.db.models.users import auth_jwt  # type: ignore

router = APIRouter()

router.include_router(
    api_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    api_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    api_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    api_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
router.include_router(
    api_users.get_auth_router(auth_jwt),
    prefix="/auth/jwt",
    tags=["auth"],
)
