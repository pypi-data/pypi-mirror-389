from viggocorev2.common import subsystem
from viggocorev2.subsystem.capability import resource, manager


subsystem = subsystem.Subsystem(resource=resource.Capability,
                                manager=manager.Manager)
