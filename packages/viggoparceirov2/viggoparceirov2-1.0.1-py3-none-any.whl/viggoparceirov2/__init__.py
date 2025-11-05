import os
import viggocorev2
import viggolocalv2

from flask_cors import CORS

from viggocorev2.system import System
# from viggolocalv2.subsystem.sysadmin import ibge_sync
# from viggolocalv2.subsystem.parametrizacao.localidade \
#     import regiao, uf, mesorregiao, microrregiao, municipio

from viggoparceirov2.subsystem import parceiro
from viggoparceirov2.resources import SYSADMIN_EXCLUSIVE_POLICIES, \
    SYSADMIN_RESOURCES, USER_RESOURCES


system = System('viggoparceirov2',
                [parceiro.subsystem],
                USER_RESOURCES,
                SYSADMIN_RESOURCES,
                SYSADMIN_EXCLUSIVE_POLICIES)


class SystemFlask(viggocorev2.SystemFlask):

    def __init__(self):
        super().__init__(system, viggolocalv2.system)
        # ViggoLocal
        #     ibge_sync.subsystem, regiao.subsystem, uf.subsystem,
        #     mesorregiao.subsystem, microrregiao.subsystem,
        #     municipio.subsystem,
        #     # ViggoParceiroV2
        #     parceiro.subsystem
        # )

    def configure(self):
        origins_urls = os.environ.get('ORIGINS_URLS', '*')
        CORS(self, resources={r'/*': {'origins': origins_urls}})

        self.config['BASEDIR'] = os.path.abspath(os.path.dirname(__file__))
        self.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        viggoparceiro_database_uri = os.getenv('VIGGOPARCEIRO_DATABASE_URI', None)
        if viggoparceiro_database_uri is None:
            raise Exception('DATABASE_URI not defined in enviroment.')
        else:
            # URL os enviroment example for Postgres
            # export VIGGOPARCEIRO_DATABASE_URI=
            # mysql+pymysql://root:mysql@localhost:3306/viggoparceirov2
            self.config['SQLALCHEMY_DATABASE_URI'] = viggoparceiro_database_uri
