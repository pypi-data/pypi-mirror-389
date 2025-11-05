from viggocorev2.common import subsystem
from viggocorev2.subsystem.file import resource
from viggocorev2.subsystem.file import manager
from viggocorev2.subsystem.file import controller

subsystem = subsystem.Subsystem(resource=resource.File,
                                manager=manager.Manager,
                                controller=controller.Controller)
