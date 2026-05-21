"""Router de Roles — solo lectura, solo ADMIN."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import engine
from app.core.deps import require_role
from app.modules.rol.rol_model import Rol
from app.modules.rol.rol_schema import RolRead
from app.modules.rol.rol_repository import RolRepository

rol_router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])


@rol_router.get(
    "/",
    response_model=list[RolRead],
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def listar_roles():
    with Session(engine) as session:
        repo = RolRepository(session)
        return [RolRead.model_validate(r) for r in repo.get_all()]
