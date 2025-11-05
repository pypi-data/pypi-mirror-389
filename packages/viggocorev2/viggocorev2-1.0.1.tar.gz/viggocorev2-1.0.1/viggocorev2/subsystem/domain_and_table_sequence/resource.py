from sqlalchemy import UniqueConstraint

from viggocorev2.database import db
from viggocorev2.common.subsystem import entity, schema_model


class DomainAndTableSequence(entity.Entity, schema_model.DynamicSchemaModel):

    attributes = ['table_id', 'name', 'value']
    attributes += entity.Entity.attributes

    table_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Numeric(10), default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'name',
            'table_id',
            name='domain_and_table_sequence_name_table_id_uk'),)

    def __init__(self, id, table_id, name, value,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.table_id = table_id
        self.name = name
        self.value = value

    @classmethod
    def individual(cls):
        return 'domain_and_table_sequence'

    def is_stable(self):
        table_id_stable = self.table_id is not None
        name_stable = self.name is not None
        value_stable = self.value is not None and self.value >= 0

        return table_id_stable and name_stable and value_stable
