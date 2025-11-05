from gabbi import fixture

import abc
import json
import uuid
import orcomm
import os
import pdb


class Fixture(fixture.GabbiFixture):

    def __init__(self):
        super().__init__()

        self.system = orcomm.SystemFlask()
        self.app = self.system.test_client()

    @property
    def individual(self):
        return None

    @property
    def collection(self):
        return self.individual + 's'

    @abc.abstractmethod
    def new_dict(self):
        raise NotImplementedError

    def start_fixture(self):
        if self.individual == 'token':
            headers = {'Content-Type': 'application/json'}
        else:
            headers = {
                'token': self.env('token'),
                'Content-Type': 'application/json'
            }

        response = self.app.post(
            '/' + self.collection,
            headers=headers,
            data=json.dumps(self.new_dict()))

        pdb.set_trace()
        resource = json.loads(response.data.decode())[self.individual]

        k = self.individual
        if self.env(k):
            i = 2
            while self.env(k + '.' + str(i)):
                i += 1
            k = k + '.' + str(i)

        self.key = k
        self.value = resource['id']

        self.env(self.key, self.value)

    def stop_fixture(self):
        if self.collection == 'tokens':
            return
        headers = {
            'token': self.env('token'),
            'Content-Type': 'application/json'
        }
        self.app.delete('/' + self.collection + '/' + self.value,
                        headers=headers)
        os.environ.pop(self.key)

    def env(self, k, v=None):
        if v is not None:
            os.environ[k] = v
        else:
            try:
                v = os.environ[k]
            except KeyError:
                v = None
        return v


class TokenFixture(Fixture):

    @property
    def individual(self):
        return 'token'

    def new_dict(self):
        return {'domain_name': 'default',
                'username': 'sysadmin',
                'password': '123456'}


class DomainFixture(Fixture):

    @property
    def individual(self):
        return 'domain'

    def new_dict(self):
        return {'name': uuid.uuid4().hex}


class UserFixture(Fixture):

    @property
    def individual(self):
        return 'user'

    def new_dict(self):
        return {'domain_id': self.env('domain'),
                'name': uuid.uuid4().hex,
                'email': uuid.uuid4().hex,
                'password': uuid.uuid4().hex}


class ClienteFixture(Fixture):

    @property
    def individual(self):
        return 'cliente'

    def new_dict(self):
        return {'domain_id': self.env('domain'),
                'promotor_id': self.env('user'),
                'nome': uuid.uuid4().hex}


class CicloFixture(Fixture):

    @property
    def individual(self):
        return 'ciclo'

    def new_dict(self):
        return {'domain_id': self.env('domain'),
                'nome': uuid.uuid4().hex,
                'data_inicio': '3017-01-01',
                'data_fim': '3017-03-31'}


class VisitaFixture(Fixture):

    @property
    def individual(self):
        return 'visita'

    def new_dict(self):
        return {'cliente_id': self.env('cliente'),
                'ciclo_id': self.env('ciclo'),
                'data': '3017-02-01'}
