from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import joinedload

from ..models import Ticket, Chat
from ..deps import db_dependency, user_dependency

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"]
)

class TicketPatchRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

@router.get("/")
async def get_tickets(db: db_dependency, user: user_dependency):
    tickets = db.query(Ticket).join(Chat).filter(
        Chat.user_id == user.get("id")
    ).all()
    return tickets

@router.get("/{ticket_id}")
async def get_ticket(ticket_id: int, db: db_dependency, user: user_dependency):
    ticket = db.query(Ticket).join(Chat).filter(
        Chat.user_id == user.get("id")
    ).filter(
        Ticket.id == ticket_id
    ).first()
    
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket

@router.patch("/{ticket_id}", status_code=status.HTTP_200_OK)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketPatchRequest,
    db: db_dependency,
    user: user_dependency
):
    # Find ticket and verify ownership through chat relationship
    ticket = db.query(Ticket).join(Chat).filter(
        Chat.user_id == user.get("id")
    ).filter(
        Ticket.id == ticket_id
    ).first()
    
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update only provided fields
    if ticket_update.title is not None:
        ticket.title = ticket_update.title
    if ticket_update.description is not None:
        ticket.description = ticket_update.description
    if ticket_update.status is not None:
        ticket.status = ticket_update.status
    
    db.commit()
    db.refresh(ticket)
    return ticket

