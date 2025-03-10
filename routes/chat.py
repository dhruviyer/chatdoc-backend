from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel

from ..models import Chat, Ticket
from ..deps import db_dependency, user_dependency
from typing import Optional
from sqlalchemy.orm import joinedload
import openai
import json
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(
    prefix="/chats",
    tags=["chat"],
)

class CreateChatRequest(BaseModel):
    messages: str

class TicketCreate(BaseModel):
    title: str
    description: str
    status: str = "OPEN"

class ChatPatchRequest(BaseModel):
    messages: Optional[str] = None
    ticket: Optional[TicketCreate] = None

@router.get("/")
async def get_chats(db: db_dependency, user: user_dependency):
    chats = db.query(Chat).options(joinedload(Chat.ticket)).filter(Chat.user_id == user.get("id")).all()
    return chats

@router.get("/{chat_id}")
async def get_chat(chat_id: int, db: db_dependency, user: user_dependency):
    chat = db.query(Chat).options(joinedload(Chat.ticket)).filter(Chat.user_id == user.get("id")).filter(Chat.id == chat_id).first()
    return chat

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_chat(db: db_dependency, user: user_dependency, chat_create_request: CreateChatRequest):
    chat = Chat(user_id=user.get("id"), messages=chat_create_request.messages)
    db.add(chat)
    db.commit()
    db.add(Ticket(chat_id=chat.id, title="My ticket", description="Ticket description", status="Pending"))
    db.commit()
    db.refresh(chat)
   

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: int, db: db_dependency, user: user_dependency):
    chat = db.query(Chat).filter(Chat.user_id == user.get("id")).filter(Chat.id == chat_id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(chat)
    db.commit()

@router.patch("/{chat_id}", status_code=status.HTTP_200_OK)
async def update_chat(
    chat_id: int, 
    chat_update: ChatPatchRequest, 
    db: db_dependency, 
    user: user_dependency
):
    chat = db.query(Chat).filter(
        Chat.user_id == user.get("id")
    ).options(joinedload(Chat.ticket)).filter(
        Chat.id == chat_id
    ).first()
    
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if chat_update.messages is not None:
        messages = json.loads(chat_update.messages)
        print(messages)
        # make a call to openai to get the response using the message history
        client = openai.OpenAI()
        openai_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        messages.append({"role": "assistant", "content": openai_response.choices[0].message.content})
        print("======")
        print(messages)
        print(json.dumps(messages))
        chat.messages = json.dumps(messages)

    if chat_update.ticket is not None:
        if chat.ticket is None:
            db.add(Ticket(chat_id=chat.id, title=chat_update.ticket.title, description=chat_update.ticket.description, status=chat_update.ticket.status))
        else:
            raise HTTPException(
                status_code=400, 
                detail="Chat already has a ticket. Use the ticket endpoint to update it."
            )
    db.commit()
    db.refresh(chat)
    chat = db.query(Chat).filter(
        Chat.user_id == user.get("id")
    ).options(joinedload(Chat.ticket)).filter(
        Chat.id == chat_id
    ).first() 
    return chat
