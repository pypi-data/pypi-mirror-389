from viggocorev2.common import subsystem
from viggocorev2.subsystem.tag import resource, router, manager, controller


subsystem = subsystem.Subsystem(resource=resource.Tag,
                                router=router.Router,
                                manager=manager.Manager,
                                controller=controller.Controller)
