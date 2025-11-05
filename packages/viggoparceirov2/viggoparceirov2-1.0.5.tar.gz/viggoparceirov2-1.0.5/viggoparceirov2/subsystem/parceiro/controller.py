import flask
from viggocorev2.common import exception, utils
from viggocorev2.common import controller


class Controller(controller.CommonController):

    def get_usuarios_disponiveis(self):
        filters = self._filters_parse()
        filters = self._filters_cleanup(filters)
        try:
            filters = self._parse_list_options(filters)
            users, total_rows = self.manager.\
                get_usuarios_disponiveis(**filters)

            page = filters.get('page', None)
            page_size = filters.get('page_size', None)
        except exception.ViggoCoreException as exc:
            return flask.Response(response=exc.message,
                                  status=exc.status)

        users_dict = []
        for user in users:
            user_dict = user.to_dict()
            users_dict.append(user_dict)

        response = {self.resource_wrap: users_dict}

        if total_rows is not None:
            response.update({'pagination': {'page': int(page),
                                            'page_size': int(page_size),
                                            'total': total_rows}})

        return flask.Response(response=utils.to_json(response),
                              status=200,
                              mimetype="application/json")
