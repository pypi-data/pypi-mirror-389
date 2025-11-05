from sqlalchemy import orm
from viggocorev2.database import db
from viggocorev2.common.subsystem import entity, schema_model


class Microrregiao(entity.Entity, schema_model.PublicModel):

    attributes = ['mesorregiao_id', 'codigo_ibge', 'nome']
    attributes += entity.Entity.attributes

    mesorregiao_id = db.Column(
        db.CHAR(32), db.ForeignKey('public.mesorregiao.id'), nullable=False)
    mesorregiao = orm.relationship(
        'Mesorregiao', backref=orm.backref('microrregioes'))
    codigo_ibge = db.Column(db.Numeric(5, 0), nullable=False, unique=True)
    nome = db.Column(db.String(50), nullable=False)

    def __init__(self, id, mesorregiao_id, codigo_ibge, nome,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.mesorregiao_id = mesorregiao_id
        self.codigo_ibge = codigo_ibge
        self.nome = nome

    @classmethod
    def collection(cls):
        return 'microrregioes'

    def is_stable(self):
        cod_ibge = int(self.codigo_ibge)
        return 10000 <= cod_ibge <= 99999
