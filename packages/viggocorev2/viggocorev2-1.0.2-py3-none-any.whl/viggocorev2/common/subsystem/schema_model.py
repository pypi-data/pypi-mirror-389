import flask
from sqlalchemy.ext.declarative import declared_attr
from viggocorev2.database import db
from sqlalchemy import MetaData


# Classe base para modelos no esquema 'public'
class PublicModel(db.Model):
    __abstract__ = True
    __table_args__ = {'schema': 'public'}
    schema_args = {'schema': 'public'}


# Classe base para modelos em esquemas dinâmicos
class DynamicSchemaModel(db.Model):
    __abstract__ = True
