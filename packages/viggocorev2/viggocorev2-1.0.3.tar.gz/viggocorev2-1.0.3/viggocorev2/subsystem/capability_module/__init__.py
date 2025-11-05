from viggocorev2.common import subsystem
from viggocorev2.subsystem.capability_module \
    import manager, resource, controller, router

subsystem = subsystem.Subsystem(resource=resource.CapabilityModule,
                                controller=controller.Controller,
                                manager=manager.Manager,
                                router=router.Router)
