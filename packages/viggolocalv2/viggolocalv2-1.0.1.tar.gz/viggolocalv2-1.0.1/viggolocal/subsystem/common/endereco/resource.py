from viggocore.database import db
from viggocore.common.subsystem import entity


class Endereco(entity.Entity):

    attributes = ['logradouro', 'numero', 'complemento', 'bairro',
                  'municipio_id', 'ponto_referencia', 'cep', 'tag']

    logradouro = db.Column(db.String(255), nullable=False)
    numero = db.Column(db.String(60), nullable=False)
    complemento = db.Column(db.String(60), nullable=True)
    bairro = db.Column(db.String(60), nullable=False)
    municipio_id = db.Column(db.CHAR(32), nullable=False)
    ponto_referencia = db.Column(db.String(512), nullable=True)
    cep = db.Column(db.CHAR(8), nullable=False)

    def __init__(self, id, logradouro, numero, bairro, municipio_id, cep,
                 complemento=None, ponto_referencia=None,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.logradouro = logradouro
        self.numero = numero
        self.bairro = bairro
        self.complemento = complemento
        self.municipio_id = municipio_id
        self.ponto_referencia = ponto_referencia
        self.cep = cep
