import flask
import uuid


from sqlalchemy import text
from viggocorev2 import database
from viggocorev2.common import exception
from viggocorev2.common.subsystem.apihandler import Api, ApiHandler


class Request(flask.Request):

    # TODO(samueldmq): find a better place to put this utility method
    def _check_uuid4(self, uuid_str):
        if len(uuid_str) != 32:
            return False
        try:
            return uuid.UUID(uuid_str, version=4)
        except ValueError:
            return False

    @property
    def url(self):
        path_info = flask.request.environ['PATH_INFO'].rstrip('/')
        path_bits = [
            '<id>' if self._check_uuid4(i) else i for i in path_info.split('/')
        ]

        if path_bits.count('<id>') > 1:
            pos = 0
            qty_id = 1
            for bit in path_bits:
                if bit == '<id>':
                    path_bits[pos] = '<id' + str(qty_id) + '>'
                    qty_id += 1
                pos += 1
        return '/'.join(path_bits)

    @property
    def token(self):
        return flask.request.headers.get('token')

    @property
    def domain_id(self):
        return flask.request.headers.get('Domain-Id')


class RequestManager(object):

    def __init__(self, api_handler: ApiHandler):
        self.api_handler = api_handler

    def before_request(self):  # noqa
        # configura qual esquema observar
        try:
            self._configure_schemas()
        except Exception as e:
            return flask.Response(response=e.message, status=e.status)

        api: Api = self.api_handler.api()
        if flask.request.method == 'OPTIONS':
            return

        # Short-circuit if accessing the root URL,
        # which will just return the version
        # TODO(samueldmq): Do we need to create a subsystem just for this ?
        if not flask.request.url:
            return

        routes = api.routes().list(url=flask.request.url,
                                   method=flask.request.method)
        if not routes:
            msg = 'Route not found'
            return flask.Response(response=msg, status=404)
        route = routes[0]

        if not route.active:
            msg = 'Route is inactive'
            return flask.Response(response=msg, status=410)

        if route.bypass:
            return

        token_id = flask.request.token

        if not token_id:
            msg = 'Token is required'
            return flask.Response(response=msg, status=401)

        try:
            token = api.tokens().get(id=token_id)
        except exception.NotFound:
            msg = 'Token not found'
            return flask.Response(response=msg, status=401)

        can_access = api.users().authorize(user_id=token.user_id, route=route)

        if not can_access:
            msg = 'You do not have permission'
            return flask.Response(response=msg, status=403)

        return

    def _configure_schemas(self):
        """
        ✅ CORRIGIDO: Configura schemas de forma thread-safe
        """

        # ✅ 1. Obter domain_id
        domain_id = getattr(flask.request, 'domain_id', None)
        if domain_id is None:
            raise exception.BadRequest(
                "Domain-Id é obrigatório no header da requisição.")

        try:
            schema_name = domain_id

            # ✅ 2. SALVAR CONTEXTO (por request)
            flask.g.tenant_domain_id = domain_id
            flask.g.tenant_schema = schema_name

            # # ✅ 3. CONFIGURAR SEARCH_PATH ao invés de alterar modelos globais
            # self._configure_database_connection_safe(schema_name)

            # # ✅ 4. REGISTRAR cleanup para final da requisição
            @flask.after_this_request
            def cleanup_schema(response):
                """
                Limpa o search_path e fecha a sessão ao final da requisição.
                Garante que nenhuma conexão permaneça com o schema do tenant.
                """
                try:
                    session = database.db.session

                    # 🔹 Garante que a sessão termine limpa
                    if session.is_active:
                        session.rollback()

                    # 🔹 Reseta o search_path explicitamente para o public
                    session.execute(text('SET search_path TO public'))
                    session.commit()

                except Exception as e:
                    # print(f"⚠️ Erro ao limpar search_path: {e}")
                    try:
                        # Fallback no nível do engine (caso a session esteja inconsistente)
                        with database.db.engine.connect() as conn:
                            conn.execution_options(autocommit=True)
                            conn.execute(text('SET search_path TO public'))
                    except Exception as e2:
                        # print(f"⚠️ Falha no fallback de cleanup: {e2}")
                        pass
                finally:
                    # 🔹 Fecha a sessão e remove do escopo (sem reusar a conexão)
                    session.close()
                    database.db.session.remove()

                    # 🔹 Remove dados do contexto Flask
                    for attr in ('tenant_domain_id', 'tenant_schema'):
                        if hasattr(flask.g, attr):
                            delattr(flask.g, attr)

                return response

            # print(f"✅ Schema configurado via search_path: {schema_name}")

        except Exception as e:
            print(f"❌ Erro ao configurar schemas para {domain_id}: {e}")
            raise
