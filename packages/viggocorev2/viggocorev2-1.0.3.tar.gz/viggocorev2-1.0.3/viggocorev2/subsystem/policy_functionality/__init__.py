from viggocorev2.common import subsystem
from viggocorev2.subsystem.policy_functionality \
    import manager, resource, controller, router

subsystem = subsystem.Subsystem(resource=resource.PolicyFunctionality,
                                controller=controller.Controller,
                                manager=manager.Manager,
                                router=router.Router)
