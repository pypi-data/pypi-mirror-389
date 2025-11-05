
from viggocorev2.common import subsystem

from viggocorev2.subsystem.log_system import \
    manager, resource, router


subsystem = subsystem.Subsystem(resource=resource.LogSystem,
                                manager=manager.Manager,
                                router=router.Router)
