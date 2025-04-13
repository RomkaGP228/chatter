from flask import Flask, render_template, redirect, request, flash, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from data.projects import Project, Task
from forms.user import LoginForm, RegisterForm
from forms.project import ProjectForm, TaskForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    project_form = ProjectForm()
    projects = []
    
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        projects = db_sess.query(Project).filter(Project.user_id == current_user.id).all()
    
    if request.method == 'POST' and project_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in to create projects', 'error')
            return redirect(url_for('login'))
            
        db_sess = db_session.create_session()
        project = Project(
            name=project_form.name.data,
            description=project_form.description.data,
            user_id=current_user.id
        )
        db_sess.add(project)
        db_sess.commit()
        return redirect(url_for('index'))
    
    return render_template('index.html', projects=projects, project_form=project_form)


@app.route('/account', methods=['GET', 'POST'])
def account():
    if not current_user.is_authenticated:
        form = LoginForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for('account'))
            return render_template('account.html', form=form, message="Неправильный логин или пароль")
        return render_template('account.html', form=form)
    
    if request.method == 'POST':
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        
        if user:
            # Update basic information
            user.name = request.form.get('name')
            user.about = request.form.get('about')
            
            # Check if email is being changed
            new_email = request.form.get('email')
            if new_email != user.email:
                # Verify email is not already taken
                existing_user = db_sess.query(User).filter(User.email == new_email).first()
                if existing_user and existing_user.id != user.id:
                    flash('Email is already taken', 'error')
                    return redirect('/account')
                user.email = new_email
            
            # Handle password change if provided
            new_password = request.form.get('password')
            if new_password:
                user.set_password(new_password)
            
            db_sess.commit()
            flash('Account updated successfully!', 'success')
            return redirect('/account')
    
    return render_template('account.html')


@app.route('/projects', methods=['GET', 'POST'])
def projects():
    print(f"Current user: {current_user}")
    print(f"User authenticated: {current_user.is_authenticated}")
    
    project_form = ProjectForm()
    task_form = TaskForm()
    
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please log in to create a project', 'error')
            return redirect(url_for('login'))
            
        print("POST request received")
        print(f"Form data: {request.form}")
        if project_form.validate_on_submit():
            print("Form validated successfully")
            db_sess = db_session.create_session()
            project = Project(
                name=project_form.name.data,
                description=project_form.description.data,
                user_id=current_user.id
            )
            db_sess.add(project)
            db_sess.commit()
            flash('Project created successfully!', 'success')
            return redirect('/projects')
        else:
            print(f"Form validation errors: {project_form.errors}")
    
    db_sess = db_session.create_session()
    projects = []
    if current_user.is_authenticated:
        projects = db_sess.query(Project).filter(Project.user_id == current_user.id).all()
    return render_template('projects.html', projects=projects, project_form=project_form, task_form=task_form)


@app.route('/projects/task', methods=['POST'])
@login_required
def add_task():
    task_form = TaskForm()
    if task_form.validate_on_submit():
        db_sess = db_session.create_session()
        project = db_sess.query(Project).filter(
            Project.id == request.form.get('project_id'),
            Project.user_id == current_user.id
        ).first()
        
        if project:
            task = Task(
                name=task_form.name.data,
                description=task_form.description.data,
                deadline=task_form.deadline.data,
                project_id=project.id
            )
            db_sess.add(task)
            db_sess.commit()
            flash('Task added successfully!', 'success')
        else:
            flash('Project not found', 'error')
    return redirect('/projects')


@app.route('/projects/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if task:
        task.is_completed = not task.is_completed
        db_sess.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@app.route('/projects/task/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if task:
        db_sess.delete(task)
        db_sess.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@app.route('/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    db_sess = db_session.create_session()
    project = db_sess.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if project:
        db_sess.delete(project)
        db_sess.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


def main():
    db_session.global_init("db/database.db")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
