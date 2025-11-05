import uuid
import flask
from sqlalchemy import text
from viggocorev2.common import exception
from viggocorev2.subsystem.domain import tasks
from viggocorev2.common.subsystem import operation
from viggocorev2.subsystem.role.resource import Role, RoleDataViewType


class ConfiguracaoInicial(operation.List):

    def _criar_policies_default(self, session, domain_id):
        """
        ✅ CORRIGIDO (2025-10-28): Cria policies usando a transação existente

        IMPORTANTE: NÃO faz commit aqui! A transação será commitada
        pelo operation.__call__() ao final. Usa flush() para garantir
        que os dados sejam enviados ao banco dentro da transação.
        """

        try:
            # Verificar search_path antes de criar policies
            path_antes = session.execute(text('SHOW search_path')).scalar()
            # print(f"🔍 Search path antes de criar policies: {path_antes}")

            query = text(f'''
                INSERT INTO "{domain_id}"."policy"
                (capability_id, role_id, id, active, created_at, created_by, updated_at, updated_by, tag)
                SELECT 
                    p.capability_id,
                    dest_role.id AS role_id,
                    md5((random())::text) AS id,
                    p.active,
                    NOW() AS created_at,
                    p.created_by,
                    NOW() AS updated_at,
                    p.updated_by,
                    p.tag
                FROM "default_schema"."policy" p
                    INNER JOIN "default_schema"."role" source_role ON source_role.id = p.role_id
                    INNER JOIN "{domain_id}"."role" dest_role ON dest_role.name = source_role.name
                WHERE p.active = true
            ''')  # noqa

            # ✅ EXECUTAR query
            result = session.execute(query)

            # ✅ FLUSH ao invés de COMMIT
            # Flush envia dados para o banco mas mantém transação aberta
            session.flush()

            # print(f"✅ {result.rowcount} policies criadas para domain {domain_id}")
            return result.rowcount

        except Exception as e:
            # print(f"❌ Erro ao criar policies para domain {domain_id}: {e}")
            # NÃO fazer rollback aqui - deixar operation.__call__() gerenciar
            raise

    def _get_role(self, name: str, data_view: RoleDataViewType, numero=None):
        role = Role(id=uuid.uuid4().hex, name=name, data_view=data_view,
                    numero=numero)
        return role

    def _default_roles(self):
        user = self._get_role(Role.USER, RoleDataViewType.DOMAIN, 0)
        sysadmin = self._get_role(
            Role.SYSADMIN, RoleDataViewType.MULTI_DOMAIN, -1)
        admin = self._get_role(Role.ADMIN, RoleDataViewType.DOMAIN, -2)
        suporte = self._get_role(
            Role.SUPORTE, RoleDataViewType.MULTI_DOMAIN, -3)

        return [user, sysadmin, admin, suporte]

    def _criar_papeis_default(self, domain_id):
        default_roles = self._default_roles()
        roles = self.manager.api.roles().create_roles(
            session=self.manager.driver.transaction_manager.session,
            roles=default_roles)
        return roles

    def pre(self, session, **kwargs):
        self.domain_name = kwargs.get('domain_name', None)
        self.username = kwargs.get('username', 'admin').lower()
        self.email = kwargs.get('email', None)
        self.password = kwargs.get('password', None)

        if None in [self.domain_name, self.username, self.email, self.password]:
            raise exception.BadRequest(
                'É obrigatório informar o domain_name, o username, ' +
                'o email, e o password.')

        return True

    def do(self, session, **kwargs):
        # 🔍 DEBUG: Verificar estado inicial do flask.g
        tenant_antes = getattr(flask.g, 'tenant_schema', None)
        # print(f"\n{'='*80}")
        # print(f"🔍 INÍCIO DO DO() - flask.g.tenant_schema = {tenant_antes}")

        # Verificar search_path inicial
        path_inicial = session.execute(text('SHOW search_path')).scalar()
        # print(f"🔍 Search path inicial: {path_inicial}")
        # print(f"{'='*80}\n")

        # ✅ CORREÇÃO 1: Buscar domain (está no schema 'public')
        domains = self.manager.api.domains().list(
            session=session, name=self.domain_name)
        if not domains:
            raise exception.BadRequest('Domínio não encontrado.')

        self.domain = domains[0]
        domain = domains[0]

        # print(f"📋 Domain encontrado: {domain.id} (nome: {domain.name})")

        # ✅ CORREÇÃO 2: Configurar contexto Flask
        flask.g.tenant_domain_id = domain.id
        flask.g.tenant_schema = domain.id
        # print(f"✅ flask.g.tenant_schema configurado para: {domain.id}")

        # ✅ CORREÇÃO 3: FORÇAR search_path imediatamente!
        # IMPORTANTE: NÃO fazer commit aqui! A transação já foi iniciada
        # pelo operation.__call__() e será commitada no final.
        session.execute(text(f'SET search_path TO "{domain.id}", public'))

        # Verificar se search_path foi aplicado
        current_path = session.execute(text('SHOW search_path')).scalar()
        # print(f"🔧 Search path configurado: {current_path}")

        # ✅ CORREÇÃO 4: Verificar se ROLES já existem (não users!)
        # Verificar search_path antes de consultar roles
        path_before = session.execute(text('SHOW search_path')).scalar()
        # print(f"🔍 Search path antes de consultar roles: {path_before}")

        existing_roles = self.manager.api.roles().list(
            session=session)

        if not existing_roles:
            # print(f"📝 Criando estrutura inicial para domain {domain.id}")

            # Verificar search_path antes de criar roles
            path_before_create = session.execute(text('SHOW search_path')).scalar()
            # print(f"🔍 Search path antes de criar roles: {path_before_create}")

            # cria os papéis default no esquema do tenant
            self._criar_papeis_default(self.domain.id)
        else:
            # print(f"✓ Domain {domain.id} já possui {len(existing_roles)} roles")
            pass

        # ✅ CORREÇÃO 5: Buscar ou criar usuário
        users = self.manager.api.users().list(
            session=session,
            domain_id=domain.id,
            name=self.username
        )

        if not users:
            # print(f"📝 Criando usuário {self.username} para domain {domain.id}")

            # Verificar search_path antes de criar usuário
            path_before_user = session.execute(text('SHOW search_path')).scalar()
            # print(f"🔍 Search path antes de criar usuário: {path_before_user}")

            # cria o usuário já com o papel User
            self.user = self.manager.api.users().create(
                session=session,
                name=self.username,
                email=self.email,
                domain_id=self.domain.id,
                active=False
            )

            # print(f"✅ Usuário criado: {self.user.id}")

            # reseta a senha do usuário
            self.manager.api.users().reset(
                session=session,
                id=self.user.id,
                password=self.password
            )

            # busca o papel sysadmin
            role = self.manager.api.roles().get_role_by_name(
                session=session,
                role_name=Role.SYSADMIN
            )

            # adiciona o papel sysadmin
            self.manager.api.grants().create(
                session=session,
                role_id=role.id,
                user_id=self.user.id
            )
        else:
            # print(f"✓ Usuário {self.username} já existe no domain {domain.id}")
            self.user = users[0]

            # Atualiza senha mesmo se usuário já existe
            self.manager.api.users().reset(
                session=session,
                id=self.user.id,
                password=self.password
            )

        if not users:
            # criar policies default (movido para cá)
            self._criar_policies_default(session, self.domain.id)

        # 🔍 DEBUG: Verificar estado final
        path_final = session.execute(text('SHOW search_path')).scalar()
        tenant_final = getattr(flask.g, 'tenant_schema', None)
        # print(f"\n{'='*80}")
        # print(f"🔍 FIM DO DO()")
        # print(f"   Domain processado: {domain.id}")
        # print(f"   flask.g.tenant_schema: {tenant_final}")
        # print(f"   Search path: {path_final}")
        # print(f"{'='*80}\n")

        return True

    def post(self):
        if not hasattr(self, 'user'):
            # The notification don't be part of transaction must be on post
            tasks.send_email(self.user.id)
