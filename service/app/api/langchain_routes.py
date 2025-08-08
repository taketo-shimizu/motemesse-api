from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import Field

from ...modules.database import get_db
from ...modules import crud

load_dotenv()

router = APIRouter(prefix="/api/langchain", tags=["langchain"])


class ReplyRequest(BaseModel):
    userId: int
    selectedTargetId: int
    message: str


class InitialGreetingRequest(BaseModel):
    userId: int
    selectedTargetId: int
    type: str


class Reply(BaseModel):
    id: int
    text: str


class ReplyResponse(BaseModel):
    replies: List[Reply] = Field(description="3つの返信候補")


class GenerateReplyResponse(BaseModel):
    status: str
    replies: List[Reply]
    context: dict


class GenerateInitialGreetingResponse(BaseModel):
    status: str
    replies: List[Reply]
    context: dict


@router.post("/generate-reply", response_model=GenerateReplyResponse)
async def generate_reply(request: ReplyRequest, db: Session = Depends(get_db)):
    """
    女性からのメッセージに対する返信候補を生成
    """
    try:
        # リクエストパラメータを使用
        user_id = request.userId
        target_id = request.selectedTargetId
        message = request.message
        
        print(f"リクエストパラメータ: userId={user_id}, selectedTargetId={target_id}, message={message}")
        
        # データベースからユーザー情報を取得
        user = crud.get_user_by_id(db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # データベースからターゲット情報を取得
        target = crud.get_target_by_id(db, target_id=target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        
        # 2. LangChainでプロンプトを構築
        output_parser = PydanticOutputParser(pydantic_object=ReplyResponse)
        
        # メッセージの文字数を計算
        message_length = len(message)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは恋愛コミュニケーションのアドバイザーです。
            
ユーザー情報:
- 名前: {user_name}
- 年齢: {user_age}
- 職業: {user_job}
- 趣味: {user_hobby}
- 居住地: {user_residence}
- 勤務地: {user_workplace}
- 血液型: {user_blood_type}
- 学歴: {user_education}
- 仕事の種類: {user_work_type}
- 休日: {user_holiday}
- 結婚歴: {user_marriage_history}
- 子供の有無: {user_has_children}
- 煙草: {user_smoking}
- お酒: {user_drinking}
- 一緒に住んでいる人: {user_living_with}
- 結婚に対する意思: {user_marriage_intention}
- 自己紹介: {user_self_introduction}

相手の女性情報:
- 名前: {target_name}
- 年齢: {target_age}
- 職業: {target_job}
- 趣味: {target_hobby}
- 居住地: {target_residence}
- 勤務地: {target_workplace}
- 血液型: {target_blood_type}
- 学歴: {target_education}
- 仕事の種類: {target_work_type}
- 休日: {target_holiday}
- 結婚歴: {target_marriage_history}
- 子供の有無: {target_has_children}
- 煙草: {target_smoking}
- お酒: {target_drinking}
- 一緒に住んでいる人: {target_living_with}
- 結婚に対する意思: {target_marriage_intention}
- 自己紹介: {target_self_introduction}

受信メッセージの文字数: {message_length}文字

相手の女性から送られてきたメッセージに対して、自然で魅力的な返信を3つ生成してください。
返信は以下の点を考慮してください：
1. 相手のプロフィール情報（職業、趣味、居住地、ライフスタイルなど）を考慮した内容
2. 関係を深められるような内容
3. 自然な会話の流れ
4. 適度に親しみやすさを表現
5. ユーザーのプロフィール情報も活かした返信
6. 共通点があれば自然に触れる
7. メッセージの文字数に応じた適切な長さの返信を生成：
   - 10文字以下: 短く簡潔な返信（5-15文字程度）
   - 11-30文字: 適度な長さの返信（15-40文字程度）
   - 31-60文字: しっかりとした返信（30-80文字程度）
   - 61文字以上: 丁寧で詳細な返信（50-120文字程度）
8. 受信したメッセージの時制と挨拶に合わせた返信：
   - 「おはよう」「こんにちは」「こんばんは」などの挨拶が含まれていれば、返信にも同じ時制の挨拶を含める
   - 「今日は」「昨日」「明日」などの時制表現に適切に対応した返信をする

{format_instructions}"""),
            ("human", "女性からのメッセージ: {message}")
        ])
        
        # 3. OpenAI GPT-4oで返信生成
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=api_key
        )
        
        # 4. チェーンを実行
        chain = prompt | llm | output_parser
        
        result = chain.invoke({
            "user_name": user.name or "ユーザー",
            "user_age": f"{user.age}歳" if user.age else "不明",
            "user_job": user.job or "不明",
            "user_hobby": user.hobby or "不明",
            "user_residence": user.residence or "不明",
            "user_workplace": user.work_place or "不明",
            "user_blood_type": user.blood_type or "不明",
            "user_education": user.education or "不明",
            "user_work_type": user.work_type or "不明",
            "user_holiday": user.holiday or "不明",
            "user_marriage_history": user.marriage_history or "不明",
            "user_has_children": user.has_children or "不明",
            "user_smoking": user.smoking or "不明",
            "user_drinking": user.drinking or "不明",
            "user_living_with": user.living_with or "不明",
            "user_marriage_intention": user.marriage_intention or "不明",
            "user_self_introduction": getattr(user, 'self_introduction', None) or "情報なし",
            "target_name": target.name,
            "target_age": f"{target.age}歳" if target.age else "不明",
            "target_job": target.job or "不明",
            "target_hobby": target.hobby or "不明",
            "target_residence": target.residence or "不明",
            "target_workplace": target.work_place or "不明",
            "target_blood_type": target.blood_type or "不明",
            "target_education": target.education or "不明",
            "target_work_type": target.work_type or "不明",
            "target_holiday": target.holiday or "不明",
            "target_marriage_history": target.marriage_history or "不明",
            "target_has_children": target.has_children or "不明",
            "target_smoking": target.smoking or "不明",
            "target_drinking": target.drinking or "不明",
            "target_living_with": target.living_with or "不明",
            "target_marriage_intention": target.marriage_intention or "不明",
            "target_self_introduction": getattr(target, 'self_introduction', None) or "情報なし",
            "message": message,
            "message_length": message_length,
            "format_instructions": output_parser.get_format_instructions()
        })
        
        # 5. レスポンスを返す
        return GenerateReplyResponse(
            status="success",
            replies=result.replies,
            context={
                "userName": user.name or "ユーザー",
                "targetName": target.name,
                "userAge": user.age,
                "targetAge": target.age
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate replies: {str(e)}")


@router.post("/generate-initial-greeting", response_model=GenerateInitialGreetingResponse)
async def generate_initial_greeting(request: InitialGreetingRequest, db: Session = Depends(get_db)):
    """
    初回挨拶メッセージを生成
    """
    try:
        # リクエストパラメータを使用
        user_id = request.userId
        target_id = request.selectedTargetId
        tone_style = request.type
        
        print(f"リクエストパラメータ: userId={user_id}, selectedTargetId={target_id}, type={tone_style}")
        
        # データベースからユーザー情報を取得
        user = crud.get_user_by_id(db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # データベースからターゲット情報を取得
        target = crud.get_target_by_id(db, target_id=target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        
        # 2. LangChainでプロンプトを構築（初回挨拶専用）
        output_parser = PydanticOutputParser(pydantic_object=ReplyResponse)
        
        # トーンスタイルの説明を作成
        tone_descriptions = {
            "軽いノリのタメ口": "フレンドリーでカジュアルな感じで、相手を〜ちゃん/〜くんと呼び、タメ口で話す。絵文字や！を適度に使い、親しみやすい雰囲気を出す。",
            "真面目なタメ口": "丁寧だが堅苦しくない感じで、タメ口を使いながらも落ち着いたトーン。相手の名前を呼び捨てにし、誠実な印象を与える。",
            "軽いノリの敬語": "敬語を使いながらも親しみやすい雰囲気。〜さんと呼び、です/ます調を使いつつ、絵文字や！で明るさを演出する。",
            "真面目な敬語": "礼儀正しく真摯な態度で、きちんとした敬語を使う。〜さんと呼び、落ち着いた大人の雰囲気を出す。"
        }
        
        tone_description = tone_descriptions.get(tone_style, tone_descriptions["軽いノリの敬語"])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは恋愛コミュニケーションのアドバイザーです。初回挨拶メッセージの専門家として、魅力的な第一印象を与える挨拶を作成してください。
            
ユーザー情報:
- 名前: {user_name}
- 年齢: {user_age}
- 職業: {user_job}
- 趣味: {user_hobby}
- 居住地: {user_residence}
- 勤務地: {user_workplace}
- 血液型: {user_blood_type}
- 学歴: {user_education}
- 仕事の種類: {user_work_type}
- 休日: {user_holiday}
- 結婚歴: {user_marriage_history}
- 子供の有無: {user_has_children}
- 煙草: {user_smoking}
- お酒: {user_drinking}
- 一緒に住んでいる人: {user_living_with}
- 結婚に対する意思: {user_marriage_intention}
- 自己紹介: {user_self_introduction}

相手の女性情報:
- 名前: {target_name}
- 年齢: {target_age}
- 職業: {target_job}
- 趣味: {target_hobby}
- 居住地: {target_residence}
- 勤務地: {target_workplace}
- 血液型: {target_blood_type}
- 学歴: {target_education}
- 仕事の種類: {target_work_type}
- 休日: {target_holiday}
- 結婚歴: {target_marriage_history}
- 子供の有無: {target_has_children}
- 煙草: {target_smoking}
- お酒: {target_drinking}
- 一緒に住んでいる人: {target_living_with}
- 結婚に対する意思: {target_marriage_intention}
- 自己紹介: {target_self_introduction}

トーンスタイル: {tone_style}
トーンの説明: {tone_description}

初回挨拶メッセージを3つ生成してください。
以下の点を考慮してください：
1. 第一印象が良く、親しみやすい挨拶
2. 相手のプロフィール情報（職業、趣味、居住地、ライフスタイルなど）に関連した話題を自然に含める
3. 相手が返信しやすい質問や話題を含める
4. 適度な距離感を保ちつつ、興味を示す内容
5. ユーザーのプロフィール情報を活かした自己紹介を含める
6. 共通点があれば自然に触れる
7. 長すぎず短すぎない適切な長さ（30-80文字程度）
8. 相手のライフスタイルに合わせたトーンで作成
9. 指定されたトーンスタイル（{tone_style}）を厳密に守って作成

{format_instructions}"""),
            ("human", "初回挨拶メッセージを生成してください。")
        ])
        
        # 3. OpenAI GPT-4oで初回挨拶生成
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=api_key
        )
        
        # 4. チェーンを実行
        chain = prompt | llm | output_parser
        
        result = chain.invoke({
            "user_name": user.name or "ユーザー",
            "user_age": f"{user.age}歳" if user.age else "不明",
            "user_job": user.job or "不明",
            "user_hobby": user.hobby or "不明",
            "user_residence": user.residence or "不明",
            "user_workplace": user.work_place or "不明",
            "user_blood_type": user.blood_type or "不明",
            "user_education": user.education or "不明",
            "user_work_type": user.work_type or "不明",
            "user_holiday": user.holiday or "不明",
            "user_marriage_history": user.marriage_history or "不明",
            "user_has_children": user.has_children or "不明",
            "user_smoking": user.smoking or "不明",
            "user_drinking": user.drinking or "不明",
            "user_living_with": user.living_with or "不明",
            "user_marriage_intention": user.marriage_intention or "不明",
            "user_self_introduction": getattr(user, 'self_introduction', None) or "情報なし",
            "target_name": target.name,
            "target_age": f"{target.age}歳" if target.age else "不明",
            "target_job": target.job or "不明",
            "target_hobby": target.hobby or "不明",
            "target_residence": target.residence or "不明",
            "target_workplace": target.work_place or "不明",
            "target_blood_type": target.blood_type or "不明",
            "target_education": target.education or "不明",
            "target_work_type": target.work_type or "不明",
            "target_holiday": target.holiday or "不明",
            "target_marriage_history": target.marriage_history or "不明",
            "target_has_children": target.has_children or "不明",
            "target_smoking": target.smoking or "不明",
            "target_drinking": target.drinking or "不明",
            "target_living_with": target.living_with or "不明",
            "target_marriage_intention": target.marriage_intention or "不明",
            "target_self_introduction": getattr(target, 'self_introduction', None) or "情報なし",
            "tone_style": tone_style,
            "tone_description": tone_description,
            "format_instructions": output_parser.get_format_instructions()
        })
        
        # 5. レスポンスを返す
        return GenerateInitialGreetingResponse(
            status="success",
            replies=result.replies,
            context={
                "userName": user.name or "ユーザー",
                "targetName": target.name,
                "userAge": user.age,
                "targetAge": target.age,
                "messageType": "initial_greeting",
                "toneStyle": tone_style
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate initial greeting: {str(e)}")


@router.post("/chat")
def chat_completion(
    request: dict
):
    """
    LangChainを使用したチャット処理エンドポイント
    """
    message = request.get("message", "")
    
    return {
        "response": f"LangChain応答: {message}",
        "processed_by": "langchain-api"
    }


@router.post("/generate")
def generate_content(
    request: dict
):
    """
    LangChainを使用したコンテンツ生成エンドポイント
    """
    prompt = request.get("prompt", "")
    
    return {
        "generated_content": f"生成されたコンテンツ: {prompt}",
        "model": "langchain-model"
    }