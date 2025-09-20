from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import json
import os
from typing import List, Optional
from pydantic import BaseModel
from openai import OpenAI

from ...modules.database import get_db
from ...modules import crud

router = APIRouter(prefix="/api/screenshot", tags=["screenshot"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ExtractedMessage(BaseModel):
    text: str
    sender: str  # 'female' or 'male'
    order: int


class ChatScreenshotRequest(BaseModel):
    images: List[str]  # List of Base64 encoded images
    userId: int
    targetId: int


class ChatScreenshotResponse(BaseModel):
    status: str
    extractedMessages: List[ExtractedMessage]
    newMessages: List[ExtractedMessage]
    savedCount: int
    pendingFemaleMessage: Optional[str]


@router.post("/analyze-chat")
async def analyze_chat_screenshot(
    request: ChatScreenshotRequest,
    db: Session = Depends(get_db)
):
    """
    チャット画面のスクリーンショットを解析してメッセージを抽出
    複数画像対応版
    """
    try:
        # ユーザーとターゲットの確認
        user = crud.get_user_by_id(db, user_id=request.userId)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        target = crud.get_target_by_id(db, target_id=request.targetId)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

        # プロンプトの準備
        system_prompt = """あなたはマッチングアプリのチャット画面からメッセージを正確に抽出する専門家です。
複数の画像が提供される場合は、全ての画像から時系列順にメッセージを統合して抽出してください。

以下のJSON形式で返してください：
{
  "messages": [
    {
      "text": "メッセージ内容",
      "sender": "female" または "male",
      "order": 1
    }
  ]
}

注意事項：
- 吹き出しの位置で送信者を判定（左側=female、右側=male）
- 複数の画像がある場合は、時系列順（上から下）に統合
- 改行も保持
- 絵文字も正確に抽出
- タイムスタンプは無視
- メッセージのみ抽出（プロフィール情報などは無視）"""

        # 複数画像用のコンテンツを構築
        user_content = [
            {
                "type": "text",
                "text": f"これら{len(request.images)}枚の画像からチャットメッセージを時系列順に抽出してください。"
            }
        ]

        # 各画像をコンテンツに追加
        for image_data in request.images:
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
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        # レスポンスの解析
        extracted_data = json.loads(response.choices[0].message.content)

        # ExtractedMessageモデルに変換
        extracted_messages = [
            ExtractedMessage(**msg) for msg in extracted_data.get('messages', [])
        ]

        # 既存の会話履歴を取得
        existing_conversations = crud.get_conversation(
            db,
            user_id=request.userId,
            target_id=request.targetId
        )
        if not existing_conversations:
            existing_conversations = []

        # 既存メッセージのテキストをセットに追加
        existing_texts = set()
        for conv in existing_conversations:
            if conv.female_message:
                existing_texts.add(conv.female_message.strip())
            if conv.male_reply:
                existing_texts.add(conv.male_reply.strip())

        # 新規メッセージを特定
        new_messages = []
        for msg in extracted_messages:
            trimmed_text = msg.text.strip()
            if trimmed_text and trimmed_text not in existing_texts:
                new_messages.append(msg)

        # 新規メッセージをデータベースに保存
        saved_count = 0
        last_female_message = ''

        for msg in new_messages:
            if msg.sender == 'female':
                # 女性のメッセージは一時保存
                last_female_message = msg.text
            elif msg.sender == 'male' and last_female_message:
                # 男性の返信と女性のメッセージをペアで保存
                crud.create_conversation(
                    db,
                    user_id=request.userId,
                    target_id=request.targetId,
                    female_message=last_female_message,
                    male_reply=msg.text
                )
                saved_count += 1
                last_female_message = ''  # リセット

        # 最後に女性のメッセージが残っている場合（返信待ち）
        pending_female_message = last_female_message if last_female_message else None

        return ChatScreenshotResponse(
            status="success",
            extractedMessages=extracted_messages,
            newMessages=new_messages,
            savedCount=saved_count,
            pendingFemaleMessage=pending_female_message
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error analyzing chat screenshot: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"チャット画像の解析中にエラーが発生しました: {str(e)}"
        )