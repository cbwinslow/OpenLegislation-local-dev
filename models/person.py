from pydantic import BaseModel

from .person_name import PersonName

class Person(BaseModel):
    person_id: int
    name: PersonName
    email: str
    img_name: str

    def __init__(self, person_id: int, name: PersonName, email: str, img_name: str, **data):
        if not img_name:
            img_name = "no_image.jpg"
        super().__init__(person_id=person_id, name=name, email=email, img_name=img_name, **data)

    def get_suggested_image_file_name(self) -> str:
        temp = f"{self.person_id}_{self.name.first_name}_{self.name.last_name}.jpg"
        # TODO: remove accented characters
        return temp

    def __lt__(self, other: 'Person'):
        if self.name != other.name:
            return self.name < other.name
        return self.person_id < other.person_id