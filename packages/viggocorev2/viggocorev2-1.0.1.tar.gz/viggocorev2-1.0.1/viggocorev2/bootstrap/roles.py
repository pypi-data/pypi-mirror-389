from viggocorev2.common.subsystem.apihandler import Api
import uuid

from typing import Dict, List

from viggocorev2.common.subsystem import Subsystem
from viggocorev2.subsystem.role.resource import Role, RoleDataViewType


class BootstrapRoles(object):

    def __init__(self, api: Api) -> None:
        self.role_manager = api.roles()

    def execute(self):
        roles = self.role_manager.list()
        if not roles:
            default_roles = self._default_roles()
            roles = self.role_manager.create_roles(roles=default_roles)
        return roles

    def _get_role(self, name: str, data_view: RoleDataViewType, numero=None) -> Role:  # noqa
        role = Role(id=uuid.uuid4().hex, name=name, data_view=data_view,
                    numero=numero)
        return role

    def _default_roles(self) -> List[Role]:
        user = self._get_role(Role.USER, RoleDataViewType.DOMAIN, 0)
        sysadmin = self._get_role(Role.SYSADMIN, RoleDataViewType.MULTI_DOMAIN, -1)
        admin = self._get_role(Role.ADMIN, RoleDataViewType.DOMAIN, -2)
        suporte = self._get_role(Role.SUPORTE, RoleDataViewType.MULTI_DOMAIN, -3)

        return [user, sysadmin, admin, suporte]
