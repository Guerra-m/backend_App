import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.modules.uploads.uploads_schema import CloudinaryResponse

# Tipos MIME permitidos
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _init_cloudinary() -> None:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )


class UploadsService:

    def subir_imagen(self, file: UploadFile, folder: str = "foodstore") -> CloudinaryResponse:
        # Validar tipo MIME
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no permitido: {file.content_type}. Solo jpeg, png, webp.",
            )

        # Leer contenido y validar tamaño
        file_bytes = file.file.read()
        if len(file_bytes) > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo supera el tamaño máximo de 5 MB.",
            )

        _init_cloudinary()

        try:
            result = cloudinary.uploader.upload(
                file_bytes,
                folder=folder,
                resource_type="image",
                overwrite=False,
                unique_filename=True,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al subir imagen a Cloudinary: {str(e)}",
            )

        return CloudinaryResponse(
            secure_url=result["secure_url"],
            public_id=result["public_id"],
            width=result["width"],
            height=result["height"],
            format=result["format"],
            resource_type=result["resource_type"],
        )

    def eliminar_imagen(self, public_id: str) -> None:
        _init_cloudinary()

        try:
            result = cloudinary.uploader.destroy(public_id, resource_type="image")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al eliminar imagen de Cloudinary: {str(e)}",
            )

        if result.get("result") not in ("ok", "not found"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cloudinary no pudo eliminar la imagen: {result}",
            )