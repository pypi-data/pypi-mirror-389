from viggocorev2.database import db
from sqlalchemy import UniqueConstraint
from viggocorev2.common.subsystem import entity, schema_model


class Tag(entity.Entity, schema_model.PublicModel):

    attributes = ['domain_id', 'name', 'color', 'description', 'tag_name']
    attributes += entity.Entity.attributes

    domain_id = db.Column(
        db.CHAR(32), db.ForeignKey('public.domain.id'), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    color = db.Column(db.CHAR(7), nullable=False)
    description = db.Column(db.String(1024), nullable=False)
    tag_name = db.Column(db.String(60), nullable=False)

    table_args_base = schema_model.PublicModel.__table_args__
    __table_args__ = (
        UniqueConstraint('domain_id', 'name', name='tag_domain_id_name_uk'),
        UniqueConstraint('domain_id', 'tag_name',
                         name='tag_domain_id_tag_name_uk'),
        table_args_base)

    def __init__(self, id, domain_id, name, color, description, tag_name,
                 active=True, created_at=None, created_by=None,
                 updated_at=None, updated_by=None, tag=None):
        super().__init__(id, active, created_at, created_by,
                         updated_at, updated_by, tag)
        self.domain_id = domain_id
        self.name = name
        self.color = color
        self.description = description
        self.tag_name = tag_name
