from sqlalchemy import orm
from viggocore.database import db
from viggocore.common.subsystem import entity, schema_model


class Mesorregiao(entity.Entity, schema_model.PublicModel):

    attributes = ['uf_id', 'codigo_ibge', 'nome']
    attributes += entity.Entity.attributes

    uf_id = db.Column(db.CHAR(32), db.ForeignKey('public.uf.id'),
                      nullable=False)
    uf = orm.relationship('UF', backref=orm.backref('mesorregioes'))
    codigo_ibge = db.Column(db.Numeric(4, 0), nullable=False, unique=True)
    nome = db.Column(db.String(50), nullable=False)

    def __init__(self, id, uf_id, codigo_ibge, nome,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.uf_id = uf_id
        self.codigo_ibge = codigo_ibge
        self.nome = nome

    @classmethod
    def collection(cls):
        return 'mesorregioes'

    def is_stable(self):
        cod_ibge = int(self.codigo_ibge)
        return 1000 <= cod_ibge <= 9999
