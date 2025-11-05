from sqlalchemy import orm
from viggocorev2.database import db
from viggocorev2.common.subsystem import entity, schema_model
from sqlalchemy.ext.declarative import declared_attr


class TimelineEvent(entity.Entity, schema_model.DynamicSchemaModel):

    LIMIT_SEARCH = 30

    attributes = ['domain_id', 'event_at', 'event_by', 'lat', 'lon',
                  'description', 'entity', 'entity_id']
    attributes += entity.Entity.attributes

    domain_id = db.Column(
        db.CHAR(32), db.ForeignKey('public.domain.id'), nullable=False)
    event_at = db.Column(db.DateTime, nullable=False, unique=False)
    event_by = db.Column(db.CHAR(32), nullable=False, unique=False)
    lat = db.Column(db.Numeric(14, 8), nullable=False, unique=False)
    lon = db.Column(db.Numeric(14, 8), nullable=False, unique=False)
    description = db.Column(db.String(500), nullable=False, unique=False)
    entity = db.Column(db.String(100), nullable=True, unique=False)
    entity_id = db.Column(db.CHAR(32), nullable=True, unique=False)
    users = orm.relationship(
        "TimelineEventUser", backref=orm.backref('timeline_event_user'),
        cascade='delete,delete-orphan,save-update')

    __tablename__ = 'timeline_event'

    def __init__(self, id, domain_id, event_at, event_by, lat, lon,
                 description, entity=None, entity_id=None,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.id = id
        self.domain_id = domain_id
        self.event_at = event_at
        self.event_by = event_by
        self.lat = lat
        self.lon = lon
        self.description = description
        self.entity = entity
        self.entity_id = entity_id,

    @classmethod
    def individual(cls):
        return 'timeline_event'

    @classmethod
    def embedded(cls):
        return ['users']


class TimelineEventUser(entity.Entity, schema_model.DynamicSchemaModel):
    attributes = ['id', 'user_id']

    # timeline_event_id = db.Column(
    #     db.CHAR(32), db.ForeignKey("timeline_event.id"), nullable=False)

    # # Aqui precisamos incluir o esquema na referência
    # @declared_attr
    # def timeline_event_id(cls):
    #     schema_name = getattr(cls, '_schema_name', 'default_schema')
    #     return db.Column(db.CHAR(32),
    #                      db.ForeignKey(f'{schema_name}.timeline_event.id'),
    #                      nullable=False)
    timeline_event_id = db.Column(db.CHAR(32),
                                  db.ForeignKey('timeline_event.id'),
                                  nullable=False)

    user_id = db.Column(
        db.CHAR(32), db.ForeignKey("user.id"), nullable=False)

    user = orm.relationship(
        'User',
        foreign_keys=[user_id],
        primaryjoin="TimelineEventUser.user_id == User.id",
        backref=orm.backref('timeline_event_user'))

    def __init__(self, id, timeline_event_id, user_id,
                 active=True, created_at=None,
                 created_by=None, updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.timeline_event_id = timeline_event_id
        self.user_id = user_id

    def is_stable(self):
        if self.user_id is not None and self.timeline_event_id is not None:
            return True
        return False
