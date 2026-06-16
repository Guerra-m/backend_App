from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.deps import require_role
from app.modules.uploads.uploads_schema import CloudinaryResponse
from app.modules.uploads.uploads_service import UploadsService

uploads_router = APIRouter(prefix="/api/v1/uploads", tags=["Uploads - Cloudinary"])


def get_uploads_service() -> UploadsService:
    return UploadsService()


@uploads_router.post(
    "/imagen",
    response_model=CloudinaryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def subir_imagen(
    file: UploadFile = File(...),
    folder: str = Form(default="foodstore/productos"),
    service: UploadsService = Depends(get_uploads_service),
):
    """
    Sube una imagen a Cloudinary.
    - Acepta: image/jpeg, image/png, image/webp
    - Tamaño máximo: 5 MB
    - Devuelve secure_url y public_id
    """
    return service.subir_imagen(file, folder=folder)


@uploads_router.delete(
    "/imagen/{public_id:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["ADMIN"]))],
)
def eliminar_imagen(
    public_id: str,
    service: UploadsService = Depends(get_uploads_service),
):
    """
    Elimina una imagen de Cloudinary por su public_id.
    El public_id puede contener barras (ej: foodstore/productos/abc123).
    """
    service.eliminar_imagen(public_id)