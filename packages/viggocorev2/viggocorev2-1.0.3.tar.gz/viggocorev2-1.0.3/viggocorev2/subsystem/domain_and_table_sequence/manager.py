from viggocorev2.common import exception
from viggocorev2.common.subsystem import operation, manager


class GetNextVal(operation.Operation):
    def pre(self, session, table_id, name, **kwargs):
        if not name or not table_id:
            raise exception.BadRequest(
                'Os campos "table_id" e "name" são obrigatórios.')
        self.name = name
        self.table_id = table_id

        return True

    def do(self, session, **kwargs):
        nextval = self.driver.get_nextval(session, self.table_id, self.name)

        if nextval is None:
            raise exception.ViggoCoreException(
                'Não foi possível recuperar o próximo valor.')

        return nextval


class Manager(manager.Manager):

    def __init__(self, driver):
        super(Manager, self).__init__(driver)
        self.get_nextval = GetNextVal(self)
