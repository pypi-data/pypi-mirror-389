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
                'action': 'registrar evento do saldo_limite_credito',
                'method': 'PUT',
                'url': self.resource_url + '/reg_parceiro_saldo_credito_evento',
                'callback': 'reg_parceiro_saldo_credito_evento',
                'bypass': False
            },
            {
                'action': 'Histórico de movimentação financeira do parceiro',
                'method': 'GET',
                'url': self.resource_url + '/historico_movimentacao',
                'callback': 'historico_movimentacao'
            },
            {
                'action': 'Histórico de movimentação financeira do parceiro',
                'method': 'POST',
                'url': self.resource_url +
                '/relatorio_movimentacao_parceiro_xlsx',
                'callback': 'relatorio_movimentacao_parceiro_xlsx'
            }
        ]
