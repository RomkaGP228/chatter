import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Project(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'projects'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=sqlalchemy.func.now())
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    user = orm.relationship('User')
    tasks = orm.relationship('Task', back_populates='project', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project> {self.id} {self.name}'


class Task(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    deadline = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    is_completed = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    project_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('projects.id'))
    project = orm.relationship('Project', back_populates='tasks')

    def __repr__(self):
        return f'<Task> {self.id} {self.name}' 