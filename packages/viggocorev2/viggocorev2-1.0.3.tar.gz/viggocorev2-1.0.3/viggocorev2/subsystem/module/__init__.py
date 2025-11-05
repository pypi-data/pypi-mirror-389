from viggocorev2.common import subsystem
from viggocorev2.subsystem.module \
    import manager, resource, controller, router

subsystem = subsystem.Subsystem(resource=resource.Module,
                                controller=controller.Controller,
                                manager=manager.Manager,
                                router=router.Router)
