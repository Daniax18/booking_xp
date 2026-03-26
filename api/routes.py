# api/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/resources")
def create_resource(data: dict):
    resource = create_resource_use_case.execute(data)
    return resource