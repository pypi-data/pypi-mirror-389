from viggocorev2.common import subsystem, controller
from viggocorev2.subsystem.project_cost \
    import resource, manager

subsystem = subsystem.Subsystem(resource=resource.ProjectCost,
                                manager=manager.Manager,
                                controller=controller.CommonController)
