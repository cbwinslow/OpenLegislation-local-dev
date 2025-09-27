from __future__ import annotations
from typing import Optional, Dict, List, Any
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum

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
    def __eq__(self, other):
        return (
            self.document_id == other.document_id and
            self.published_date == other.published_date and
            self.location_id == other.location_id and
            self.law_id == other.law_id
        )
    def __hash__(self):
        return hash((self.document_id, self.published_date, self.location_id, self.law_id))
    def __str__(self):
        return f"{self.document_id}:{self.published_date}"

class LawDocInfo(LawDocId):
    title: Optional[str] = None
    doc_type: Optional[LawDocumentType] = None
    doc_type_id: Optional[str] = None
    dummy: bool = False
    def __str__(self):
        return f"{self.document_id} ({self.doc_type}) {self.published_date}"

class LawTreeNode(BaseModel):
    sequence_no: int
    law_doc_info: LawDocInfo
    parent: Optional[LawTreeNode] = None
    children: Dict[str, 'LawTreeNode'] = Field(default_factory=dict)
    repealed_date: Optional[date] = None
    section_range: Optional[List['LawTreeNode']] = None

    def is_root_node(self) -> bool:
        return self.law_doc_info.doc_type == LawDocumentType.CHAPTER

    def add_child(self, node: 'LawTreeNode'):
        node.parent = self
        self.children[node.law_doc_info.document_id] = node

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

    def __str__(self):
        return f"Law Tree Node [{self.sequence_no}] {self.law_doc_info}"
