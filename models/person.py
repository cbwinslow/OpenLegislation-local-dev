from pydantic import BaseModel
from typing import Optional

from .person_name import PersonName

class Person(BaseModel):
    person_id: Optional[int] = None
    name: Optional[PersonName] = None
    email: Optional[str] = None
    img_name: Optional[str] = None

    def __init__(self, person_id: int = None, name: PersonName = None,
                 email: str = None, img_name: str = None, **data):
        if img_name is None or img_name.strip() == "":
            img_name = "no_image.jpg"
        super().__init__(person_id=person_id, name=name, email=email, img_name=img_name, **data)

    def get_suggested_image_file_name(self) -> str:
        temp = f"{self.person_id}_{self.name.first_name}_{self.name.last_name}.jpg"
        # TODO: remove accented characters - RegexUtils.removeAccentedCharacters(temp)
        return temp

    def __lt__(self, other: 'Person'):
        if self.name != other.name:
            return self.name < other.name
        return self.person_id < other.person_id