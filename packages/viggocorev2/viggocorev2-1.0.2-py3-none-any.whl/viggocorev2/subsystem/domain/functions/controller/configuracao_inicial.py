import flask

from viggocorev2.common import exception


def configuracao_inicial(self):
    try:
        data = flask.request.get_json()
        self.manager.configuracao_inicial(**data)
    except exception.ViggoCoreException as exc:
        return flask.Response(response=exc.message,
                              status=exc.status)

    return flask.Response(response=None,
                          status=204,
                          mimetype="application/json")
