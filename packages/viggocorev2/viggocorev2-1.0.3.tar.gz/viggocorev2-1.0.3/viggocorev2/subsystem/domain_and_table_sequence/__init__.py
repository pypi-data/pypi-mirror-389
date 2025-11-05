from viggocorev2.common import subsystem
from viggocorev2.subsystem.domain_and_table_sequence \
    import resource, controller, manager, router, driver


subsystem = subsystem.Subsystem(resource=resource.DomainAndTableSequence,
                                controller=controller.Controller,
                                manager=manager.Manager,
                                router=router.Router,
                                driver=driver.Driver)
