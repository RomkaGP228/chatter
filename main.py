from flask import Flask, render_template, redirect, request, flash, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from data.projects import Project, Task
from forms.user import LoginForm, RegisterForm
from datetime import datetime, timedelta
import os
from data.telegram_text import telegram
from data.scheduled_tasks import schedule_task, cancel_task

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandex_lyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    """Функция для загрузки информации о юзере"""
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/logout')
@login_required
def logout():
    """Функция двыхода из аккаунта"""
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Функция для регистрации аккаунта"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect(url_for('login'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Функция для входа в аккаунт"""
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
def index():
    """основная страница сайта"""
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        projects = db_sess.query(Project).filter(Project.user_id == current_user.id).all()
    else:
        projects = []

    # Инициализация переменных
    task_deadlines = {}
    selected_date = None

    # Получаем нынешний месяц
    month = request.args.get('month')
    if month:
        current_date = datetime.strptime(month, '%Y-%m')
    else:
        current_date = datetime.now()

    # Первый день месяца
    first_day = current_date.replace(day=1)

    # Последний день месяца
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

    # Количество дней в месяце
    days_in_month = last_day.day

    # День недели первого дня месяца
    first_day_weekday = first_day.weekday()

    # список дней
    calendar_days = []
    for i in range(1, days_in_month + 1):
        day_date = current_date.replace(day=i)
        has_tasks = any(
            task.deadline and task.deadline.date() == day_date.date()
            for project in projects
            for task in project.tasks
        )
        calendar_days.append({
            'day': i,
            'has_tasks': has_tasks,
            'date': day_date.strftime('%Y-%m-%d')
        })

    if request.method == 'POST':
        if 'selected_date' in request.form:
            selected_date = datetime.strptime(request.form['selected_date'], '%Y-%m-%d').date()
        elif 'task_id' in request.form:
            task_id = request.form['task_id']
            task = db_sess.get(Task, task_id)

            if task and task.project.user_id == current_user.id:
                if request.form.get('action') == 'edit':
                    # Показываем форму редактирования
                    selected_date = task.deadline.date() if task.deadline else None
                    # Собираем задачи для выбранной даты
                    if selected_date:
                        for project in projects:
                            for t in project.tasks:
                                if t.deadline and t.deadline.date() == selected_date:
                                    if selected_date not in task_deadlines:
                                        task_deadlines[selected_date] = []
                                    task_deadlines[selected_date].append({
                                        'id': t.id,
                                        'name': t.name,
                                        'description': t.description,
                                        'project_name': project.name,
                                        'deadline': t.deadline
                                    })
                    return render_template('index.html',
                                           projects=projects,
                                           current_date=current_date,
                                           calendar_days=calendar_days,
                                           first_day_weekday=first_day_weekday,
                                           selected_date=selected_date,
                                           task_deadlines=task_deadlines,
                                           editing_task=task)
                else:
                    # Сохраняем изменения
                    task.name = request.form['name']
                    task.description = request.form['description']
                    if request.form['deadline']:
                        task.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
                    else:
                        task.deadline = None
                    db_sess.commit()
                    flash('Задача успешно обновлена!', 'success')
                    
                    # Оптимизированное обновление task_deadlines только для измененной даты
                    selected_date = task.deadline.date() if task.deadline else None
                    if selected_date:
                        task_deadlines[selected_date] = []
                        for project in projects:
                            for t in project.tasks:
                                if t.deadline and t.deadline.date() == selected_date:
                                    task_deadlines[selected_date].append({
                                        'id': t.id,
                                        'name': t.name,
                                        'description': t.description,
                                        'project_name': project.name,
                                        'deadline': t.deadline
                                    })
                    
                    return render_template('index.html',
                                           projects=projects,
                                           current_date=current_date,
                                           calendar_days=calendar_days,
                                           first_day_weekday=first_day_weekday,
                                           selected_date=selected_date,
                                           task_deadlines=task_deadlines)
        elif 'delete_task' in request.form:
            task_id = request.form['delete_task']
            task = db_sess.get(Task, task_id)

            if task and task.project.user_id == current_user.id:
                selected_date = task.deadline.date() if task.deadline else None
                db_sess.delete(task)
                db_sess.commit()
                # отправка в теелграм
                telegram(current_user.telegram, f'Задача: {task.name} удалена!')
                flash('Задача успешно удалена!', 'success')
            else:
                flash('Ошибка: Задача не найдена или у вас нет прав на её удаление', 'error')

            return redirect(url_for('index', selected_date=selected_date.strftime('%Y-%m-%d') if selected_date else ''))
    else:
        selected_date_str = request.args.get('selected_date')
        if selected_date_str:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    # Собираем задачи для выбранной даты
    if selected_date:
        for project in projects:
            for task in project.tasks:
                if task.deadline and task.deadline.date() == selected_date:
                    if selected_date not in task_deadlines:
                        task_deadlines[selected_date] = []
                    task_deadlines[selected_date].append({
                        'id': task.id,
                        'name': task.name,
                        'description': task.description,
                        'project_name': project.name,
                        'deadline': task.deadline
                    })

    return render_template('index.html',
                           projects=projects,
                           current_date=current_date,
                           calendar_days=calendar_days,
                           first_day_weekday=first_day_weekday,
                           selected_date=selected_date,
                           task_deadlines=task_deadlines)


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    try:
        """Функция страницы аккаунта"""
        if request.method == 'POST':
            db_sess = db_session.create_session()
            user = db_sess.get(User, current_user.id)

            if user:
                user.name = request.form['name']
                user.email = request.form['email']
                user.about = request.form['about']
                user.telegram = request.form['telegram']

                if request.form['password']:
                    user.set_password(request.form['password'])

                db_sess.commit()
                flash('Изменения успешно сохранены!', 'success')
                return redirect(url_for('account'))

        return render_template('account.html')
    except:
        login()




@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    """функция страница проектов"""
    db_sess = db_session.create_session()
    if request.method == 'POST':
        if 'name' in request.form:  # Добавление нового проекта
            project = Project(
                name=request.form['name'],
                description=request.form['description'],
                user_id=current_user.id
            )
            db_sess.add(project)
            db_sess.commit()
            flash('Проект успешно создан!', 'success')
            # отправка в телеграм
            telegram(current_user.telegram, f"Создан новый проект: {request.form['name']}")
            return redirect(url_for('projects'))

        elif 'task_name' in request.form:  # Добавление новой задачи
            project_id = request.form['project_id']
            project = db_sess.get(Project, project_id)
            task_name = request.form['task_name']
            if project and project.user_id == current_user.id:
                task = Task(
                    name=task_name,
                    description=request.form['task_description'],
                    project_id=project_id
                )
                if request.form['task_deadline']:
                    task.deadline = datetime.strptime(request.form['task_deadline'], '%Y-%m-%dT%H:%M')
                db_sess.add(task)
                db_sess.commit()
                # отправка в теелграм
                telegram(current_user.telegram, f"Добавлена новая задача: {task_name} с дедлайном: {task.deadline} в проект: {project.name}")
                # делаем отсылку что дедлайн закончился
                schedule_task(f'task_{task.id}', task_name, task.deadline, current_user.telegram)
                flash('Задача успешно добавлена!', 'success')
            else:
                flash('Ошибка: Проект не найден или у вас нет прав на его изменение', 'error')

            return redirect(url_for('projects'))

        elif 'toggle_task' in request.form:  # Выполнена ли задача
            task_id = request.form['toggle_task']
            task = db_sess.get(Task, task_id)
            if task and task.project.user_id == current_user.id:
                task.is_completed = not task.is_completed
                # отправка в теелграм
                telegram(current_user.telegram, f'Задача: {task.name} выполнена')
                db_sess.commit()
            else:
                flash('Ошибка: Задача не найдена или у вас нет прав на её изменение', 'error')
            return redirect(url_for('projects'))

        elif 'delete_task' in request.form:  # Удаление задания
            task_id = request.form['delete_task']
            task = db_sess.get(Task, task_id)
            if task and task.project.user_id == current_user.id:
                db_sess.delete(task)
                db_sess.commit()
                # отправка в теелграм
                cancel_task(f'task_{task_id}')
                telegram(current_user.telegram, f'Задача: {task.name} удалена!')
                flash('Задача успешно удалена!', 'success')
            else:
                flash('Ошибка: Задача не найдена или у вас нет прав на её удаление', 'error')

            return redirect(url_for('projects'))

        elif 'delete_project' in request.form:  # Удаление проекта
            project_id = request.form['delete_project']
            project = db_sess.get(Project, project_id)
            if project and project.user_id == current_user.id:
                db_sess.delete(project)
                db_sess.commit()
                telegram(current_user.telegram, f'Проект: {project.name} удален!')
                flash('Проект успешно удален!', 'success')
            else:
                flash('Ошибка: Проект не найден или у вас нет прав на его удаление', 'error')

            return redirect(url_for('projects'))

    # GET request - show projects
    projects = db_sess.query(Project).filter(Project.user_id == current_user.id).all()
    return render_template('projects.html', projects=projects)


def main():
    """основная функция"""
    # создание папки базы данных если ее нет
    if os.path.exists('db') is True:
        pass
    else:
        os.mkdir('db')
    # подключение к базе данных
    db_session.global_init("db/database.db")
    # запуск сервера
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
