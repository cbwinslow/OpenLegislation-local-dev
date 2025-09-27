from enum import Enum

class CacheType(Enum):
    """
    Content caches store various types of data. The cache types enumerated here should
    be able to manage themselves, have configurable sizes, and have functionality to warm
    up upon request.
    """
    AGENDA = "AGENDA"
    API_USER = "API_USER"
    BILL = "BILL"
    BILL_INFO = "BILL_INFO"
    CALENDAR = "CALENDAR"
    COMMITTEE = "COMMITTEE"
    FULL_MEMBER = "FULL_MEMBER"
    LAW = "LAW"
    SESSION_MEMBER = "SESSION_MEMBER"
    SHORTNAME = "SHORTNAME"

class Chamber(Enum):
    """
    Enumeration of the different legislative chambers.
    """
    SENATE = 'S'
    ASSEMBLY = 'A'

    @property
    def abbreviation(self):
        return self.value

    def as_sql_enum(self):
        return self.name.lower()

    def opposite(self):
        return Chamber.ASSEMBLY if self == Chamber.SENATE else Chamber.SENATE

    @staticmethod
    def get_value(value: str):
        if value is None:
            raise ValueError("Supplied value cannot be null when mapping to Chamber.")
        return Chamber[value.strip().upper()]

class BillType(Enum):
    S = (Chamber.SENATE, "Senate", False)
    J = (Chamber.SENATE, "Regular and Joint", True)
    B = (Chamber.SENATE, "Concurrent", True)
    R = (Chamber.SENATE, "Rules and Extraordinary Session", True)
    A = (Chamber.ASSEMBLY, "Assembly", False)
    K = (Chamber.ASSEMBLY, "Regular", True)
    C = (Chamber.ASSEMBLY, "Concurrent", True)
    E = (Chamber.ASSEMBLY, "Rules and Extraordinary Session", True)
    L = (Chamber.ASSEMBLY, "Joint", True)

    def __init__(self, chamber, name, resolution):
        self._chamber = chamber
        self._name = name
        self._resolution = resolution

    @property
    def chamber(self):
        return self._chamber

    @property
    def bill_name(self):
        return self._name

    @property
    def is_resolution(self):
        return self._resolution

class BillStatusType(Enum):
    """
    An enumeration of the different stages a bill can be in. This listing is not meant to be
    granular but rather provides a high level bill status to the end user. This status should
    be determined by parsing the actions list. It is worth noting that bills will generally
    cycle through these statuses as they pass/die in a house and move to the other one.
    """
    INTRODUCED = "Introduced"
    IN_ASSEMBLY_COMM = "In Assembly Committee"
    IN_SENATE_COMM = "In Senate Committee"
    ASSEMBLY_FLOOR = "Assembly Floor Calendar"
    SENATE_FLOOR = "Senate Floor Calendar"
    PASSED_ASSEMBLY = "Passed Assembly"
    PASSED_SENATE = "Passed Senate"
    DELIVERED_TO_GOV = "Delivered to Governor"
    SIGNED_BY_GOV = "Signed by Governor"
    VETOED = "Vetoed"
    STRICKEN = "Stricken"
    LOST = "Lost"
    SUBSTITUTED = "Substituted"
    ADOPTED = "Adopted"
    POCKET_APPROVAL = "Pocket Approval"

    @property
    def desc(self):
        return self.value

class BillTextFormat(Enum):
    """
    Enumerates the possible formats of bill text
    """
    PLAIN = "PLAIN"
    HTML = "HTML"
    TEMPLATE = "TEMPLATE"

class SobiLineType(Enum):
    """
    SOBI files that are in the line item format contain character codes that indicate the type
    of information that is to be applied. The SobiLineType enum maps the character codes for
    easy use within the code base.
    """
    BILL_INFO = '1'
    LAW_SECTION = '2'
    TITLE = '3'
    BILL_EVENT = '4'
    SAME_AS = '5'
    SPONSOR = '6'
    CO_SPONSOR = '7'
    MULTI_SPONSOR = '8'
    PROGRAM_INFO = '9'
    ACT_CLAUSE = 'A'
    LAW = 'B'
    SUMMARY = 'C'
    SPONSOR_MEMO = 'M'
    VETO_APPROVE_MEMO = 'O'
    RESOLUTION_TEXT = 'R'
    TEXT = 'T'
    VOTE_MEMO = 'V'

    @property
    def type_code(self):
        return self.value

    @classmethod
    def from_code(cls, type_code: str):
        for item in cls:
            if item.value == type_code:
                return item
        return None

class BillTextType(Enum):
    RESOLUTION = (SobiLineType.RESOLUTION_TEXT, "RESO TEXT")
    BILL = (SobiLineType.TEXT, "BTXT")
    SPONSOR_MEMO = (SobiLineType.SPONSOR_MEMO, "MTXT")
    VETO_APPROVAL = (SobiLineType.VETO_APPROVE_MEMO, "VETO|APPROVAL")

    def __init__(self, sobi_line_type, type_string):
        self._sobi_line_type = sobi_line_type
        self._type_string = type_string

    @property
    def sobi_line_type(self):
        return self._sobi_line_type

    @property
    def type_string(self):
        return self._type_string

    @classmethod
    def from_sobi_line_type(cls, sobi_line_type: SobiLineType):
        for item in cls:
            if item.sobi_line_type == sobi_line_type:
                return item
        return None

class BillUpdateField(Enum):
    PUBLISHED_BILL = "PUBLISHED_BILL"
    ACT_CLAUSE = "ACT_CLAUSE"
    ACTION = "ACTION"
    ACTIVE_VERSION = "ACTIVE_VERSION"
    APPROVAL = "APPROVAL"
    COSPONSOR = "COSPONSOR"
    FULLTEXT = "FULLTEXT"
    LAW = "LAW"
    MEMO = "MEMO"
    MULTISPONSOR = "MULTISPONSOR"
    SPONSOR = "SPONSOR"
    STATUS = "STATUS"
    STATUS_CODE = "STATUS_CODE"
    SUMMARY = "SUMMARY"
    TITLE = "TITLE"
    VETO = "VETO"
    VOTE = "VOTE"

class BillVoteCode(Enum):
    """
    Represents the possible voting code prefixes.
    """
    AYE = "YES"
    NAY = "NO"
    EXC = "EXCUSED"
    ABS = "ABSENT"
    ABD = "ABSTAINED"
    AYEWR = "AYE W/R"  # 'Aye, with reservations'

    def __init__(self, alternate_string):
        self._alternate_string = alternate_string

    @property
    def alternate_string(self):
        return self._alternate_string

    @classmethod
    def from_string(cls, code: str):
        if code:
            code_upper = code.strip().upper()
            for item in cls:
                if item.name == code_upper or item.alternate_string == code_upper:
                    return item
        raise ValueError(f"Failed to map '{code}' to a BillVoteCode value.")

class BillVoteType(Enum):
    """
    Represents the possible types of votes that can take place.
    """
    COMMITTEE = 1
    FLOOR = 2

    @property
    def code(self):
        return self.value

    @classmethod
    def from_string(cls, vote_type: str):
        if vote_type:
            return cls[vote_type.strip().upper()]
        raise ValueError("Supplied null 'type' when mapping BillVoteType.")

    @classmethod
    def from_code(cls, code: int):
        for item in cls:
            if item.code == code:
                return item
        raise ValueError(f"No BillVoteType mapping with code: {code}")

class TextDiffType(Enum):
    UNCHANGED = (0, [], "", "")
    ADDED = (1, ["ol-changed", "ol-added"], "<b><u>", "</u></b>")
    REMOVED = (-1, ["ol-changed", "ol-removed"], "<b><s>", "</s></b>")
    HEADER = (0, ["ol-header"], "<font size=5><b>", "</b></font>")
    BOLD = (0, ["ol-bold"], "<b>", "</b>")
    PAGE_BREAK = (0, ["ol-page-break"], "<p class=\"brk\">", "")

    def __init__(self, type_val, template_css_class, html_opening_tags, html_closing_tags):
        self._type_val = type_val
        self._template_css_class = template_css_class
        self._html_opening_tags = html_opening_tags
        self._html_closing_tags = html_closing_tags

    @property
    def type(self):
        return self._type_val

    @property
    def template_css_class(self):
        return self._template_css_class

    @property
    def html_opening_tags(self):
        return self._html_opening_tags

    @property
    def html_closing_tags(self):
        return self._html_closing_tags

class VetoType(Enum):
    STANDARD = "STANDARD"
    LINE_ITEM = "LINE_ITEM"

class CalendarType(Enum):
    ACTIVE_LIST = "ACTIVE_LIST"
    FLOOR_CALENDAR = "FLOOR_CALENDAR"
    SUPPLEMENTAL_CALENDAR = "SUPPLEMENTAL_CALENDAR"

class CalendarSectionType(Enum):
    RESOLUTIONS = (100, "RESOLUTIONS")
    ORDER_OF_THE_FIRST_REPORT = (150, "BILLS ON ORDER OF FIRST REPORT")
    ORDER_OF_THE_SECOND_REPORT = (200, "BILLS ON ORDER OF SECOND REPORT")
    ORDER_OF_THE_SPECIAL_REPORT = (250, "BILLS ON ORDER OF SPECIAL REPORT")
    THIRD_READING_FROM_SPECIAL_REPORT = (350, "BILLS ON THIRD READING FROM SPECIAL REPORT")
    THIRD_READING = (400, "BILLS ON THIRD READING")
    STARRED_ON_THIRD_READING = (450, "BILLS STARRED ON THIRD READING")

    def __init__(self, code, lrs_representation):
        self._code = code
        self._lrs_representation = lrs_representation

    @property
    def code(self):
        return self._code

    @property
    def lrs_representation(self):
        return self._lrs_representation

    @classmethod
    def from_code(cls, code: int):
        for item in cls:
            if item.code == code:
                return item
        raise ValueError(f"No CalendarSectionType matches code {code}")

    @classmethod
    def from_lrs_representation(cls, lrs_representation: str):
        for item in cls:
            if item.lrs_representation == lrs_representation:
                return item
        raise ValueError(f"No CalendarSectionType matches lrsRepresentation {lrs_representation}")

class Version(Enum):
    ORIGINAL = ""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"

    def __str__(self):
        return self.value

    @classmethod
    def of(cls, version_str: str):
        clean_version = (version_str or "").strip().upper()
        if not clean_version or clean_version == "DEFAULT":
            return cls.ORIGINAL
        return cls[clean_version]

    @classmethod
    def before(cls, version):
        return [v for v in cls if v.value < version.value]

    @classmethod
    def after(cls, version):
        return [v for v in cls if v.value > version.value]