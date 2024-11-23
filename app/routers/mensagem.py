from fastapi import APIRouter, WebSocket, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import aiofiles
import os
from datetime import datetime
import shortuuid
from database import SessionLocal
from models import Message, MessageType
from controlers.websocket_manager import manager
#from database import get_db  # Importa sua função de obter a sessão do banco de dados
from auth import * # Supondo que você tenha uma dependência para obter o usuário atual

router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Configuração para upload de arquivos
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_upload_file(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{shortuuid.uuid()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):  # 1MB chunks
            await out_file.write(content)
            
    return unique_filename

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "typing":
                await manager.notify_typing(
                    typing_user_id=user_id,
                    receiver_id=data["receiver_id"],
                    is_typing=data["is_typing"]
                )
                
            elif data["type"] == "message":
                message = Message(
                    sender_id=user_id,
                    receiver_id=data["receiver_id"],
                    content=data["content"],
                    message_type=MessageType.TEXT
                )
                db.add(message)
                db.commit()
                
                await manager.send_personal_message(
                    {
                        "type": "message",
                        "message": {
                            "id": message.id,
                            "sender_id": message.sender_id,
                            "content": message.content,
                            "created_at": message.created_at.isoformat(),
                            "message_type": message.message_type
                        }
                    },
                    data["receiver_id"]
                )
                
    except Exception as e:
        manager.disconnect(user_id)

@router.post("/upload/{receiver_id}")
async def upload_file(
    receiver_id: int,
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
        
    file_ext = os.path.splitext(file.filename)[1].lower()
    message_type = None
    
    if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
        message_type = MessageType.IMAGE
    elif file_ext == '.pdf':
        message_type = MessageType.PDF
    elif file_ext in ['.mp3', '.wav']:
        message_type = MessageType.AUDIO
    elif file_ext in ['.mp4', '.mov']:
        message_type = MessageType.VIDEO
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
        
    file_path = await save_upload_file(file)
    
    message = Message(
        sender_id=current_user_id,
        receiver_id=receiver_id,
        message_type=message_type,
        file_url=file_path,
        file_name=file.filename,
        file_size=file_size
    )
    db.add(message)
    db.commit()
    
    await manager.send_personal_message(
        {
            "type": "message",
            "message": {
                "id": message.id,
                "sender_id": message.sender_id,
                "message_type": message_type,
                "file_url": file_path,
                "file_name": message.file_name,
                "file_size": message.file_size,
                "created_at": message.created_at.isoformat()
            }
        },
        receiver_id
    )
    
    return {"message": "File uploaded successfully"}

@router.get("/messages/{other_user_id}" )
async def get_messages(
    other_user_id: int,
    current_user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    messages = db.query(Message).filter(
        (
            (Message.sender_id == current_user_id) & 
            (Message.receiver_id == other_user_id)
        ) |
        (
            (Message.sender_id == other_user_id) & 
            (Message.receiver_id == current_user_id)
        )
    ).order_by(Message.created_at.desc())\
    .offset(skip)\
    .limit(limit)\
    .all()
    
    return messages
