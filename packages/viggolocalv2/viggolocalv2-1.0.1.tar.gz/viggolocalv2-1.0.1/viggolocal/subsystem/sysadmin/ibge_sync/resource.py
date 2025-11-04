import uuid
import enum

from sqlalchemy import orm
from datetime import datetime
from sqlalchemy.types import Enum
from viggocore.database import db
from viggocore.common.subsystem import entity, schema_model


class MessageType(enum.Enum):
    Info = 0
    Warning = 1
    Error = 2


class IbgeSync(entity.Entity, schema_model.PublicModel):

    messages = orm.relationship(
        "IbgeSyncMessage", backref=orm.backref('ibge_sync'),
        cascade='delete,delete-orphan,save-update')

    def __init__(self, id,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)

    def addMsg(self, msg_type, msg_body):
        message = IbgeSyncMessage(
            id=uuid.uuid4().hex, ibge_sync_id=self.id,
            created_at=datetime.now(), type=msg_type, body=msg_body)
        self.messages.append(message)

    @classmethod
    def individual(cls):
        return 'ibge_sync'

    @classmethod
    def embedded(cls):
        return ['messages']


class IbgeSyncMessage(entity.Entity, schema_model.PublicModel):

    attributes = ['ibge_sync_id', 'type', 'body']
    attributes += entity.Entity.attributes

    ibge_sync_id = db.Column(
        db.CHAR(32), db.ForeignKey("public.ibge_sync.id"), nullable=False)
    type = db.Column(Enum(MessageType), nullable=False)
    body = db.Column(db.String(250), nullable=False)

    def __init__(self, id, ibge_sync_id, type, body,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.ibge_sync_id = ibge_sync_id
        self.type = type
        self.body = body

    @classmethod
    def individual(cls):
        return 'ibge_sync_message'
