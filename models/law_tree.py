from __future__ import annotations
from typing import Optional, Dict, List, Any, LinkedHashMap
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum
from collections import OrderedDict

class LawDocumentType(str, Enum):
    CHAPTER = "CHAPTER"
    PREAMBLE = "PREAMBLE"
    ARTICLE = "ARTICLE"
    SUBARTICLE = "SUBARTICLE"
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    RULE = "RULE"
    JOINT_RULE = "JOINT_RULE"
    PART = "PART"
    SUBPART = "SUBPART"
    INDEX = "INDEX"
    CONTENTS = "CONTENTS"
    SECTION = "SECTION"
    MISC = "MISC"
    SUBDIVISION = "SUBDIVISION"
    PARAGRAPH = "PARAGRAPH"
    SUB_PARAGRAPH = "SUB_PARAGRAPH"
    CLAUSE = "CLAUSE"
    ITEM = "ITEM"

    def is_section(self) -> bool:
        return self == LawDocumentType.SECTION

class LawDocId(BaseModel):
    document_id: str
    published_date: date
    location_id: Optional[str] = None
    law_id: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.location_id is None and self.document_id:
            self.location_id = self.document_id[3:]
        if self.law_id is None and self.document_id:
            self.law_id = self.document_id[:3]

    @classmethod
    def from_document_id_and_date(cls, document_id: str, published_date: date) -> "LawDocId":
        return cls(document_id=document_id, published_date=published_date)

    def __eq__(self, other) -> bool:
        if not isinstance(other, LawDocId):
            return False
        return (
            self.document_id == other.document_id and
            self.published_date == other.published_date and
            self.location_id == other.location_id and
            self.law_id == other.law_id
        )

    def __hash__(self) -> int:
        return hash((self.document_id, self.published_date, self.location_id, self.law_id))

    def __str__(self) -> str:
        return f"{self.document_id}:{self.published_date}"

    # Getters
    def get_document_id(self) -> str:
        return self.document_id

    def get_published_date(self) -> date:
        return self.published_date

    def get_law_id(self) -> str:
        return self.law_id

    def get_location_id(self) -> str:
        return self.location_id

class LawDocInfo(LawDocId):
    title: Optional[str] = None
    doc_type: Optional[LawDocumentType] = None
    doc_type_id: Optional[str] = None
    dummy: bool = False

    def __str__(self) -> str:
        return f"{self.document_id} ({self.doc_type}) {self.published_date}"

    # Getters and setters
    def get_title(self) -> Optional[str]:
        return self.title

    def set_title(self, title: str) -> None:
        self.title = title

    def get_doc_type(self) -> Optional[LawDocumentType]:
        return self.doc_type

    def set_doc_type(self, doc_type: LawDocumentType) -> None:
        self.doc_type = doc_type

    def get_doc_type_id(self) -> Optional[str]:
        return self.doc_type_id

    def set_doc_type_id(self, doc_type_id: str) -> None:
        self.doc_type_id = doc_type_id

    def is_dummy(self) -> bool:
        return self.dummy

    def set_dummy(self, dummy: bool) -> None:
        self.dummy = dummy

class LawTreeNode(BaseModel):
    sequence_no: int
    law_doc_info: LawDocInfo
    parent: Optional['LawTreeNode'] = None
    children: OrderedDict[str, 'LawTreeNode'] = Field(default_factory=OrderedDict)
    repealed_date: Optional[date] = None
    _section_range: Optional[tuple['LawTreeNode', 'LawTreeNode']] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.law_doc_info is None:
            raise ValueError("Cannot instantiate LawTreeNode with a null LawDocInfo")

    def is_root_node(self) -> bool:
        return self.law_doc_info.doc_type == LawDocumentType.CHAPTER

    def add_child(self, node: 'LawTreeNode') -> None:
        if node is None:
            raise ValueError("Cannot add a null child node")
        node.parent = self
        self.children[node.law_doc_info.document_id] = node

    def get_section_range(self) -> Optional[tuple['LawTreeNode', 'LawTreeNode']]:
        start = self._find_first_section(self)
        end = self._find_last_section(self)
        if start and end:
            self._section_range = (start, end)
        else:
            self._section_range = None
        return self._section_range

    def get_from_section(self) -> Optional['LawTreeNode']:
        if self._section_range is None:
            self.get_section_range()
        return self._section_range[0] if self._section_range else None

    def get_to_section(self) -> Optional['LawTreeNode']:
        if self._section_range is None:
            self.get_section_range()
        return self._section_range[1] if self._section_range else None

    def get_child_node_list(self) -> List['LawTreeNode']:
        return sorted(self.children.values(), key=lambda n: n.sequence_no)

    def get_all_nodes(self, desc_nodes: Optional[List['LawTreeNode']] = None) -> List['LawTreeNode']:
        if desc_nodes is None:
            desc_nodes = []
        desc_nodes.append(self)
        for n in self.get_child_node_list():
            n.get_all_nodes(desc_nodes)
        return desc_nodes

    def get_prev_sibling(self) -> Optional['LawTreeNode']:
        if self.parent:
            siblings = self.parent.get_child_node_list()
            idx = siblings.index(self)
            if idx > 0:
                return siblings[idx - 1]
        return None

    def get_next_sibling(self) -> Optional['LawTreeNode']:
        if self.parent:
            siblings = self.parent.get_child_node_list()
            idx = siblings.index(self)
            if idx < len(siblings) - 1:
                return siblings[idx + 1]
        return None

    def get_all_parents(self) -> List['LawTreeNode']:
        parents = []
        node = self
        while node.parent:
            node = node.parent
            parents.insert(0, node)
        return parents

    def find(self, document_id: str) -> Optional[LawDocInfo]:
        node = self.find_node(document_id, delete=False)
        return node.law_doc_info if node else None

    def find_node(self, document_id: str, delete: bool = False) -> Optional['LawTreeNode']:
        if self.law_doc_info.document_id == document_id:
            node = self
        elif document_id in self.children:
            node = self.children[document_id]
        else:
            node = None
            for child in self.children.values():
                node = child.find_node(document_id, delete)
                if node:
                    break
        if delete and node and node.parent:
            del node.parent.children[document_id]
        return node

    def print_tree(self, level: int = 1) -> str:
        sb = [str(self.law_doc_info)]
        for n in self.get_child_node_list():
            sb.append("\n" + "  |  " * level + n.print_tree(level + 1))
        return ''.join(sb)

    def _find_first_section(self, node: 'LawTreeNode') -> Optional['LawTreeNode']:
        if node.law_doc_info.doc_type and node.law_doc_info.doc_type.is_section():
            return node
        children_list = list(node.children.values())
        first_node = None
        while children_list and first_node is None:
            first_node = self._find_first_section(children_list[0])
            if first_node is None:
                children_list.pop(0)
        return first_node

    def _find_last_section(self, node: 'LawTreeNode') -> Optional['LawTreeNode']:
        if node.law_doc_info.doc_type and node.law_doc_info.doc_type.is_section():
            return node
        children_list = list(node.children.values())
        last_node = None
        while children_list and last_node is None:
            last_node = self._find_last_section(children_list[-1])
            if last_node is None:
                children_list.pop()
        return last_node

    def __str__(self) -> str:
        return f"Law Tree Node [{self.sequence_no}] {self.law_doc_info}"

    def __lt__(self, other: 'LawTreeNode') -> bool:
        return self.sequence_no < other.sequence_no

    # Delegates
    def get_law_id(self) -> str:
        return self.law_doc_info.get_law_id()

    def get_doc_type(self) -> Optional[LawDocumentType]:
        return self.law_doc_info.get_doc_type()

    def get_doc_type_id(self) -> Optional[str]:
        return self.law_doc_info.get_doc_type_id()

    def get_publish_date(self) -> date:
        return self.law_doc_info.get_published_date()

    def get_document_id(self) -> str:
        return self.law_doc_info.get_document_id()

    def get_location_id(self) -> str:
        return self.law_doc_info.get_location_id()

    # Getters and setters
    def get_sequence_no(self) -> int:
        return self.sequence_no

    def set_sequence_no(self, sequence_no: int) -> None:
        self.sequence_no = sequence_no

    def get_law_doc_info(self) -> LawDocInfo:
        return self.law_doc_info

    def get_parent(self) -> Optional['LawTreeNode']:
        return self.parent

    def set_parent(self, parent: 'LawTreeNode') -> None:
        self.parent = parent

    def get_children(self) -> OrderedDict[str, 'LawTreeNode']:
        return self.children

    def get_repealed_date(self) -> Optional[date]:
        return self.repealed_date

    def set_repealed_date(self, repealed_date: date) -> None:
        self.repealed_date = repealed_date

class LawVersionId(BaseModel):
    law_id: str
    published_date: date

    def __str__(self) -> str:
        return f"{self.law_id}v{self.published_date}"

class LawTree(BaseModel):
    law_version_id: LawVersionId
    root_node: LawTreeNode
    law_info: 'LawInfo'
    published_dates: List[date] = Field(default_factory=list)
    _node_lookup_map: Optional[Dict[str, LawTreeNode]] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.root_node is None:
            raise ValueError("Cannot construct a LawTree with a null rootNode")
        if self.law_info is None:
            raise ValueError("Cannot construct a LawTree with a null lawInfo")
        self.published_dates = list(set(node.get_publish_date() for node in self.root_node.get_all_nodes()))

    def rebuild_lookup_map(self) -> None:
        self._node_lookup_map = {node.get_document_id(): node for node in self.root_node.get_all_nodes()}

    def find(self, document_id: str) -> Optional[LawTreeNode]:
        if self._node_lookup_map is None:
            self.rebuild_lookup_map()
        return self._node_lookup_map.get(document_id)

    def get_law_id(self) -> str:
        return self.law_version_id.law_id

    def get_published_date(self) -> date:
        return self.law_version_id.published_date

    # Getters and setters
    def get_law_version_id(self) -> LawVersionId:
        return self.law_version_id

    def get_root_node(self) -> LawTreeNode:
        return self.root_node

    def get_law_info(self) -> 'LawInfo':
        return self.law_info

    def get_published_dates(self) -> List[date]:
        return self.published_dates

    def set_published_dates(self, published_dates: List[date]) -> None:
        self.published_dates = published_dates
