from pydantic import BaseModel
from typing import Optional

from .bill_id import BillId

class AgendaInfoCommitteeItem(BaseModel):
    bill_id: Optional[BillId] = None
    message: Optional[str] = None

    def __eq__(self, other):
        if not isinstance(other, AgendaInfoCommitteeItem):
            return False
        return self.bill_id == other.bill_id and self.message == other.message

    def __hash__(self):
        return hash((self.bill_id, self.message))

    # Basic Getters/Setters
    def get_bill_id(self) -> Optional[BillId]:
        return self.bill_id

    def set_bill_id(self, bill_id: BillId):
        self.bill_id = bill_id

    def get_message(self) -> Optional[str]:
        return self.message

    def set_message(self, message: str):
        self.message = message