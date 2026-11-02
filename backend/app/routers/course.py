from fastapi import APIRouter, HTTPException

from app.course.modules import MODULES

router = APIRouter(prefix="/api/course", tags=["curso"])


@router.get("/modules")
async def list_modules():
    return [{**m, "order": i + 1} for i, m in enumerate(MODULES)]


@router.get("/modules/{slug}")
async def get_module(slug: str):
    for i, m in enumerate(MODULES):
        if m["slug"] == slug:
            return {**m, "order": i + 1}
    raise HTTPException(404, "Módulo no encontrado")
