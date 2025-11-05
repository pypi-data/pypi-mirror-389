import flask

from viggocorev2.common import exception, utils
from viggocorev2.common.subsystem import controller


class Controller(controller.Controller):

    def __init__(self, manager, resource_wrap, collection_wrap):
        super(Controller, self).__init__(
            manager, resource_wrap, collection_wrap)

    def get_nextval(self):
        data = flask.request.get_json()

        try:
            if 'name' not in data:
                raise exception.BadRequest(
                    'O campo "name" é obrigatório.')

            response = self.manager.get_nextval(
                name=data['name'])
        except exception.ViggoCoreException as exc:
            return flask.Response(response=exc.message,
                                  status=exc.status)

        response = {'nextval': response}

        return flask.Response(response=utils.to_json(response),
                              status=200,
                              mimetype="application/json")
