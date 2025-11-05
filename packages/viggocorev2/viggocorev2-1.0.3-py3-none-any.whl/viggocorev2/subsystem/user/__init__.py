from viggocorev2.common import subsystem
from viggocorev2.subsystem.user import resource

from viggocorev2.subsystem.user import controller
from viggocorev2.subsystem.user import manager
from viggocorev2.subsystem.user import router


subsystem = subsystem.Subsystem(resource=resource.User,
                                router=router.Router,
                                controller=controller.Controller,
                                manager=manager.Manager)
