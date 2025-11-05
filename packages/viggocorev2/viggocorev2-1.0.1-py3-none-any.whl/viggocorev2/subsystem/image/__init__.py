from viggocorev2.common import subsystem
from viggocorev2.subsystem.image import resource, manager, controller, router

subsystem = subsystem.Subsystem(resource=resource.Image,
                                manager=manager.Manager,
                                controller=controller.Controller,
                                router=router.Router)
