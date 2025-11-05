from viggocorev2.common import exception
from viggocorev2.common.subsystem import operation


class Delete(operation.Delete):

    def _verificar_se_prosseguir(self, session):
        query = """
            SELECT count(*)
            FROM "grant" g
                JOIN "role" r ON r.id = g.role_id
            WHERE r.name ilike 'Sysadmin'
                AND g.id <> '{entity_id}';"""
        result = session.execute(query.format(entity_id=self.entity.id))
        if result == 0:
            exception.BadRequest(
                'Não é possível remover todos os papéis de Sysadmin, ' +
                'deve ficar ao menos um usuário com este papel.')

    def do(self, session, **kwargs):
        self._verificar_se_prosseguir(session=session)
        return super().do(session, **kwargs)
