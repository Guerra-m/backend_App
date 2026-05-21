from fastapi import HTTPException, status
from app.modules.categoria.categoria_uow import CategoriaUnitOfWork
from app.modules.categoria.categoria_schema import CategoriaCreate, CategoriaUpdate, CategoriaRead, CategoriaReadWithSubs


class CategoriaService:
    def __init__(self, uow: CategoriaUnitOfWork):
        self.uow = uow

    def crear_categoria(self, data: CategoriaCreate) -> CategoriaRead:
        with self.uow as uow:
            # Validar que el padre exista si se envía
            if data.parent_id is not None:
                try:
                    uow.categorias.get_by_id(data.parent_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"La categoría padre con id {data.parent_id} no existe"
                    )
            categoria = uow.categorias.create(data)
            return CategoriaRead.model_validate(categoria)
#Devuelve una categoria
    def obtener_categoria(self, categoria_id: int) -> CategoriaReadWithSubs:
        with self.uow as uow:
            try:
                categoria = uow.categorias.get_by_id(categoria_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return CategoriaReadWithSubs.model_validate(categoria)
#Para listar categorias
    def listar_categorias(self, offset: int = 0, limit: int = 20) -> list[CategoriaRead]:
        with self.uow as uow:
            categorias = uow.categorias.get_all(offset=offset, limit=limit)
            return [CategoriaRead.model_validate(c) for c in categorias]

#Para devolver categorías de nivel raíz
    def listar_raices(self) -> list[CategoriaRead]:
        with self.uow as uow:
            raices = uow.categorias.get_raices()
            return [CategoriaRead.model_validate(c) for c in raices]
#Para actualizar cagetoria       
    def actualizar_categoria(self, categoria_id: int, data: CategoriaUpdate) -> CategoriaRead:
        with self.uow as uow:
            try:
                categoria = uow.categorias.update(categoria_id, data)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return CategoriaRead.model_validate(categoria)
#Elimina una categoria con soft delete
    def eliminar_categoria(self, categoria_id: int) -> dict:
        with self.uow as uow:
            try:
                uow.categorias.soft_delete(categoria_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            return {"mensaje": f"Categoría {categoria_id} eliminada correctamente"}
