from viggocorev2.common import subsystem
from viggocorev2.subsystem.role \
    import resource, router, controller, manager

subsystem = subsystem.Subsystem(resource=resource.Role,
                                router=router.Router,
                                controller=controller.Controller,
                                manager=manager.Manager)
