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


def format_user_profile(user) -> str:
    """ユーザープロフィール情報を整形"""
    return f"""- 名前: {user.name or "ユーザー"}
- 年齢: {f"{user.age}歳" if user.age else "不明"}
- 職業: {user.job or "不明"}
- 趣味: {user.hobby or "不明"}
- 居住地: {user.residence or "不明"}
- 勤務地: {user.work_place or "不明"}
- 血液型: {user.blood_type or "不明"}
- 学歴: {user.education or "不明"}
- 仕事の種類: {user.work_type or "不明"}
- 休日: {user.holiday or "不明"}
- 結婚歴: {user.marriage_history or "不明"}
- 子供の有無: {user.has_children or "不明"}
- 煙草: {user.smoking or "不明"}
- お酒: {user.drinking or "不明"}
- 一緒に住んでいる人: {user.living_with or "不明"}
- 結婚に対する意思: {user.marriage_intention or "不明"}
- 自己紹介: {getattr(user, 'self_introduction', None) or "情報なし"}"""


def format_target_profile(target) -> str:
    """ターゲットプロフィール情報を整形"""
    return f"""- 名前: {target.name}
- 年齢: {f"{target.age}歳" if target.age else "不明"}
- 職業: {target.job or "不明"}
- 趣味: {target.hobby or "不明"}
- 居住地: {target.residence or "不明"}
- 勤務地: {target.work_place or "不明"}
- 血液型: {target.blood_type or "不明"}
- 学歴: {target.education or "不明"}
- 仕事の種類: {target.work_type or "不明"}
- 休日: {target.holiday or "不明"}
- 結婚歴: {target.marriage_history or "不明"}
- 子供の有無: {target.has_children or "不明"}
- 煙草: {target.smoking or "不明"}
- お酒: {target.drinking or "不明"}
- 一緒に住んでいる人: {target.living_with or "不明"}
- 結婚に対する意思: {target.marriage_intention or "不明"}
- 自己紹介: {getattr(target, 'self_introduction', None) or "情報なし"}"""


def get_tone_text(tone_value) -> str:
    """トーン値を文字列に変換"""
    tone_mapping = {
        0: "敬語",
        1: "タメ口", 
    }
    return tone_mapping.get(tone_value, "敬語")

router = APIRouter(prefix="/api/langchain", tags=["langchain"])


class ReplyRequest(BaseModel):
    userId: int
    selectedTargetId: int
    message: str


class InitialGreetingRequest(BaseModel):
    userId: int
    selectedTargetId: int


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
        
        
        # データベースから会話履歴を取得
        conversation = crud.get_conversation(db, user_id=user_id, target_id=target_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        print(user.tone, 'user.tone')
        
        # user.toneを文字列に変換
        user_tone_text = get_tone_text(user.tone)
        print(user_tone_text, 'user_tone_text')
        
        # 2. LangChainでプロンプトを構築
        output_parser = PydanticOutputParser(pydantic_object=ReplyResponse)
        
        # メッセージの文字数を計算
        message_length = len(message)
        
        # 会話履歴の整形（直近10件）
        history_items = conversation[-10:] if len(conversation) > 10 else conversation
        conversation_history_text = "\n".join([
            f"彼女: {c.female_message}\nあなた: {c.male_reply}" for c in history_items
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは男性ユーザーがマッチングアプリでデートアポイントメントを獲得するための返信候補を生成するAIです。
            
ユーザー情報:
{user_profile}

相手の女性情報:
{target_profile}

## 基本方針
以下の実証されたテクニックに基づき、自然で効果的な返信を3種類（カジュアル・丁寧・ユーモア）生成してください。
口調は: {user_tone}に合わせて生成してください。
## 核心戦略：4段階アプローチ
1. **プロフィール要素の具体的な拾い上げ**
2. **共感と軽い自己開示による親近感構築**
3. **場所・活動話題への自然な誘導**
4. **具体的なデート提案（2択形式）**
## 返信生成の重要原則
### 【会話展開テクニック】
- **プロフィール深掘り**: 趣味・関心事の具体的詳細を引き出す
- **場所情報収集**: よく行く場所・職場エリア・活動範囲を自然に聞く
- **共通点アピール**: 「僕も○○好きで」という軽い自己開示
- **参加感創出**: 相手の意見や好みを尊重する姿勢
### 【デート誘導戦略】
- **3-5通目で提案**: メッセージは親睦でなくアポ獲得手段
- **場所話題から直結**: 「○○(場所)の△△(店/スポット)一緒に行きませんか？」
- **2択日程提示**: 「土曜か日曜なら空いてますが、どちらがご都合よろしいですか？」
- **段取り力アピール**: 「お店調べておきます」「予約しておきます」
### 【相手タイプ別アプローチ】
**カフェ・インテリア系女性**
- 内装・雰囲気への興味を示す
- 写真映えスポットの情報交換
- 落ち着いた昼カフェデートを提案
**アクティブ・スポーツ系女性** 
- 体験談での盛り上がりを重視
- スポーツバー・フェス等の活気ある場所を選択
- 夜の飲みデートを中心に提案
**インドア・読書系女性**
- 相手の状況（就活等）への配慮を示す
- 静かで落ち着ける環境を優先
- カフェでの軽いお茶デートから開始
**ゲーム・アニメ系女性**
- オンライン交流を経由したステップアプローチ
- 共通の推しキャラ・作品での盛り上がり
- オフライン移行は段階的に提案
### 【会話継続の要点】
- **LINE交換は後回し**: 初デート後まで基本的に不要
- **減点回避**: 加点より失点を防ぐ安全運転
- **相手ペース尊重**: 押し付けがましさを避ける
## 生成指示
女性からのメッセージ内容と設定されたプロフィール情報を基に：
1. **メッセージの意図・感情を分析**
2. **プロフィール情報から関連要素を抽出** 
3. **現在の会話段階を判定**（初期/展開/アポ打診段階）
4. **最適な返信戦略を選択**
5. **3種類の返信候補を生成**（各150文字以内）
各候補は自然で実践的、かつアポイントメント獲得という最終目標に向けた戦略的なものとしてください。

{format_instructions}"""),
            ("system", "これまでの会話履歴:\n{conversation_history}"),
            ("human", "女性からのメッセージ: {message}")
        ])
        
        # 3. OpenAI GPT-4oで返信生成
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=1.0,
            api_key=api_key
        )
        
        # 4. チェーンを実行
        chain = prompt | llm | output_parser
        
        result = chain.invoke({
            "user_profile": format_user_profile(user),
            "target_profile": format_target_profile(target),
            "user_tone": user_tone_text,
            "message": message,
            "message_length": message_length,
            "conversation_history": conversation_history_text,
            "format_instructions": output_parser.get_format_instructions()
        })

        print(user.smoking, 'user')
        
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
        
        print(f"リクエストパラメータ: userId={user_id}, selectedTargetId={target_id}")
        
        # データベースからユーザー情報を取得
        user = crud.get_user_by_id(db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # データベースからターゲット情報を取得
        target = crud.get_target_by_id(db, target_id=target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        
        # user.toneを文字列に変換
        user_tone_text = get_tone_text(user.tone)
        
        # 2. LangChainでプロンプトを構築（初回挨拶専用）
        output_parser = PydanticOutputParser(pydantic_object=ReplyResponse)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは恋愛コミュニケーションのアドバイザーです。初回挨拶メッセージの専門家として、魅力的な第一印象を与える挨拶を作成してください。
            
ユーザー情報:
{user_profile}

相手の女性情報:
{target_profile}

初回挨拶メッセージを3つ生成してください。
### 【初回メッセージ対応】
- **質問は控えめに**: 相手に負担をかけない簡潔な反応
- **記号・顔文字は最小限**: 1メッセージあたり最大2個まで
- **承諾ベース**: 「○○について話せたら嬉しいです」形式
- **誠実さ重視**: 奇策より信頼感を優先
以下の点を考慮してください：
1. 第一印象が良く、親しみやすい挨拶
2. 相手のプロフィール情報（職業、趣味、居住地、ライフスタイルなど）に関連した話題を自然に含める
3. 相手が返信しやすい質問や話題を含める
4. 適度な距離感を保ちつつ、興味を示す内容
5. ユーザーのプロフィール情報を活かした自己紹介を含める
6. 共通点があれば自然に触れる
7. 長すぎず短すぎない適切な長さ（30-80文字程度）
8. 相手のライフスタイルに合わせたトーンで作成
9. 口調は: {user_tone}に合わせて生成してください。

{format_instructions}"""),
            ("human", "初回挨拶メッセージを生成してください。")
        ])
        
        # 3. OpenAI GPT-4oで初回挨拶生成
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=1.0,
            api_key=api_key
        )
        
        # 4. チェーンを実行
        chain = prompt | llm | output_parser
        
        result = chain.invoke({
            "user_profile": format_user_profile(user),
            "target_profile": format_target_profile(target),
            "user_tone": user_tone_text,
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
                "toneStyle": user_tone_text
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