from viggocorev2.common import subsystem
from viggocorev2.subsystem.constant_for_calculation \
    import resource, router, controller, manager

subsystem = subsystem.Subsystem(resource=resource.ConstantForCalculation,
                                router=router.Router,
                                controller=controller.Controller,
                                manager=manager.Manager)
