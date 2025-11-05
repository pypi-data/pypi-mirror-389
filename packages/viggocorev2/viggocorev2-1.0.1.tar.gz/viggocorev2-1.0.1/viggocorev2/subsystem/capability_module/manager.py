from viggocorev2.common import manager, exception
from viggocorev2.common.subsystem import operation
from viggocorev2.common.subsystem.pagination import Pagination
from viggocorev2.subsystem.capability_module.resource \
    import CapabilityModule
from viggocorev2.subsystem.module.resource \
    import Module
from sqlalchemy import or_


class GetAvailableModules(operation.List):

    def pre(self, **kwargs):
        self.application_id = kwargs.get('application_id', None)
        if self.application_id is None:
            raise exception.BadRequest(
                'O campo "application_id" é obrigatório.')
        return super().pre(**kwargs)

    def do(self, session, **kwargs):
        query = session.query(Module). \
            join(CapabilityModule,
                 CapabilityModule.module_id == Module.id,
                 isouter=True) \
            .filter(
                or_(CapabilityModule.application_id != self.application_id,  # noqa
                    CapabilityModule.application_id == None))  # noqa
        query = self.manager.apply_filters(query, Module, **kwargs)
        query = query.distinct()

        dict_compare = {'capability_module.': CapabilityModule}
        query = self.manager.apply_filters_includes(
            query, dict_compare, **kwargs)
        query = query.distinct()

        total_rows = None
        if self.manager.with_pagination(**kwargs):
            total_rows = query.count()

        pagination = Pagination.get_pagination(Module, **kwargs)
        if pagination.order_by is not None:
            pagination.adjust_order_by(Module)
        query = self.driver.apply_pagination(query, pagination)
        result = query.all()

        return (result, total_rows)


class GetSelectedModules(operation.List):

    def pre(self, **kwargs):
        self.application_id = kwargs.get('application_id', None)
        if self.application_id is None:
            raise exception.BadRequest(
                'O campo "application_id" é obrigatório.')
        return super().pre(**kwargs)

    def do(self, session, **kwargs):
        query = session.query(Module, CapabilityModule.id). \
            join(CapabilityModule,
                 CapabilityModule.module_id == Module.id,
                 isouter=True) \
            .filter(
                CapabilityModule.application_id == self.application_id)
        query = self.manager.apply_filters(query, Module, **kwargs)
        query = query.distinct()

        dict_compare = {'capability_module.': CapabilityModule}
        query = self.manager.apply_filters_includes(
            query, dict_compare, **kwargs)
        query = query.distinct()

        total_rows = None
        if self.manager.with_pagination(**kwargs):
            total_rows = query.count()

        pagination = Pagination.get_pagination(Module, **kwargs)
        if pagination.order_by is not None:
            pagination.adjust_order_by(Module)
        query = self.driver.apply_pagination(query, pagination)
        result = query.all()

        return (result, total_rows)


class Delete(operation.Delete):

    def pre(self, session, id, **kwargs):
        super().pre(session, id=id)
        policies = self.manager.api.policy_modules().list(
            capability_module_id=id)
        if policies:
            message = (
                'Você não pode remover essa funcionalidade porque'
                ' existem políticas associadas.')
            raise exception.BadRequest(message)
        return True


class Manager(manager.CommonManager):

    def __init__(self, driver):
        super(Manager, self).__init__(driver)
        self.get_available_modules = GetAvailableModules(self)
        self.get_selected_modules = GetSelectedModules(self)
        self.delete = Delete(self)
