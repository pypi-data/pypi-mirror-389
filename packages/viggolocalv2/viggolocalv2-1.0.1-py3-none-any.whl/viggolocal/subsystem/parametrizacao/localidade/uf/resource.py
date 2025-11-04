from sqlalchemy import orm
from viggocore.database import db
from viggocore.common.subsystem import entity, schema_model


class UF(entity.Entity, schema_model.PublicModel):

    attributes = ['regiao_id', 'codigo_ibge', 'sigla', 'nome']
    attributes += entity.Entity.attributes

    regiao_id = db.Column(
        db.CHAR(32), db.ForeignKey('public.regiao.id'), nullable=False)
    regiao = orm.relationship('Regiao', backref=orm.backref('ufs'))
    codigo_ibge = db.Column(db.Numeric(2, 0), nullable=False, unique=True)
    sigla = db.Column(db.CHAR(2), nullable=False, unique=True)
    nome = db.Column(db.String(20), nullable=False)

    __tablename__ = 'uf'

    def __init__(self, id, regiao_id, codigo_ibge, sigla, nome,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.regiao_id = regiao_id
        self.codigo_ibge = codigo_ibge
        self.sigla = sigla
        self.nome = nome

    def is_stable(self):
        is_codigo_ibge = 10 <= self.codigo_ibge <= 99
        is_sigla = ((len(self.sigla) == 2) and (
            self.sigla.isupper() and self.sigla.isalpha()))

        return is_codigo_ibge and is_sigla
