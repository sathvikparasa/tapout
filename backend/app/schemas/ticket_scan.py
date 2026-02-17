"""
Schemas for ticket scan endpoint.
"""

from typing import Optional

from pydantic import BaseModel


class TicketScanResponse(BaseModel):
    success: bool
    ticket_date: Optional[str] = None
    ticket_time: Optional[str] = None
    ticket_location: Optional[str] = None
    mapped_lot_id: Optional[int] = None
    mapped_lot_name: Optional[str] = None
    mapped_lot_code: Optional[str] = None
    is_recent: bool
    sighting_id: Optional[int] = None
    users_notified: int = 0
