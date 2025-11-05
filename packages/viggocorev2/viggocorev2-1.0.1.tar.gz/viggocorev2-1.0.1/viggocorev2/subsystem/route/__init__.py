from viggocorev2.common import subsystem
from viggocorev2.subsystem.route import resource, manager


subsystem = subsystem.Subsystem(resource=resource.Route,
                                manager=manager.Manager)
