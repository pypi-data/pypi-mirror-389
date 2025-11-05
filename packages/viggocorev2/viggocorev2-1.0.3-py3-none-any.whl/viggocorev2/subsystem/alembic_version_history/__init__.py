from viggocorev2.common import subsystem
from viggocorev2.subsystem.alembic_version_history import resource, router

subsystem = subsystem.Subsystem(resource=resource.AlembicVersionHistory,
                                router=router.Router)
