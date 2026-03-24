from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User, Document, Comment, Rubric, RubricExpert, DOCUMENT_STATUSES
from app.utils import role_required, get_current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@role_required('admin')
def users():
    admin       = get_current_user()
    my_rubric   = Rubric.query.get(admin.rubric_id) if admin.rubric_id else None

    if my_rubric:
        # Org users in this rubric
        org_in_rubric = User.query.filter_by(rubric_id=my_rubric.id, role='org').all()

        # Expert users assigned to this rubric via RubricExpert
        re_ids       = {re.user_id for re in RubricExpert.query.filter_by(rubric_id=my_rubric.id).all()}
        exp_in_rubric = User.query.filter(User.id.in_(re_ids), User.role == 'expert').all() if re_ids else []

        rubric_users = org_in_rubric + list(exp_in_rubric)

        # Platform users NOT yet in this rubric (for "add existing" section)
        rubric_user_ids = {u.id for u in rubric_users} | {admin.id}
        other_users = User.query.filter(
            User.role.in_(['org', 'expert']),
            ~User.id.in_(rubric_user_ids)
        ).order_by(User.role, User.full_name).all()
    else:
        rubric_users = []
        other_users  = User.query.filter(User.role.in_(['org', 'expert']))\
                                 .order_by(User.role, User.full_name).all()

    return render_template('admin/users.html',
                           rubric_users=rubric_users,
                           other_users=other_users,
                           my_rubric=my_rubric,
                           user=admin)


@admin_bp.route('/users/create', methods=['POST'])
@role_required('admin')
def create_user():
    admin        = get_current_user()
    full_name    = request.form.get('full_name',    '').strip()
    email        = request.form.get('email',        '').strip()
    username     = request.form.get('username',     '').strip()
    password     = request.form.get('password',     '').strip()
    role         = request.form.get('role',         '').strip()
    organization = request.form.get('organization', '').strip()
    position     = request.form.get('position',     '').strip()
    phone        = request.form.get('phone',        '').strip()

    if not all([full_name, email, username, password, role]):
        flash('Заполните все обязательные поля.', 'warning')
        return redirect(url_for('admin.users'))
    if role not in ('org', 'expert'):
        flash('Недопустимая роль.', 'warning')
        return redirect(url_for('admin.users'))
    if User.query.filter_by(username=username).first():
        flash(f'Логин «{username}» уже занят.', 'danger')
        return redirect(url_for('admin.users'))
    if User.query.filter_by(email=email).first():
        flash(f'Email «{email}» уже используется.', 'danger')
        return redirect(url_for('admin.users'))

    # For org: store rubric_id directly; for expert: create RubricExpert entry
    new_rubric_id = admin.rubric_id if role == 'org' else None
    new_user = User(full_name=full_name, email=email, username=username,
                    password=password, role=role,
                    organization=organization or None, position=position or None,
                    phone=phone or None,
                    rubric_id=new_rubric_id)
    db.session.add(new_user)
    db.session.flush()   # get new_user.id

    if role == 'expert' and admin.rubric_id:
        db.session.add(RubricExpert(rubric_id=admin.rubric_id, user_id=new_user.id))

    db.session.commit()
    rubric_name = Rubric.query.get(admin.rubric_id).name if admin.rubric_id else '—'
    flash(f'Аккаунт «{full_name}» создан и прикреплён к рубрике «{rubric_name}».', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@role_required('admin')
def toggle_user(user_id):
    u = User.query.get_or_404(user_id)
    u.is_active = not u.is_active
    db.session.commit()
    state = 'активирован' if u.is_active else 'деактивирован'
    flash(f'Пользователь {u.full_name} {state}.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/rubric/add-user', methods=['POST'])
@role_required('admin')
def add_to_rubric():
    admin       = get_current_user()
    user_id_raw = request.form.get('user_id', '').strip()

    if not admin.rubric_id:
        flash('У вас не назначена рубрика. Обратитесь к администратору системы.', 'danger')
        return redirect(url_for('admin.users'))
    if not user_id_raw:
        flash('Выберите пользователя из списка.', 'warning')
        return redirect(url_for('admin.users'))

    target = User.query.get_or_404(int(user_id_raw))

    if target.role == 'org':
        target.rubric_id = admin.rubric_id
        db.session.commit()
        flash(f'Организация «{target.full_name}» прикреплена к рубрике.', 'success')
    elif target.role == 'expert':
        exists = RubricExpert.query.filter_by(rubric_id=admin.rubric_id, user_id=target.id).first()
        if exists:
            flash('Этот эксперт уже в вашей рубрике.', 'warning')
        else:
            db.session.add(RubricExpert(rubric_id=admin.rubric_id, user_id=target.id))
            db.session.commit()
            flash(f'Эксперт «{target.full_name}» прикреплён к рубрике.', 'success')
    else:
        flash('Нельзя добавить пользователя с этой ролью.', 'warning')

    return redirect(url_for('admin.users'))


@admin_bp.route('/rubric/remove-user/<int:target_id>', methods=['POST'])
@role_required('admin')
def remove_from_rubric(target_id):
    admin  = get_current_user()
    target = User.query.get_or_404(target_id)

    if target.role == 'org' and target.rubric_id == admin.rubric_id:
        target.rubric_id = None
        db.session.commit()
        flash(f'Организация «{target.full_name}» откреплена от рубрики.', 'info')
    elif target.role == 'expert':
        re = RubricExpert.query.filter_by(rubric_id=admin.rubric_id, user_id=target.id).first()
        if re:
            db.session.delete(re)
            db.session.commit()
            flash(f'Эксперт «{target.full_name}» откреплён от рубрики.', 'info')
    else:
        flash('Пользователь не привязан к вашей рубрике.', 'warning')

    return redirect(url_for('admin.users'))


# ── Legacy rubric management (kept for internal use, not linked in sidebar) ──

@admin_bp.route('/rubrics')
@role_required('admin')
def rubrics():
    user        = get_current_user()
    all_rubrics = Rubric.query.all()
    experts     = User.query.filter_by(role='expert').all()
    assignments = {re.user_id: re.rubric_id
                   for re in RubricExpert.query.all()}
    return render_template('admin/rubrics.html',
                           rubrics=all_rubrics, experts=experts,
                           assignments=assignments, user=user)


@admin_bp.route('/rubrics/assign', methods=['POST'])
@role_required('admin')
def assign_expert():
    rubric_id_raw = request.form.get('rubric_id', '').strip()
    user_id_raw   = request.form.get('user_id',   '').strip()
    if not user_id_raw:
        flash('Выберите эксперта из списка.', 'warning')
        return redirect(url_for('admin.rubrics'))
    rubric_id = int(rubric_id_raw)
    user_id   = int(user_id_raw)
    if not RubricExpert.query.filter_by(rubric_id=rubric_id, user_id=user_id).first():
        db.session.add(RubricExpert(rubric_id=rubric_id, user_id=user_id))
        db.session.commit()
        flash('Эксперт назначен на рубрику.', 'success')
    else:
        flash('Эксперт уже назначен на эту рубрику.', 'warning')
    return redirect(url_for('admin.rubrics'))


@admin_bp.route('/rubrics/unassign/<int:re_id>', methods=['POST'])
@role_required('admin')
def unassign_expert(re_id):
    re = RubricExpert.query.get_or_404(re_id)
    db.session.delete(re)
    db.session.commit()
    flash('Эксперт удалён из рубрики.', 'info')
    return redirect(url_for('admin.rubrics'))


@admin_bp.route('/monitoring')
@role_required('admin')
def monitoring():
    user = get_current_user()

    docs_stats = []
    for doc in Document.query.order_by(Document.updated_at.desc()).all():
        docs_stats.append({
            'doc':              doc,
            'total_comments':   Comment.query.filter_by(document_id=doc.id).count(),
            'new_comments':     Comment.query.filter_by(document_id=doc.id, status='new').count(),
            'accepted_comments': Comment.query.filter_by(document_id=doc.id, status='accepted').count(),
        })

    status_counts   = {k: Document.query.filter_by(status=k).count()
                       for k in DOCUMENT_STATUSES}
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(10).all()
    total_users     = User.query.count()
    total_experts   = User.query.filter_by(role='expert').count()
    total_orgs      = User.query.filter_by(role='org').count()

    return render_template('admin/monitoring.html',
                           docs_stats=docs_stats,
                           status_counts=status_counts,
                           recent_comments=recent_comments,
                           DOCUMENT_STATUSES=DOCUMENT_STATUSES,
                           total_users=total_users,
                           total_experts=total_experts,
                           total_orgs=total_orgs,
                           user=user)
