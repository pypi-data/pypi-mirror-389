from viggocorev2.common import subsystem
from viggocorev2.subsystem.application import resource, manager, controller, \
    router

subsystem = subsystem.Subsystem(resource=resource.Application,
                                manager=manager.Manager,
                                controller=controller.Controller,
                                router=router.Router)
