from enum import Enum


class BillStatusType(str, Enum):
    INTRODUCED = ("INTRODUCED", "Introduced")
    IN_ASSEMBLY_COMM = ("IN_ASSEMBLY_COMM", "In Assembly Committee")
    IN_SENATE_COMM = ("IN_SENATE_COMM", "In Senate Committee")
    ASSEMBLY_FLOOR = ("ASSEMBLY_FLOOR", "Assembly Floor Calendar")
    SENATE_FLOOR = ("SENATE_FLOOR", "Senate Floor Calendar")
    PASSED_ASSEMBLY = ("PASSED_ASSEMBLY", "Passed Assembly")
    PASSED_SENATE = ("PASSED_SENATE", "Passed Senate")
    DELIVERED_TO_GOV = ("DELIVERED_TO_GOV", "Delivered to Governor")
    SIGNED_BY_GOV = ("SIGNED_BY_GOV", "Signed by Governor")
    VETOED = ("VETOED", "Vetoed")
    STRICKEN = ("STRICKEN", "Stricken")
    LOST = ("LOST", "Lost")
    SUBSTITUTED = ("SUBSTITUTED", "Substituted")
    ADOPTED = ("ADOPTED", "Adopted")
    POCKET_APPROVAL = ("POCKET_APPROVAL", "Pocket Approval")

    def __new__(cls, value: str, description: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._description = description
        return obj

    @property
    def description(self) -> str:
        return self._description

    def get_desc(self) -> str:
        return self._description
