from viggocorev2.database import db
from viggocorev2.common.subsystem import entity, schema_model


class Pais(entity.Entity, schema_model.PublicModel):

    attributes = ['codigo', 'nome']
    attributes += entity.Entity.attributes

    codigo = db.Column(db.Numeric(5, 0), nullable=False, unique=True)
    nome = db.Column(db.String(80), nullable=False)

    def __init__(self, id, codigo, nome,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.codigo = codigo
        self.nome = nome

    @classmethod
    def collection(cls):
        return 'paises'
