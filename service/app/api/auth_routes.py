from fastapi import APIRouter, Depends
from typing import Dict, Any
from ...modules.auth_middleware import require_auth

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/profile")
def get_profile(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    認証されたユーザーのプロフィール情報を取得
    """
    return {
        "user": current_user,
        "message": "Successfully authenticated"
    }


@router.get("/protected")
def protected_endpoint(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    認証が必要な保護されたエンドポイントのサンプル
    """
    return {
        "message": f"Hello {current_user.get('name', 'User')}! This is a protected endpoint.",
        "user_id": current_user.get('sub'),
        "email": current_user.get('email')
    }