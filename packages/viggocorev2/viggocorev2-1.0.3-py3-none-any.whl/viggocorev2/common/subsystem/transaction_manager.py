from contextlib import contextmanager
from sqlalchemy import text, event
from viggocorev2 import database
import flask
import threading
import logging

# ✅ CORRIGIDO (2025-10-28): Listener Singleton
# Flag global thread-safe - listener registrado apenas uma vez
_listener_lock = threading.Lock()
_listener_registered = False

logger = logging.getLogger(__name__)


class TransactionManager(object):
    """
    ✅ CORRIGIDO (2025-10-28): Gerenciador Thread-Safe

    IMPORTANTE: Listener registrado APENAS UMA VEZ (singleton).

    Como funciona:
    1. Primeira instância registra listener (singleton)
    2. Instâncias subsequentes reutilizam o mesmo
    3. Listener aplica search_path automaticamente
    4. Lê schema de flask.g (thread-local)

    HISTÓRICO:
    - Antes: Múltiplos listeners registrados
    - Problema: Overhead, execuções redundantes
    - Solução: Singleton com lock thread-safe
    """

    def __init__(self, session=None) -> None:
        self.count = 0
        self.session = database.db.session
        self.current_schema = None
        self.original_search_path = None

        # ✅ Garantir que listener seja registrado apenas uma vez (singleton)
        self._ensure_listener_registered()

    @classmethod
    def _ensure_listener_registered(cls):
        """
        ✅ NOVO: Garante listener registrado apenas UMA VEZ.

        Usa lock thread-safe para evitar race conditions.
        Registra no nível da classe Session.
        """
        global _listener_registered

        with _listener_lock:
            if not _listener_registered:
                # Registrar listener estático
                # propagate=True para sub-sessões
                event.listen(
                    database.db.session.__class__,
                    "after_begin",
                    cls._after_begin_static,
                    propagate=True
                )
                _listener_registered = True
                logger.info(
                    "✅ Listener search_path registrado"
                )

    @staticmethod
    def _after_begin_static(session, transaction, connection):
        """
        ✅ CORRIGIDO: Listener estático (automático).

        Aplica search_path ao iniciar transação.
        Lê schema de flask.g (thread-local).

        Args:
            session: Sessão SQLAlchemy
            transaction: Transação atual
            connection: Conexão do banco
        """
        try:
            # Obter schema do contexto Flask
            schema = getattr(flask.g, 'tenant_schema', None)
            if not schema:
                schema = getattr(
                    flask.g, 'tenant_domain_id', 'public'
                )

            # Aplicar search_path se não for public
            if schema and schema != 'public':
                connection.execute(
                    text(
                        f'SET search_path TO "{schema}", public'
                    )
                )
                logger.debug(f"🔧 Search path: {schema}")
        except Exception as e:
            # Log mas não quebra (flask.g pode não existir)
            logger.warning(
                f"⚠️ Erro search_path: {e}"
            )

    def set_schema(self, schema: str):
        """
        Configura o schema ativo para a sessão.
        Cria o schema se não existir.
        """
        conn = self.session.connection().execution_options(
            schema_translate_map={None: schema}
        )

        # Armazena search_path original na primeira vez
        if self.original_search_path is None:
            self.original_search_path = conn.execute(text("SHOW search_path")).scalar()

        if schema != "public":
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

        # Aplica na conexão atual
        conn.execute(text(f'SET search_path TO "{schema}", public'))
        self.current_schema = schema
        # print(f"🔧 Schema definido para {schema}")

    def begin(self):
        self.log('antes begin')
        self.count += 1
        self.log('apos begin')

    def commit(self):
        self.log('antes commit')
        self.count -= 1
        if self.count == 0:
            self.session.commit()
            self.log('apos commit')
        self.log('não fez commit')

    def rollback(self):
        self.session.rollback()
        self.count = -1000000
        self.log('apos rollback')

    def reset_schema(self):
        """
        Restaura o search_path original da sessão.
        """
        if self.original_search_path:
            self.session.execute(
                text(f'SET search_path TO {self.original_search_path}')
            )
        self.current_schema = None

    def shutdown(self):
        self.log('antes shutdown')
        self.reset_schema()
        self.session.remove()
        self.log('apos shutdown')

    def log(self, prefix=""):
        from sqlalchemy import text

        conn = self.session.connection()
        result = conn.execute(text("SHOW search_path")).scalar()

        # print(prefix, " - 🔍 search_path atual:", result, " - Original: ",
        #       self.original_search_path)

    def trace(self):
        import traceback
        # print("EXECUTANDO SET search_path para %s\nstack:\n%s",
        #       self.current_schema, ''.join(traceback.format_stack()))

    @contextmanager
    def transaction(self):
        """
        Context manager para transações.
        Faz commit automático se não houver exceção,
        rollback caso ocorra erro.
        """
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def auto_configure_from_flask(self):
        """
        Define schema automaticamente a partir de flask.g
        """
        try:
            schema = getattr(flask.g, "tenant_schema", None)
            if not schema:
                schema = getattr(flask.g, "tenant_domain_id", "public")
            self.set_schema(schema)
        except Exception as e:
            # print(f"⚠️ Erro auto-configurando schema: {e}")
            pass
