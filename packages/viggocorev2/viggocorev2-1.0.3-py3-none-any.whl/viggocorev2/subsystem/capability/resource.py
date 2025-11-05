from viggocorev2.database import db
from sqlalchemy import UniqueConstraint, orm
from viggocorev2.common.subsystem import entity, schema_model
from datetime import datetime


class Capability(entity.Entity, schema_model.PublicModel):

    attributes = ['route_id', 'application_id']
    attributes += entity.Entity.attributes

    route_id = db.Column(
        db.CHAR(32), db.ForeignKey("public.route.id"), nullable=False)
    route = orm.relationship('Route', backref=orm.backref('capabilities'))
    application_id = db.Column(
        db.CHAR(32), db.ForeignKey("public.application.id"), nullable=False)
    application = orm.relationship('Application', backref=orm.backref(
        'capabilities'))

    table_args_base = schema_model.PublicModel.__table_args__
    __table_args__ = (
        UniqueConstraint('route_id', 'application_id', name='capability_uk'),
        table_args_base)

    def __init__(self, id, route_id, application_id,
                 active=True, created_at=datetime.now(), created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.route_id = route_id
        self.application_id = application_id

    @classmethod
    def collection(cls):
        return 'capabilities'
