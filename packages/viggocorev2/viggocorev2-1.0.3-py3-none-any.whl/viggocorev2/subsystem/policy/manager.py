import flask

from viggocorev2.common import exception
from viggocorev2.common.subsystem import manager, operation
from viggocorev2.subsystem.capability.resource import Capability
from viggocorev2.subsystem.application.resource import Application
from flask.globals import current_app


class Create(operation.Create):

    def do(self, session, **kwargs):
        # Cria a Policy normalmente
        super().do(session, **kwargs)

        try:
            # Só dispara replicação automática quando estiver no schema fonte
            current_schema = getattr(flask.g, 'tenant_schema', None)
            if current_schema != 'default_schema':
                return self.entity

            # Recupera a aplicação da capability para ler configurações
            capability = session.query(Capability) \
                .filter(Capability.id == self.entity.capability_id) \
                .first()
            if not capability:
                return self.entity

            application = session.query(Application) \
                .filter(Application.id == capability.application_id) \
                .first()
            if not application:
                return self.entity

            # Se PERMISSOES_POR_DOMINIO=False, replicar policies ausentes
            if current_app.config['PERMISSOES_POR_DOMINIO'] is False:
                # Executa inserção somente do que estiver faltando nos tenants
                self.manager.api.applications() \
                    .replicate_policies_from_default(dry_run=False)

        except exception.ViggoCoreException:
            # Propaga erros de domínio de negócio da própria API
            raise
        except Exception:
            # Não falha a criação da policy por erro no hook
            pass

        return self.entity


class Manager(manager.Manager):

    def __init__(self, driver):
        super().__init__(driver)
        self.create = Create(self)

