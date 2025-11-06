# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)

from caerp.models.base import (
    DBBASE,
    default_table_args,
)


class PDFSignatureHistory(DBBASE):
    __tablename__ = "pdf_signature_history"
    __table_args__ = default_table_args
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(), default=datetime.datetime.now)
    user_id = Column(Integer)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(255), nullable=False)
    node_id = Column(Integer())
