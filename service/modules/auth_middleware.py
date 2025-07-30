from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from .auth0_verify import auth0_verifier

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    認証トークンからユーザー情報を取得
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required"
        )
    
    token = credentials.credentials
    payload = auth0_verifier.verify_token(token)
    
    return {
        'sub': payload.get('sub'),
        'email': payload.get('email'),
        'name': payload.get('name'),
        'picture': payload.get('picture'),
        'email_verified': payload.get('email_verified', False)
    }


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    認証が必要なエンドポイント用のデペンデンシー
    """
    return get_current_user(credentials)