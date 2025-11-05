from viggocorev2.common import subsystem
from viggocorev2.subsystem.functionality \
    import manager, resource, controller, router

subsystem = subsystem.Subsystem(resource=resource.Functionality,
                                controller=controller.Controller,
                                manager=manager.Manager,
                                router=router.Router)
