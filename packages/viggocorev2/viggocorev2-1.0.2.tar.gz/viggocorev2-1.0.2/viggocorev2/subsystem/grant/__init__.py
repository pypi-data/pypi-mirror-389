from viggocorev2.common import subsystem
from viggocorev2.subsystem.grant import resource, manager

subsystem = subsystem.Subsystem(
    resource=resource.Grant,
    manager=manager.Manager
)
