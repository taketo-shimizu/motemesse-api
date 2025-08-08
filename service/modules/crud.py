from sqlalchemy.orm import Session
from . import models


def get_user_by_id(db: Session, user_id: int):
    """ユーザーIDからユーザー情報を取得"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_auth0_id(db: Session, auth0_id: str):
    """Auth0 IDからユーザー情報を取得"""
    return db.query(models.User).filter(models.User.auth0_id == auth0_id).first()


def get_target_by_id(db: Session, target_id: int):
    """ターゲットIDから相手の女性情報を取得"""
    return db.query(models.Target).filter(models.Target.id == target_id).first()


def get_user_targets(db: Session, user_id: int):
    """ユーザーIDから全てのターゲット情報を取得"""
    return db.query(models.Target).filter(models.Target.user_id == user_id).all()


def create_user(db: Session, auth0_id: str, name: str, email: str, **kwargs):
    """新規ユーザーを作成"""
    db_user = models.User(auth0_id=auth0_id, name=name, email=email, **kwargs)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_target(db: Session, user_id: int, name: str, **kwargs):
    """新規ターゲットを作成"""
    db_target = models.Target(
        user_id=user_id,
        name=name,
        **kwargs
    )
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target


def update_user(db: Session, user_id: int, **kwargs):
    """ユーザー情報を更新"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def update_target(db: Session, target_id: int, **kwargs):
    """ターゲット情報を更新"""
    db_target = get_target_by_id(db, target_id)
    if not db_target:
        return None
    
    for key, value in kwargs.items():
        if hasattr(db_target, key):
            setattr(db_target, key, value)
    
    db.commit()
    db.refresh(db_target)
    return db_target


def create_conversation(db: Session, user_id: int, target_id: int, female_message: str, male_reply: str):
    """新規会話を作成"""
    db_conversation = models.Conversation(
        user_id=user_id,
        target_id=target_id,
        female_message=female_message,
        male_reply=male_reply
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def get_conversations(db: Session, user_id: int, target_id: int):
    """ユーザーとターゲット間の会話履歴を取得"""
    return db.query(models.Conversation).filter(
        models.Conversation.user_id == user_id,
        models.Conversation.target_id == target_id
    ).order_by(models.Conversation.created_at.asc()).all()


def get_conversation_by_id(db: Session, conversation_id: int):
    """会話IDから会話情報を取得"""
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()