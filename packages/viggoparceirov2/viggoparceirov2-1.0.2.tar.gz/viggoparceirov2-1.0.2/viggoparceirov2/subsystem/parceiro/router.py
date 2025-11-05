from viggocorev2.common.subsystem import router


class Router(router.Router):

    def __init__(self, collection, routes=[]):
        super().__init__(collection, routes)

    @property
    def routes(self):
        return [
            {
                'action': 'create',
                'method': 'POST',
                'url': self.collection_url,
                'callback': 'create'
            },
            {
                'action': 'get',
                'method': 'GET',
                'url': self.resource_url,
                'callback': 'get'
            },
            {
                'action': 'update',
                'method': 'PUT',
                'url': self.resource_url,
                'callback': 'update'
            },
            {
                'action': 'delete',
                'method': 'DELETE',
                'url': self.resource_url,
                'callback': 'delete'
            },
            {
                'action': 'activate or deactivate multiple entities',
                'method': 'POST',
                'url': self.collection_url + '/activate_or_deactivate',
                'callback': 'activate_or_deactivate_multiple_entities'
            },
            {
                'action': 'Get users disponíveis',
                'method': 'GET',
                'url': self.collection_url + '/usuarios_disponiveis',
                'callback': 'get_usuarios_disponiveis'
            },
        ]
