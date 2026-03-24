from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            _set_session(user)
            flash(f'Добро пожаловать, {user.full_name}!', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Неверный логин или пароль.', 'danger')

    demo_users = User.query.all()
    return render_template('auth/login.html', demo_users=demo_users)


@auth_bp.route('/demo-login/<int:user_id>')
def demo_login(user_id):
    user = User.query.get_or_404(user_id)
    _set_session(user)
    flash(f'Вы вошли как {user.full_name} ({user.role_label()})', 'success')
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('auth.login'))


def _set_session(user: User):
    session['user_id']   = user.id
    session['username']  = user.username
    session['role']      = user.role
    session['full_name'] = user.full_name
