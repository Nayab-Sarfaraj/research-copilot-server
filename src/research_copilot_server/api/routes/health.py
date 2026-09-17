from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Research Copilot API"}

@router.get("/health")
def health():
    return {"status": "ok"}

