from viggocorev2.common import subsystem
from viggocorev2.subsystem.domain import manager, resource, controller, router

subsystem = subsystem.Subsystem(resource=resource.Domain,
                                controller=controller.Controller,
                                manager=manager.Manager,
                                router=router.Router)
