from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ...modules.database import get_db
from ...modules import crud

router = APIRouter(prefix="/api/users", tags=["users"])


class UpdateToneRequest(BaseModel):
    user_id: int
    tone: int


class UserResponse(BaseModel):
    id: int
    auth0_id: Optional[str]
    name: Optional[str]
    email: str
    age: Optional[int]
    job: Optional[str]
    hobby: Optional[str]
    residence: Optional[str]
    work_place: Optional[str]
    blood_type: Optional[str]
    education: Optional[str]
    work_type: Optional[str]
    holiday: Optional[str]
    marriage_history: Optional[str]
    has_children: Optional[str]
    smoking: Optional[str]
    drinking: Optional[str]
    living_with: Optional[str]
    marriage_intention: Optional[str]
    self_introduction: Optional[str]
    tone: int

    class Config:
        from_attributes = True


@router.put("/tone")
def update_user_tone(
    request: UpdateToneRequest,
    db: Session = Depends(get_db)
):
    """
    ユーザーのトーン設定を更新
    
    - **user_id**: ユーザーID
    - **tone**: トーン設定 (0=丁寧な敬語, 1=丁寧なタメ口, 2=カジュアルな敬語, 3=カジュアルなタメ口)
    """
    # トーン値のバリデーション
    if request.tone < 0 or request.tone > 3:
        raise HTTPException(
            status_code=400,
            detail="Tone must be between 0 and 3"
        )
    
    # ユーザー存在確認
    user = crud.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # トーン更新
    updated_user = crud.update_user(db, request.user_id, tone=request.tone)
    
    if not updated_user:
        raise HTTPException(
            status_code=500,
            detail="Failed to update user tone"
        )
    
    return UserResponse.from_orm(updated_user)


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    ユーザー情報を取得
    """
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user) 