from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import base64
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from ...modules.database import get_db
from ...modules import crud

load_dotenv()

router = APIRouter(prefix="/api/vision", tags=["vision"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ProfileImageRequest(BaseModel):
    images: list[str]  # List of Base64 encoded images

class ProfileData(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    job: Optional[str] = None
    hobby: Optional[str] = None
    residence: Optional[str] = None
    workplace: Optional[str] = None
    bloodType: Optional[str] = None
    education: Optional[str] = None
    workType: Optional[str] = None
    holiday: Optional[str] = None
    marriageHistory: Optional[str] = None
    hasChildren: Optional[str] = None
    smoking: Optional[str] = None
    drinking: Optional[str] = None
    livingWith: Optional[str] = None
    marriageIntention: Optional[str] = None
    selfIntroduction: Optional[str] = None

class ProfileAnalysisResponse(BaseModel):
    status: str
    profile: ProfileData
    confidence: float


class ChatScreenshotRequest(BaseModel):
    image: str  # Single Base64 encoded image
    userId: int
    targetId: int


class ChatScreenshotResponse(BaseModel):
    status: str
    message: Optional[str]  # The extracted latest female message


@router.post("/analyze-profile", response_model=ProfileAnalysisResponse)
async def analyze_profile_image(request: ProfileImageRequest):
    """
    マッチングアプリのスクリーンショットからプロフィール情報を抽出
    複数画像対応版
    """
    try:
        # プロンプトの準備
        system_prompt = """あなたはマッチングアプリのプロフィール画面から情報を正確に抽出する専門家です。
複数の画像が提供される場合は、全ての画像から情報を統合して抽出してください。
画像から以下の情報を日本語で抽出してJSON形式で返してください：

{
  "name": "名前",
  "age": 年齢（数値）,
  "job": "職業",
  "hobby": "趣味",
  "residence": "居住地",
  "workplace": "勤務地",
  "bloodType": "血液型",
  "education": "学歴",
  "workType": "仕事の種類",
  "holiday": "休日",
  "marriageHistory": "結婚歴",
  "hasChildren": "子供の有無",
  "smoking": "煙草",
  "drinking": "お酒",
  "livingWith": "同居人",
  "marriageIntention": "結婚に対する意思",
  "selfIntroduction": "自己紹介文"
}

注意事項：
- 複数の画像から情報を統合してください
- 画像に表示されていない項目はnullとして返してください
- 年齢は数値型で返してください
- 各項目は日本語の文字列で返してください
- 自己紹介文は改行を含む場合があります
- マッチングアプリによって項目名が異なる場合は、最も近い項目にマッピングしてください
- 複数の画像で同じ情報が異なる場合は、最も詳細または最新と思われる情報を採用してください
"""

        # 複数画像用のコンテンツを構築
        user_content = [
            {
                "type": "text",
                "text": f"これら{len(request.images)}枚の画像からプロフィール情報を抽出して統合してください。"
            }
        ]
        
        # 各画像をコンテンツに追加
        for i, image_data in enumerate(request.images, 1):
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_data,
                    "detail": "high"
                }
            })

        # Vision APIを呼び出し
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            max_tokens=1500,  # 複数画像の場合、より多くのトークンが必要になる可能性
            response_format={"type": "json_object"}
        )

        # レスポンスの解析
        extracted_data = json.loads(response.choices[0].message.content)
        
        # ProfileDataモデルに変換
        profile_data = ProfileData(**extracted_data)
        
        # 抽出された項目数から信頼度を計算
        total_fields = 17
        extracted_fields = sum(1 for field in extracted_data.values() if field is not None)
        confidence = extracted_fields / total_fields

        return ProfileAnalysisResponse(
            status="success",
            profile=profile_data,
            confidence=confidence
        )

    except Exception as e:
        print(f"Error analyzing profile image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"画像の解析中にエラーが発生しました: {str(e)}"
        )


@router.post("/analyze-chat")
async def analyze_chat_screenshot(
    request: ChatScreenshotRequest,
    db: Session = Depends(get_db)
):
    """
    チャット画面のスクリーンショットから最新の女性メッセージを抽出
    """
    try:
        print(request.image, 'request.image')
        # ユーザーとターゲットの確認（認証目的のみ）
        user = crud.get_user_by_id(db, user_id=request.userId)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        target = crud.get_target_by_id(db, target_id=request.targetId)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

        # プロンプトの準備
        system_prompt = """あなたはマッチングアプリのチャット画面から最新の女性メッセージを抽出する専門家です。

以下のJSON形式で返してください：
{
  "latestFemaleMessage": "最新の女性メッセージ内容" または null
}

重要な判定ルール：
- 左側の吹き出しが女性（相手）のメッセージです
- 右側の吹き出しは男性（自分）のメッセージです
- 画面に表示されている最も下にある左側の吹き出し（女性メッセージ）のテキストのみを抽出してください
- 女性のメッセージが画面に存在しない場合はnullを返してください

注意事項：
- 改行も保持
- 絵文字も正確に抽出
- タイムスタンプは無視
- メッセージのみ抽出（プロフィール情報などは無視）"""

        # 単一画像用のコンテンツを構築
        user_content = [
            {
                "type": "text",
                "text": "この画像から最新（最も下にある）の女性メッセージ（左側の吹き出し）を抽出してください。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": request.image,
                    "detail": "high"
                }
            }
        ]

        # Vision APIを呼び出し
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        # レスポンスの解析
        extracted_data = json.loads(response.choices[0].message.content)
        latest_female_message = extracted_data.get('latestFemaleMessage')
        print(latest_female_message, 'latest_female_message')
        return ChatScreenshotResponse(
            status="success",
            message=latest_female_message
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing chat screenshot: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"チャット画像の解析中にエラーが発生しました: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Vision API ヘルスチェック"""
    return {"status": "ok", "service": "vision"}