import flask
import requests
from math import trunc
from viggocore.common import exception
from viggocore.common.subsystem import manager, operation
from viggolocal.subsystem.sysadmin.ibge_sync.resource import MessageType


class Create(operation.Create):

    def pre(self, **kwargs):
        self.token = self.manager.api.tokens().get(
            id=flask.request.headers.get('token'))

        url = 'http://servicodados.ibge.gov.br'
        resource = '/api/v1/localidades/municipios'
        self.response = requests.get(url + resource)

        if self.response.status_code != 200:
            raise exception.OperationBadRequest(
                'A api do IBGE retornou status diferente de 200.')

        # regioes = self.manager.api.regioes().list()

        # if regioes:
        #     raise exception.OperationBadRequest()

        return self.token is not None and super().pre(**kwargs)

    def do(self, session, **kwargs):
        self.entity.created_by = self.token.user_id
        self.entity = super().do(session, **kwargs)

        self.entity.addMsg(MessageType.Info, 'Iniciando Sync...')

        regioes = {}
        ufs = {}
        mesorregioes = {}
        microrregioes = {}
        municipios = {}

        for mun in self.response.json():
            reg = mun['microrregiao']['mesorregiao']['UF'].pop('regiao')
            uf = mun['microrregiao']['mesorregiao'].pop('UF')
            meso = mun['microrregiao'].pop('mesorregiao')
            micro = mun.pop('microrregiao')
            mun.pop('regiao-imediata')

            mun['microrregiao_id'] = micro['id']
            micro['mesorregiao_id'] = meso['id']
            meso['uf_id'] = uf['id']
            uf['regiao_id'] = reg['id']

            for d in (reg, uf, meso, micro, mun):
                d['codigo_ibge'] = d.pop('id')

            regioes[reg['codigo_ibge']] = reg
            ufs[uf['codigo_ibge']] = uf
            mesorregioes[meso['codigo_ibge']] = meso
            microrregioes[micro['codigo_ibge']] = micro
            municipios[mun['codigo_ibge']] = mun

        for codigo_ibge, reg in regioes.items():
            regiao = self.manager.api.regioes().list(codigo_ibge=codigo_ibge)
            if regiao:
                regioes[codigo_ibge] = regiao[0]
            else:
                regioes[codigo_ibge] = self.manager.api.regioes().create(**reg)

        for codigo_ibge, uf in ufs.items():
            un_fed = self.manager.api.ufs().list(codigo_ibge=codigo_ibge)
            if un_fed:
                ufs[codigo_ibge] = un_fed[0]
            else:
                uf['regiao_id'] = regioes[uf['regiao_id']].id
                ufs[codigo_ibge] = self.manager.api.ufs().create(**uf)

        for codigo_ibge, meso in mesorregioes.items():
            mesor = self.manager.api.mesorregioes().list(codigo_ibge=codigo_ibge)
            if mesor:
                mesorregioes[codigo_ibge] = mesor[0]
            else:
                meso['uf_id'] = ufs[meso['uf_id']].id
                mesorregioes[codigo_ibge] = \
                    self.manager.api.mesorregioes().create(**meso)

        for codigo_ibge, micro in microrregioes.items():
            micror = \
                self.manager.api.microrregioes().list(codigo_ibge=codigo_ibge)
            if micror:
                microrregioes[codigo_ibge] = micror[0]
            else:
                micro['mesorregiao_id'] = \
                    mesorregioes[micro['mesorregiao_id']].id
                microrregioes[codigo_ibge] = \
                    self.manager.api.microrregioes().create(**micro)

        for codigo_ibge, mun in municipios.items():
            munic = self.manager.api.municipios().list(codigo_ibge=codigo_ibge)
            if munic:
                municipios[codigo_ibge] = munic[0]
            else:
                cod_ibge_uf = trunc(int(codigo_ibge) / 100000)
                mun['sigla_uf'] = ufs[cod_ibge_uf].sigla
                mun['microrregiao_id'] = \
                    microrregioes[mun['microrregiao_id']].id
                municipios[codigo_ibge] = \
                    self.manager.api.municipios().create(**mun)

        self.entity.addMsg(MessageType.Info, 'Sync realizado com SUCESSO!')

        return self.entity


class Manager(manager.Manager):

    def __init__(self, driver):
        super(Manager, self).__init__(driver)
        self.create = Create(self)
