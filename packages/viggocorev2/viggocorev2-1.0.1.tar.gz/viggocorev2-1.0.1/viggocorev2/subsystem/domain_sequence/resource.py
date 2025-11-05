from viggocorev2.database import db
from viggocorev2.common.subsystem import entity, schema_model


class DomainSequence(entity.Entity, schema_model.DynamicSchemaModel):

    attributes = ['name', 'value']
    attributes += entity.Entity.attributes

    name = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Numeric(10), default=0, nullable=False)

    def __init__(self, id, name, value,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.name = name
        self.value = value

    @classmethod
    def individual(cls):
        return 'domain_sequence'

    def is_stable(self):
        name_stable = self.name is not None
        value_stable = self.value is not None and self.value >= 0

        return name_stable and value_stable
