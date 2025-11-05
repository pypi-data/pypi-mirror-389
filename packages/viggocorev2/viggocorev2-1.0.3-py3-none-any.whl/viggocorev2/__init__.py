import flask
import os

from viggocorev2 import database
from viggocorev2 import request
from viggocorev2 import subsystem as subsystem_module
from viggocorev2 import scheduler
from viggocorev2 import celery
from viggocorev2.bootstrap import Bootstrap
from viggocorev2.common.subsystem.apihandler import ApiHandler
from viggocorev2.common.input import InputResourceUtils
from viggocorev2.system import System
from viggocorev2._version import version as viggocore_version
from viggocorev2.migration import migration_upgrade, migration_downgrade
from sqlalchemy import text

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json

from viggocorev2.resources import SYSADMIN_EXCLUSIVE_POLICIES, \
    SYSADMIN_RESOURCES, USER_RESOURCES


system = System('viggocorev2',
                subsystem_module.all,
                USER_RESOURCES,
                SYSADMIN_RESOURCES,
                SYSADMIN_EXCLUSIVE_POLICIES)


class SystemFlask(flask.Flask):

    request_class = request.Request

    def __init__(self, *args, **kwargs):
        super().__init__(__name__, static_folder=None)

        self.configure()
        self.configure_commands()
        self.init_database()
        self.after_init_database()
        self.configure_request_logging()
        self.configure_msg_error_500()

        system_list = [system] + list(kwargs.values()) + list(args)

        subsystem_list, self.user_resources, self.sysadmin_resources, \
            self.sysadmin_exclusive_resources = self._parse_systems(
                system_list)

        self.subsystems = {s.name: s for s in subsystem_list}

        self.api_handler = self.inject_dependencies()
        self.__validate_routes(self.subsystems)

        for subsystem in self.subsystems.values():
            self.register_blueprint(subsystem)

        # Add version in the root URL
        self.add_url_rule('/', view_func=self.version, methods=['GET'])

        # ✅ Registrar handler de cleanup (ANTES de processar requisições)
        self._register_cleanup_handlers()

        self.before_request(
            request.RequestManager(self.api_handler).before_request)

    def configure_request_logging(self):
        # Diretório de logs configurável via ENV
        diretorio_logs = os.getenv('ERROR_LOGS', None)
        if diretorio_logs:
            if not os.path.exists(diretorio_logs):
                os.makedirs(diretorio_logs)

            log_path = os.path.join(diretorio_logs, 'app_requests_400.log')

            handler = RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,
                backupCount=3
            )
            handler.setLevel(logging.WARNING)
            self.logger.addHandler(handler)

            #
            # Hook que intercepta *todas* as respostas do Flask
            #
            @self.after_request
            def log_bad_requests(response):
                code = response.status_code
                if code in [400, 500]:
                    flask_request = flask.request
                    method = flask_request.method
                    path = flask_request.path
                    try:
                        body = flask_request.get_json()
                    except Exception:
                        body = {}

                    params = dict(flask_request.args)

                    log_data = {
                        "ip": flask_request.remote_addr,
                        "headers": dict(flask_request.headers),
                        "body": body,
                        "params": params
                    }

                    # caractere_divisor
                    ca_div = '#' * 60
                    comeco = f'{ca_div} {method}-{path}-{code} - {datetime.now()} {ca_div}\n'  # noqa
                    final = f"\n{ca_div}{ca_div}{ca_div}\n"

                    self.logger.warning(
                        comeco +
                        str(json.dumps(log_data, ensure_ascii=False)) +
                        final)
                return response

    def configure_msg_error_500(self):
        # usa o decorator errohandler para definir uma mensagem padrão para
        # qualquer erro 500 no servidor
        @self.errorhandler(500)
        def internal_error(error):
            msg = ("Ocorreu um erro interno no servidor, por favor entre em " +
                   "contato com o suporte.")
            return msg, 500

    def configure(self):
        self.config['BASEDIR'] = os.path.abspath(os.path.dirname(__file__))
        self.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        self.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.config['USE_WORKER'] = False
        self.config['PERMISSOES_POR_DOMINIO'] = \
            os.getenv('PERMISSOES_POR_DOMINIO', 'False').upper() == 'TRUE'

    def configure_commands(self):
        # add comando "bootstrap"
        bootstrap_decorator = self.cli.command(name='bootstrap',
                                               help='Perform bootstrap')
        bootstrap_command = bootstrap_decorator(self.bootstrap)
        self.cli.add_command(bootstrap_command)
        # add comando "dbupgrade"
        db_upgrade_decorator = self.cli.command(
            name='dbupgrade',
            help='Perform flask db upgrade e preenche o historico')
        db_upgrade_command = db_upgrade_decorator(self.dbupgrade)
        self.cli.add_command(db_upgrade_command)
        # add comando "dbdowngrade"
        db_downgrade_decorator = self.cli.command(
            name='dbdowngrade',
            help='Perform flask db downgrade e preenche o historico')
        db_downgrade_command = db_downgrade_decorator(self.dbdowngrade)
        self.cli.add_command(db_downgrade_command)

    def init_database(self):
        database.db.init_app(self)
        # Precisa de app_context para create_all funcionar
        with self.app_context():
            # ✅ Flag para evitar cleanup durante init
            flask.g.in_init = True
            database.db.create_all()

    def after_init_database(self):
        pass

    def _register_cleanup_handlers(self):  # noqa
        """
        ✅ NOVO (2025-10-28): Registra handlers de cleanup global.

        Deve ser chamado ANTES de processar qualquer requisição.
        Garante cleanup de sessões e search_path mesmo em caso de erro.
        """
        import logging
        from sqlalchemy import text

        logger = logging.getLogger(__name__)

        @self.teardown_appcontext
        def force_cleanup(exception=None):
            """
            Cleanup forçado ao final do contexto da aplicação.
            Executa SEMPRE, mesmo se houver exceção.

            Args:
                exception: Exceção que causou o teardown (None se sucesso)
            """
            try:
                # ✅ Rastrear de onde vem o cleanup
                import traceback
                stack = traceback.extract_stack()
                caller = stack[-3] if len(stack) > 3 else stack[-1]
                # print(f"\n🧹 CLEANUP CHAMADO de: {caller.filename}:{caller.lineno} ({caller.name})")

                # ✅ CORREÇÃO CRÍTICA: Não fazer cleanup durante bootstrap ou init!
                if getattr(flask.g, 'in_bootstrap', False):
                    # print("⏭️  SKIP CLEANUP - Bootstrap em execução\n")
                    return

                if getattr(flask.g, 'in_init', False):
                    # print("⏭️  SKIP CLEANUP - Inicialização em execução\n")
                    return

                # print("🧹 INICIANDO CLEANUP...")

                # Verificar flask.g antes de limpar
                tenant_before = getattr(flask.g, 'tenant_schema', None)
                # print(f"🔍 flask.g.tenant_schema antes do cleanup: {tenant_before}")

                # Verificar se há sessão ativa
                if hasattr(database.db, 'session'):
                    session = database.db.session

                    # Verificar search_path antes de resetar
                    try:
                        path_before = session.execute(
                            text('SHOW search_path')
                        ).scalar()
                        # print(f"🔍 Search path antes do cleanup: {path_before}")
                    except:
                        pass

                    # ✅ CORRIGIDO: Comportamento diferente para exceção vs sucesso
                    if exception:
                        # ❌ HOUVE EXCEÇÃO: Fazer rollback
                        if session.is_active:
                            # print("🔄 Rollback por exceção")
                            session.rollback()
                    else:
                        # ✅ SUCESSO: Não fazer nada com a transação
                        # O commit já foi feito pela operação/bootstrap
                        # print("✓ Transação já commitada, nenhum rollback necessário")
                        pass

                    # Resetar search_path para public
                    # Apenas para limpar o estado, sem commit/rollback
                    try:
                        # Usar conexão separada para resetar search_path
                        # sem interferir na sessão principal
                        with database.db.engine.connect() as conn:
                            conn.execute(text('SET search_path TO public'))
                            # print("✅ Search path resetado para public")
                    except Exception as e:
                        # print(f"⚠️ Erro ao resetar search_path: {e}")
                        pass

                    # Fechar e remover sessão apenas em caso de sucesso
                    # Se houve exceção, a sessão já pode estar em estado ruim
                    if not exception:
                        try:
                            session.close()
                            database.db.session.remove()
                            # print("✅ Sessão fechada e removida")
                        except Exception as e:
                            # print(f"⚠️ Erro ao fechar sessão: {e}")
                            pass

                # Limpar contexto Flask
                for attr in ('tenant_domain_id', 'tenant_schema'):
                    if hasattr(flask.g, attr):
                        try:
                            value = getattr(flask.g, attr)
                            delattr(flask.g, attr)
                            # print(f"✅ flask.g.{attr} = {value} removido")
                        except Exception:
                            pass

                # print("✅ CLEANUP CONCLUÍDO\n")

            except Exception as e:
                logger.error(f"❌ Erro no cleanup: {e}")

        logger.info("✅ Handler de cleanup registrado")

    def version(self):
        return viggocore_version

    def schedule_jobs(self):
        pass

    def inject_dependencies(self) -> ApiHandler:
        bootstrap_resources = {
            'USER': self.user_resources,
            'SYSADMIN': self.sysadmin_resources,
            'SYSADMIN_EXCLUSIVE': self.sysadmin_exclusive_resources
        }
        api_handler = ApiHandler(self.subsystems, bootstrap_resources)

        for subsystem in self.subsystems.values():
            subsystem.api = api_handler.api

        return api_handler

    def __validate_routes(self, subsystems):
        errors = []
        for subsystem in subsystems.values():
            errors = errors + subsystem.validate_routes()
        if errors:
            for i in errors:
                # print(i)  # TODO change to logger
                pass
            raise Exception(*errors)

    def _parse_systems(self, systems):
        user_resources = []
        sysadmin_resources = []
        sysadmin_exclusive_resources = []
        subsystems = []
        for system in systems:
            subsystems += system.subsystems
            user_resources += system.user_resources
            sysadmin_resources += system.sysadmin_resources
            sysadmin_exclusive_resources += system.sysadmin_exclusive_resources

        utils = InputResourceUtils
        user_resources = utils.remove_duplicates(user_resources)
        sysadmin_resources = utils.remove_duplicates(sysadmin_resources)
        sysadmin_exclusive_resources = utils.remove_duplicates(
            sysadmin_exclusive_resources)

        return (subsystems, user_resources,
                sysadmin_resources, sysadmin_exclusive_resources)

    def configure_celery(self):
        use_worker = self.config.get('USE_WORKER', False)
        if use_worker:
            celery.init_celery(self)

    def init_scheduler(self):
        self.scheduler = scheduler.Scheduler()
        self.schedule_jobs()

    # alteração do comando "db upgrade"
    def dbupgrade(self, directory=None, revision='head', sql=False,
                  tag=None, x_arg=None):
        migration_upgrade.dbupgrade(directory, revision, sql, tag, x_arg)

    # alteração do comando "db downgrade"
    def dbdowngrade(self, directory=None, revision='-1', sql=False,
                    tag=None, x_arg=None):
        migration_downgrade.dbdowngrade(directory, revision, sql, tag,
                                        x_arg)

    # MÉTODO ANTIGO
    # def bootstrap(self):
    #     """Bootstrap the system.

    #     - routes;
    #     - TODO(samueldmq): sysadmin;
    #     - default domain with admin and capabilities.

    #     """

    #     with self.app_context():
    #         api = self.api_handler.api()
    #         Bootstrap(api,
    #                   self.subsystems,
    #                   self.user_resources,
    #                   self.sysadmin_resources,
    #                   self.sysadmin_exclusive_resources).\
    #             execute()
    def bootstrap(self):
        """
        ✅ CORRIGIDO (2025-10-28): Bootstrap com commit ao final

        Bootstrap the system:
        - routes;
        - sysadmin;
        - default domain with admin and capabilities.

        IMPORTANTE: Agora faz commit explícito ao final para persistir dados.
        """

        with self.app_context():
            # ✅ Flag para indicar que estamos em bootstrap
            # (cleanup não deve interferir)
            flask.g.in_bootstrap = True

            try:
                # print("\n" + "="*80)
                # print("🚀 INICIANDO BOOTSTRAP DO SISTEMA")
                # print("="*80 + "\n")

                # ✅ 1. CONFIGURAR SCHEMA PADRÃO
                self._configure_default_schema()

                # ✅ 2. EXECUTAR BOOTSTRAP
                api = self.api_handler.api()

                # Verificar estado da sessão antes do bootstrap
                # print("🔍 Sessão ativa antes do bootstrap: "
                #       f"{database.db.session.is_active}")

                Bootstrap(api,
                          self.subsystems,
                          self.user_resources,
                          self.sysadmin_resources,
                          self.sysadmin_exclusive_resources).execute()

                # Verificar estado após bootstrap
                # print(
                #     "🔍 Sessão ativa após bootstrap: "
                #     f"{database.db.session.is_active}")

                # ✅ 3. VERIFICAR dados ANTES do commit (na memória)
                from viggocorev2.subsystem.role.resource import Role
                roles_in_session = database.db.session.query(Role).count()
                # print(f"🔍 Roles na sessão (antes commit): {roles_in_session}")

                # ✅ 4. COMMIT DIRETO NA CONEXÃO
                # print("\n💾 Executando commit...")

                # Pegar conexão subjacente e fazer commit
                connection = database.db.session.connection()
                # print(f"🔍 Conexão em transação: {connection.in_transaction()}")
                connection.commit()

                # print("✅ COMMIT da conexão realizado!")

                # ✅ 5. VERIFICAR com nova conexão independente
                # print("\n🔍 Verificando persistência com nova conexão...")
                with database.db.engine.connect() as conn:
                    conn.execute(text('SET search_path TO default_schema'))
                    role_count = conn.execute(
                        text('SELECT COUNT(*) FROM role')
                    ).scalar()
                    # print(f"📊 Total de roles no banco: {role_count}")

                    if role_count > 0:
                        roles = conn.execute(
                            text('SELECT name FROM role ORDER BY name')
                        ).fetchall()
                        # print(f"📋 Roles: {[r[0] for r in roles]}")
                        # print("✅ DADOS PERSISTIDOS COM SUCESSO!")
                    else:
                        # print("❌ DADOS NÃO FORAM PERSISTIDOS!")
                        pass

                # print("\n" + "="*80)
                # print("✅ BOOTSTRAP CONCLUÍDO COM SUCESSO")
                # print("="*80 + "\n")

                # ✅ NÃO remover a flag aqui!
                # Ela será removida automaticamente pelo cleanup do flask.g

            except Exception as e:
                # print(f"\n❌ ERRO NO BOOTSTRAP: {e}")
                database.db.session.rollback()
                # print("🔄 Rollback realizado")
                raise

    def _criar_func_viggocore_normalize(self):
        viggocore_normalize = """
        CREATE OR REPLACE FUNCTION public.viggocore_normalize(text)
        RETURNS text
        LANGUAGE sql
        IMMUTABLE STRICT
        AS $function$
                SELECT trim(regexp_replace(translate(
                    lower($1),
                    'áàâãäåāăąèééêëēĕėęěìíîïìĩīĭḩóôõöōŏőùúûüũūŭůäàáâãåæçćĉčöòóôõøüùúûßéèêëýñîìíïşṕ',
                    'aaaaaaaaaeeeeeeeeeeiiiiiiiihooooooouuuuuuuuaaaaaaeccccoooooouuuuseeeeyniiiisp'
                ), '[^a-z0-9%\-]+', ' ', 'g'));
                $function$
        ;
        """  # noqa

        # ✅ Criar função normalize automaticamente
        database.db.session.execute(text(viggocore_normalize))

    def _configure_default_schema(self):
        """
        ✅ NOVO: Configura conexão para usar default_schema
        """
        default_schema = "default_schema"
        try:
            # ✅ Configurar search_path no PostgreSQL
            with database.db.engine.connect() as conn:
                conn = conn.execution_options(autocommit=True)
                conn.execute(
                    text(f'CREATE SCHEMA IF NOT EXISTS "{default_schema}"'))
                conn.execute(
                    text(f'SET search_path TO "{default_schema}", public'))

            # ✅ Criar função normalize automaticamente
            viggocore_normalize = """
                CREATE OR REPLACE FUNCTION public.viggocore_normalize(text)
                RETURNS text
                LANGUAGE sql
                IMMUTABLE STRICT
                AS $function$
                        SELECT trim(regexp_replace(translate(
                            lower($1),
                            'áàâãäåāăąèééêëēĕėęěìíîïìĩīĭḩóôõöōŏőùúûüũūŭůäàáâãåæçćĉčöòóôõøüùúûßéèêëýñîìíïşṕ',
                            'aaaaaaaaaeeeeeeeeeeiiiiiiiihooooooouuuuuuuuaaaaaaeccccoooooouuuuseeeeyniiiisp'
                        ), '[^a-z0-9%\-]+', ' ', 'g'));
                        $function$
                ;
                """  # noqa
            database.db.session.execute(text(viggocore_normalize))

            # ✅ Configurar na sessão atual
            database.db.session.execute(
                text(f'SET search_path TO "{default_schema}", public'))
            database.db.session.commit()

            # ✅ Armazenar no contexto Flask
            flask.g.tenant_schema = default_schema
        except Exception as e:
            raise e
