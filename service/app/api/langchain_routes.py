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
    intent: Optional[str] = None  # 'continue' or 'appointment'


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
        # データベースから会話履歴を取得（ない場合は空リスト）
        conversation = crud.get_conversation(db, user_id=user_id, target_id=target_id)
        if not conversation:
            conversation = []  # 会話履歴がない場合は空リストを使用
        
        # maleの返信件数を取得
        message_count = len(conversation)
        
        print(user.tone, 'user.tone')
        # user.toneを文字列に変換
        user_tone_text = get_tone_text(user.tone)
        print(user_tone_text, 'user_tone_text')
        # 2. LangChainでプロンプトを構築
        output_parser = PydanticOutputParser(pydantic_object=ReplyResponse)
        # メッセージの文字数を計算
        message_length = len(message)
        # 会話履歴の整形（直近10件）
        if conversation:
            history_items = conversation[-20:] if len(conversation) > 20 else conversation
            conversation_history_text = "\n".join([
                f"彼女: {c.female_message}\nあなた: {c.male_reply}" for c in history_items
            ])
        else:
            conversation_history_text = "（これが最初のメッセージです）"
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは男性ユーザーがマッチングアプリでデートアポイントメントを獲得するための返信候補を生成するAIです。実戦で検証された恋愛戦略に基づき、相手のタイプと会話段階に応じて最適なアプローチを選択します。
ユーザー情報:
{user_profile}
相手の女性情報:
{target_profile}

## 入力情報
- ユーザー情報: {user_profile}
- 相手の女性情報: {target_profile}
- 相手の最新メッセージ: {message}
- 返信通数: {message_count}通目
- 会話履歴: {conversation_history}
- 希望する口調: {user_tone}

## 統合戦略: 適応型4段階アプローチ
### **Stage 1: 初回接触（1-2通目）**
**目標:** 相手が返信したくなる第一印象の構築
**戦略選択基準:**
- **慎重派アプローチ**: プロフィール抽象的 OR 就活中・多忙 OR 慎重な印象
- **積極派アプローチ**: プロフィール具体的 AND アクティブ系 AND 明確な話題
**慎重派パターン（やました式）:**
- 質問完全回避、相手に考える負担をかけない
- 「よければメッセージから仲良くしてください」等の承諾ベース締め
- 場所話題への軽い布石のみ配置
**積極派パターン（ヘルガ式）:**
- 具体的で答えやすい質問1つのみ許可
- 例: 「最近どんなお店に行きました？」「どのアーティスト目当てでした？」
### **Stage 2-3: 関係構築・信頼深化（3-6通目）**
**目標:** 場所情報収集と心理的距離の縮小
**共通戦略:**
- **段階的深掘り**: 表面情報→具体的詳細→感情・体験の共有
- **場所誘導**: 職場エリア→活動範囲→好きな店ジャンル
- **戦略的自己開示**: 「僕も○○好きで」等の軽い共通点アピール
- **共感強化**: 相手の体験や感情に具体的に共感
### **Stage 4: アポ獲得（7通目以降）**
**目標:** 自然で断りにくいデート提案
**ヘルガ式黄金フォーマット:**
会話の流れからの自然な提案 + 具体的店舗名 + 2択日程 + 段取りアピール
例: 「話に出た○○のカフェ、△△というお店知ってるので今度一緒に行きませんか？土曜と日曜、どちらがご都合よろしいですか？お店は調べておきますね。」
## 相手タイプ別アプローチ
### **カフェ・インテリア系女性**
- **深掘り方向**: 内装・写真映え・雰囲気への興味
- **提案スタイル**: 昼間の落ち着いたカフェデート
- **段取りアピール**: 「一緒に写真撮りましょう」「内装素敵なお店調べておきます」
### **アクティブ・エネルギッシュ系女性**
- **深掘り方向**: 体験談・盛り上がり・複数趣味の連結
- **提案スタイル**: 夜のスポーツバー・居酒屋
- **段取りアピール**: 「盛り上がりそうなお店見つけておきます」
### **インドア・慎重派女性**
- **深掘り方向**: 状況への配慮・息抜き提案
- **提案スタイル**: 平日夕方の短時間カフェ
- **段取りアピール**: 「静かで落ち着けるお店を」「息抜きがてらに」
### **ゲーム・アニメ系女性**
- **深掘り方向**: 専門用語・推しキャラでの盛り上がり
- **提案スタイル**: オンライン交流→オフライン移行の2段階
- **段取りアピール**: 「まずはオンラインで→慣れたらカフェで語りましょう」
## 制約条件
### **質問制限（段階別適用）**
- **初期段階（1-3通目）**: 相手タイプに応じて0-1個（慎重派は0個、積極派は1個まで）
- **展開段階（4-6通目）**: 場所・詳細確認の軽い質問1個まで
- **アポ打診段階（7通目以降）**: 日程調整の選択式質問1個まで
### **文字数・記号基準**
- **基本**: 80-150文字を目安（デート提案時は最大180文字まで許容）
- **記号・絵文字**: 各候補2個まで
- **段階的調整**: 最初は控えめ、相手の使用量に段階的に合わせる
### **コミュニケーション原則**
- **敬語維持**: 無理なタメ語切り替えは禁止
- **LINE交換**: 初デート後まで基本的に提案しない
- **減点回避**: 加点より失点を防ぐ安全運転
- **誠実さ重視**: 奇策・ユーモアより信頼感を最優先
## 生成指示
以下の手順で返信を生成してください：
1. **相手タイプの判定**（慎重派 or 積極派）
2. **会話段階の分析**（初回/関係構築/信頼深化/アポ獲得）
3. **最新メッセージの意図分析**
4. **最適戦略の選択**（やました式 or ヘルガ式 or ハイブリッド）
5. **3種類の返信候補生成**（カジュアル・丁寧・ユーモア、各80-150文字）
## 安全ガイドライン
- 18歳未満への対応禁止
- 初回デートは公共の場所、60-90分以内
- 相手の境界線と意向を最優先
- 差別的表現や過度な身体的言及の禁止
{format_instructions}"""),
            ("system", "これまでの会話履歴:\n{conversation_history}"),
            ("human", "女性からのメッセージ: {message}")
        ])
        # 3. OpenAI GPT-4oで返信生成
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
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
            "message_count": message_count,
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
            ("system", """あなたは初回メッセージで魅力的な第一印象を与え、相手が返信したくなる挨拶を作成する専門AIです。やました式（負担軽減）とヘルガ式（具体性重視）を統合し、相手のタイプに応じて最適なアプローチを選択します。
            
## 入力情報
- ユーザー情報: {user_profile}
- 相手の女性情報: {target_profile}
- 希望する口調: {user_tone}

## 戦略判定基準
**慎重派アプローチ（やました式）を選択する条件:**
- プロフィールが抽象的（「カフェ好き」「読書好き」等の一般表現のみ）
- 就活中・多忙・仕事が忙しい等の状況表記
- 真面目・慎重・インドア派の印象
**積極派アプローチ（ヘルガ式）を選択する条件:**
- プロフィールが具体的（店名・作品名・詳細な活動描写）
- アクティブ・エネルギッシュ・社交的な印象
- 明確で話しやすい話題が存在
## 生成手順
**Step 1: タイプ判定**
{target_profile}を分析し、上記基準で慎重派・積極派を判定
**Step 2: メッセージ構成**
### **慎重派パターン（質問なし・負担軽減重視）:**
1. **冒頭:** 「マッチングありがとうございます！[ユーザー名]と申します。」
2. **共感:** 相手のプロフィール要素1つに「○○お好きなんですね」
3. **自己開示:** 「僕も」から始まる軽い共通点＋場所の布石
4. **締め:** 「よければメッセージから色々お話できたら嬉しいです。よろしくお願いいたします！」
### **積極派パターン（具体1問・興味喚起重視）:**
1. **冒頭:** 「はじめまして！」
2. **言及:** 「プロフィールで『○○』って書いてあって」＋共感理由
3. **質問:** 具体的で答えやすい質問1つのみ
## 相手タイプ別ガイド
**カフェ・インテリア系:**
- 慎重派: 「カフェ巡りお好きなんですね、僕もよく表参道のカフェに行きます。」
- 積極派: 「最近どんなお店に行かれました？」
**音楽・フェス・アクティブ系:**
- 慎重派: 「音楽フェスお好きなんですね、僕も先月○○フェス行きました。」
- 積極派: 「どのアーティスト目当てで行くことが多いんですか？」
**読書・インドア系:**
- 慎重派: 「読書がお趣味なんですね、僕も最近ビジネ書にハマってます。」
- 積極派: 「最近はどんなジャンルを読まれてるんですか？」
**ゲーム・アニメ系:**
- 慎重派: 「○○というゲームお好きなんですね、僕もどハマりしてます。」
- 積極派: 「推しキャラとかいるんですか？」
## 制約条件
**質問制限:**
- 慎重派: 0個（質問完全禁止）
- 積極派: 1個まで
**文字数:** 50-120文字（最大150文字）
**記号・絵文字:** 各メッセージ2個まで
**その他:**
- 共通点言及は1点のみ
- 場所話題の布石を必ず含める
- 外見への直接言及は避ける
## 最終チェック項目
生成後、以下を確認してください：
- 文字数が50-120文字に収まっているか
- 質問数制限を守っているか（慎重派0個、積極派1個）
- 記号・絵文字が2個以下か
- {user_tone}に口調が合っているか
- 押し付け感がないか
## 出力要件
3種類のメッセージ（カジュアル・丁寧・ユーモア）を生成し、それぞれ上記制約をすべて満たすこと。

{format_instructions}"""),
            ("human", "初回挨拶メッセージを生成してください。")
        ])
        
        # 3. OpenAI GPT-4.1-miniで初回挨拶生成
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
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