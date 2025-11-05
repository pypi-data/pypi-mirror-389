from sqlalchemy import orm, UniqueConstraint

from viggocorev2.database import db
from viggocorev2.common.subsystem import entity, schema_model
from datetime import datetime


class CapabilityFunctionality(entity.Entity, schema_model.PublicModel):

    attributes = ['functionality_id', 'application_id']
    attributes += entity.Entity.attributes

    functionality_id = db.Column(
        db.CHAR(32), db.ForeignKey("public.functionality.id"), nullable=False)
    functionality = orm.relationship(
        'Functionality',
        backref=orm.backref('capability_functionality_functionality'))
    application_id = db.Column(
        db.CHAR(32), db.ForeignKey("public.application.id"), nullable=False)
    application = orm.relationship('Application', backref=orm.backref(
        'capability_functionality_application'))

    table_args_base = schema_model.PublicModel.__table_args__
    __table_args__ = (
        UniqueConstraint(
            'functionality_id', 'application_id',
            name='cp_functionality_id_application_id_uk'),
        table_args_base)

    def __init__(self, id, functionality_id, application_id,
                 active=True, created_at=datetime.now(), created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.functionality_id = functionality_id
        self.application_id = application_id

    @classmethod
    def individual(cls):
        return 'capability_functionality'

    @classmethod
    def collection(cls):
        return 'capability_functionalities'
