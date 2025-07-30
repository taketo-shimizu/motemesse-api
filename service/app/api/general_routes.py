from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["general"])


@router.get("/hello")
def hello():
    """
    一般的なHelloエンドポイント（認証不要）
    """
    return {"message": "Hello from モテメッセ API!"}


@router.get("/health")
def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "healthy", "service": "motemesse-api"}