from functools import total_ordering
from pydantic import BaseModel, model_validator
from typing import Any
from unidecode import unidecode
from models.enums import Chamber

@total_ordering
class PersonName(BaseModel):
    """
    Used as a field in Person, otherwise the constructor would have 8 String arguments in a row.
    """
    full_name: str
    prefix: str
    first_name: str
    middle_name: str
    last_name: str
    suffix: str

    @model_validator(mode='before')
    @classmethod
    def _construct_prefix(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'most_recent_chamber' in data:
            chamber = data.pop('most_recent_chamber')
            if chamber == Chamber.SENATE:
                data['prefix'] = "Senator"
            else:
                data['prefix'] = "Assembly Member"
        return data

    def __lt__(self, other):
        if not isinstance(other, PersonName):
            return NotImplemented
        return (self.last_name, self.first_name, self.middle_name) < \
               (other.last_name, other.first_name, other.middle_name)

    class Config:
        frozen = True
        arbitrary_types_allowed = True

@total_ordering
class Person(BaseModel):
    person_id: int
    name: PersonName
    email: str
    img_name: str

    @model_validator(mode='before')
    @classmethod
    def _default_img_name(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get('img_name', '').strip():
            data['img_name'] = "no_image.jpg"
        return data

    @property
    def suggested_image_file_name(self) -> str:
        """
        A consistent naming convention for image names.
        This should be used when naming the image for all new legislators.
        For newer images, this will likely be the same as `getImageName`, but it may
        not be the same for older images which had a different naming conventions.
        """
        raw_name = f"{self.person_id}_{self.name.first_name}_{self.name.last_name}.jpg"
        return unidecode(raw_name)

    def __lt__(self, other):
        if not isinstance(other, Person):
            return NotImplemented
        return (self.name, self.person_id) < (other.name, other.person_id)

    class Config:
        frozen = True
        arbitrary_types_allowed = True