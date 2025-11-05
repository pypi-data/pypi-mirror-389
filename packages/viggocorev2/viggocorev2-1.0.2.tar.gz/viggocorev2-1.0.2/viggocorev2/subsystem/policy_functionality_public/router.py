from viggocorev2.common.subsystem import router


class Router(router.Router):

    def __init__(self, collection, routes=[]):
        super().__init__(collection, routes)

    @property
    def routes(self):
        return super().routes + [
            {
                'action': 'Pega as funcionalidades disponiveis (public)',
                'method': 'GET',
                'url': self.collection_url +
                '/get_available_capability_functionalities',
                'callback': 'get_available_functionalities'
            },
            {
                'action': 'Pega as funcionalidades selecionadas (public)',
                'method': 'GET',
                'url': self.collection_url +
                '/get_selected_capability_functionalities',
                'callback': 'get_selected_functionalities'
            },
            {
                'action': 'Cadastra as policy_functionality_public',
                'method': 'POST',
                'url': self.collection_url + '/create_entities',
                'callback': 'create_policy_functionalities'
            }
        ]
