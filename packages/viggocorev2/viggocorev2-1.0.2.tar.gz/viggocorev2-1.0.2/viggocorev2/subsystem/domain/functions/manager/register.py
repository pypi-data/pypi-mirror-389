import flask
from viggocorev2.common import exception
from viggocorev2.schema_manager import create_tenant_and_migrate
from viggocorev2.common.subsystem import operation


class Register(operation.Create):

    def pre(self, session, username, email, password,
            domain_name, domain_display_name, application_name):
        self.username = username
        self.email = email
        self.password = password
        self.domain_name = domain_name
        self.domain_display_name = domain_display_name
        self.application_name = application_name

        user_params_ok = username and email and password
        app_params_ok = domain_name and application_name
        if not user_params_ok and app_params_ok:
            raise exception.BadRequest(
                'Dados insuficientes para registrar o domínio.')

        applications = \
            self.manager.api.applications().list(name=application_name)
        if not applications:
            raise exception.BadRequest(
                f'Nenhuma aplicação com o nome {application_name} encontrado.')
        self.application = applications[0]

        return True

    def do(self, session, **kwargs):
        self.session = session
        domains = self.manager.api.domains().list(
            name=self.domain_name)
        if not domains:
            self._register_domain(
                self.domain_name, self.domain_display_name,
                self.application.id, self.username, self.email, self.password)

            flask.g.tenant_domain_id = self.domain.id
            flask.g.tenant_schema = self.domain.id
        else:
            self.domain = domains[0]
            domain = domains[0]

            flask.g.tenant_domain_id = domain.id
            flask.g.tenant_schema = domain.id

            users = self.manager.api.users().list(
                email=self.email,
                domain_id=domain.id)

            if domain.active:
                raise exception.BadRequest('O domínio já está ativo.')

            if domain.name == self.domain_name:
                raise exception.BadRequest(
                    'Já existe um domínio com este nome.')

            if not users:
                raise exception.BadRequest('O usuário não foi encontrado.')

            self.user = users[0]
            self.manager.api.users().reset(
                id=self.user.id,
                password=self.password)

        return True

    def post(self, **kwargs):
        # cria um novo esquema para o novo domínio e roda as migrações
        create_tenant_and_migrate(self.domain.id)

    def _register_domain(self, domain_name, domain_display_name,
                         application_id, username, email, password):
        self.domain = self.manager.api.domains().create(
            application_id=application_id, name=domain_name,
            display_name=domain_display_name,
            addresses=[], contacts=[], active=False)
