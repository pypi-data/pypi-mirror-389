from sqlalchemy import orm
from viggocore.database import db
from viggocore.common.subsystem import entity, schema_model


class Municipio(entity.Entity, schema_model.PublicModel):

    attributes = ['microrregiao_id', 'codigo_ibge', 'nome', 'cep', 'sigla_uf']
    attributes += entity.Entity.attributes

    microrregiao_id = db.Column(
      db.CHAR(32), db.ForeignKey('public.microrregiao.id'), nullable=False)
    microrregiao = orm.relationship(
        'Microrregiao', backref=orm.backref('municipios'))
    codigo_ibge = db.Column(db.Numeric(7, 0), nullable=False, unique=True)
    nome = db.Column(db.String(50), nullable=False)
    sigla_uf = db.Column(db.CHAR(2), nullable=False)
    cep = db.Column(db.CHAR(8), nullable=True, unique=True)

    def __init__(self, id, microrregiao_id, codigo_ibge, nome, sigla_uf,
                 cep=None, active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.microrregiao_id = microrregiao_id
        self.codigo_ibge = codigo_ibge
        self.nome = nome
        self.sigla_uf = sigla_uf
        self.cep = cep
