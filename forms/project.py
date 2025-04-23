from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateTimeLocalField, BooleanField
from wtforms.validators import DataRequired


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Project')


class TaskForm(FlaskForm):
    name = StringField('Task Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    deadline = DateTimeLocalField('Deadline', format='%Y-%m-%dT%H:%M')
    submit = SubmitField('Add Task')
