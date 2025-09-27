import datetime
from pydantic import BaseModel, Field
from typing import Optional

class PublishStatus(BaseModel):
    """
    An immutable representation of a published/unpublished date as well as some
    extra metadata that can be set for more complex publishing needs.
    """
    published: bool = Field(default=False)
    effect_date_time: datetime.datetime
    override: bool = Field(default=False)
    notes: Optional[str] = Field(default="")

    def __eq__(self, other):
        if not isinstance(other, PublishStatus):
            return NotImplemented
        return (self.published == other.published and
                self.effect_date_time == other.effect_date_time and
                self.override == other.override and
                self.notes == other.notes)

    def __hash__(self):
        return hash((self.published, self.effect_date_time, self.override, self.notes))

    def __str__(self):
        override_str = "(Override) " if self.override else ""
        published_str = "Published" if self.published else "Unpublished"
        return f"{override_str}{published_str}:{self.effect_date_time}"

    def __lt__(self, other):
        if not isinstance(other, PublishStatus):
            return NotImplemented
        if self.effect_date_time < other.effect_date_time:
            return True
        if self.effect_date_time > other.effect_date_time:
            return False
        if not self.override and other.override:
            return True
        if self.override and not other.override:
            return False
        if not self.published and other.published:
            return True
        if self.published and not other.published:
            return False
        return False

    class Config:
        from_attributes = True