from viggocorev2.common import exception
from viggocorev2.common.subsystem import operation, manager


class GetNextVal(operation.Operation):
    def pre(self, session, name, **kwargs):
        if not name:
            raise exception.BadRequest(
                'O campo "name" é obrigatório para pegar o próximo valor.')
        self.name = name

        return True

    def do(self, session, **kwargs):
        nextval = self.driver.get_nextval(session, self.name)

        if nextval is None:
            raise exception.ViggoCoreException(
                'Não foi possível recuperar o próximo valor.')

        return nextval


class Manager(manager.Manager):

    def __init__(self, driver):
        super(Manager, self).__init__(driver)
        self.get_nextval = GetNextVal(self)
