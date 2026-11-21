from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.modules.identity.api.dependencies import (
    AdminUser,
    ContextDep,
    CurrentUser,
    RuntimeDep,
    SessionDep,
)
from app.modules.identity.api.schemas import (
    ChangePasswordRequest,
    CreateUserRequest,
    LoginRequest,
    RefreshRequest,
    RoleOut,
    TokenResponse,
    UpdateUserRequest,
    UserOut,
)
from app.modules.identity.composition import (
    make_change_password,
    make_create_user,
    make_list_users,
    make_login,
    make_logout,
    make_refresh,
    make_set_user_active,
    make_update_user,
)
from app.modules.identity.domain.entities import ROLE_DESCRIPTIONS, Role
from app.shared.schemas import Page

router = APIRouter(prefix="/api/v1")

auth = APIRouter(prefix="/auth", tags=["auth"])
users = APIRouter(prefix="/users", tags=["users"])
roles = APIRouter(prefix="/roles", tags=["users"])


@auth.post("/login")
async def login(
    body: LoginRequest, session: SessionDep, runtime: RuntimeDep, ctx: ContextDep
) -> TokenResponse:
    result = await make_login(session, runtime).execute(body.email, body.password, ctx)
    return TokenResponse.from_session(result)


@auth.post("/refresh")
async def refresh(
    body: RefreshRequest, session: SessionDep, runtime: RuntimeDep, ctx: ContextDep
) -> TokenResponse:
    result = await make_refresh(session, runtime).execute(body.refresh_token, ctx)
    return TokenResponse.from_session(result)


@auth.post("/logout", status_code=204)
async def logout(
    body: RefreshRequest,
    user: CurrentUser,
    session: SessionDep,
    runtime: RuntimeDep,
    ctx: ContextDep,
) -> Response:
    await make_logout(session, runtime).execute(user, body.refresh_token, ctx)
    return Response(status_code=204)


@auth.get("/me")
async def me(user: CurrentUser) -> UserOut:
    return UserOut.from_user(user)


@auth.post("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    user: CurrentUser,
    session: SessionDep,
    runtime: RuntimeDep,
    ctx: ContextDep,
) -> Response:
    await make_change_password(session, runtime).execute(
        user, body.current_password, body.new_password, ctx
    )
    return Response(status_code=204)


@users.get("")
async def list_users(
    _: AdminUser,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    active: bool | None = None,
) -> Page[UserOut]:
    items, total = await make_list_users(session).execute(
        page=page, per_page=per_page, active=active
    )
    return Page(
        items=[UserOut.from_user(user) for user in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@users.post("", status_code=201)
async def create_user(
    body: CreateUserRequest,
    admin: AdminUser,
    session: SessionDep,
    runtime: RuntimeDep,
    ctx: ContextDep,
) -> UserOut:
    user = await make_create_user(session, runtime).execute(
        admin,
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        roles=body.roles,
        ctx=ctx,
    )
    return UserOut.from_user(user)


@users.patch("/{user_id}")
async def update_user(
    user_id: UUID,
    body: UpdateUserRequest,
    admin: AdminUser,
    session: SessionDep,
    runtime: RuntimeDep,
    ctx: ContextDep,
) -> UserOut:
    user = await make_update_user(session, runtime).execute(
        admin,
        user_id,
        full_name=body.full_name,
        roles=frozenset(body.roles) if body.roles is not None else None,
        ctx=ctx,
    )
    return UserOut.from_user(user)


@users.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID, admin: AdminUser, session: SessionDep, runtime: RuntimeDep, ctx: ContextDep
) -> UserOut:
    user = await make_set_user_active(session, runtime).execute(
        admin, user_id, active=False, ctx=ctx
    )
    return UserOut.from_user(user)


@users.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID, admin: AdminUser, session: SessionDep, runtime: RuntimeDep, ctx: ContextDep
) -> UserOut:
    user = await make_set_user_active(session, runtime).execute(
        admin, user_id, active=True, ctx=ctx
    )
    return UserOut.from_user(user)


@roles.get("")
async def list_roles(_: AdminUser) -> list[RoleOut]:
    return [RoleOut(code=role, description=ROLE_DESCRIPTIONS[role]) for role in Role]


router.include_router(auth)
router.include_router(users)
router.include_router(roles)
