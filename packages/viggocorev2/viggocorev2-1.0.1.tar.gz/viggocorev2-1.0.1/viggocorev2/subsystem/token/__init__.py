from viggocorev2.common import subsystem
from viggocorev2.subsystem.token import manager
from viggocorev2.subsystem.token import resource
from viggocorev2.subsystem.token import router
from viggocorev2.subsystem.token import controller

subsystem = subsystem.Subsystem(resource=resource.Token,
                                manager=manager.Manager,
                                router=router.Router,
                                controller=controller.Controller)
