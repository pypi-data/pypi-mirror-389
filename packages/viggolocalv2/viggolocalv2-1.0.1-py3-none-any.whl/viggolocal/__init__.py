import os
import viggocore

from viggocore.system import System
from flask_cors import CORS
from viggolocal.subsystem.common import endereco
from viggolocal.subsystem.sysadmin import ibge_sync
from viggolocal.subsystem.parametrizacao.localidade \
    import regiao, uf, mesorregiao, microrregiao, municipio, pais
from viggolocal.resources import SYSADMIN_EXCLUSIVE_POLICIES, \
    SYSADMIN_RESOURCES, USER_RESOURCES


system = System('viggolocal',
                [endereco.subsystem, ibge_sync.subsystem, regiao.subsystem,
                 mesorregiao.subsystem, uf.subsystem, microrregiao.subsystem,
                 municipio.subsystem, pais.subsystem],
                USER_RESOURCES,
                SYSADMIN_RESOURCES,
                SYSADMIN_EXCLUSIVE_POLICIES)


class SystemFlask(viggocore.SystemFlask):

    def __init__(self):
        super().__init__(system)

    def configure(self):
        origins_urls = os.environ.get('ORIGINS_URLS', '*')
        CORS(self, resources={r'/*': {'origins': origins_urls}})

        self.config['BASEDIR'] = os.path.abspath(os.path.dirname(__file__))
        self.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        viggolocal_database_uri = os.getenv('VIGGOLOCAL_DATABASE_URI', None)
        if viggolocal_database_uri is None:
            raise Exception(
                'VIGGOLOCAL_DATABASE_URI não definido no enviroment.')
        else:
            # URL os enviroment example for Postgres
            # export VIGGOLOCAL_DATABASE_URI=
            # mysql+pymysql://root:mysql@localhost:3306/viggolocal
            self.config['SQLALCHEMY_DATABASE_URI'] = viggolocal_database_uri
