from viggocorev2.common.subsystem import manager
from viggocorev2.subsystem.grant.functions.manager.entity_delete import Delete


class Manager(manager.Manager):
    """
    Manager para Grant (relacionamento User-Role)

    Operações disponíveis:
    - create: Atribuir um papel (role) a um usuário
    - delete: Remover um papel de um usuário (com validação de Sysadmin)
    - list: Listar grants (herda do manager base)
    - get: Obter grant específico (herda do manager base)
    """

    def __init__(self, driver):
        super(Manager, self).__init__(driver)
        self.delete = Delete(self)
