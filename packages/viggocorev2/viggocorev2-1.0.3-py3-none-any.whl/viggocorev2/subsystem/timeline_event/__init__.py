from viggocorev2.common import subsystem
from viggocorev2.subsystem.timeline_event \
    import resource, controller, manager


subsystem = subsystem.Subsystem(resource=resource.TimelineEvent,
                                controller=controller.Controller,
                                manager=manager.Manager)
