from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User, Document, Comment, Rubric, RubricExpert, DOCUMENT_STATUSES, RubricProposal
from app.utils import role_required, get_current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@role_required('admin')
def users():
    admin       = get_current_user()
    all_rubrics = Rubric.query.order_by(Rubric.code).all()
    all_users   = User.query.filter(User.role.in_(['org', 'organization', 'expert']))\
                            .order_by(User.role, User.full_name).all()
    orgs        = [u for u in all_users if u.role in ('org', 'organization')]
    experts     = [u for u in all_users if u.role == 'expert']

    return render_template('admin/users.html',
                           all_users=all_users,
                           orgs=orgs,
                           experts=experts,
                           all_rubrics=all_rubrics,
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
    if role not in ('org', 'organization', 'expert', 'admin'):
        flash('Недопустимая роль.', 'warning')
        return redirect(url_for('admin.users'))
    if User.query.filter_by(username=username).first():
        flash(f'Логин «{username}» уже занят.', 'danger')
        return redirect(url_for('admin.users'))
    if User.query.filter_by(email=email).first():
        flash(f'Email «{email}» уже используется.', 'danger')
        return redirect(url_for('admin.users'))

    new_user = User(full_name=full_name, email=email, username=username,
                    password=password, role=role,
                    organization=organization or None, position=position or None,
                    phone=phone or None)
    db.session.add(new_user)
    db.session.commit()
    flash(f'Аккаунт «{full_name}» создан.', 'success')
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
    user_id_raw = request.form.get('user_id',  '').strip()
    rubric_id_raw = request.form.get('rubric_id', '').strip()

    if not user_id_raw:
        flash('Выберите пользователя из списка.', 'warning')
        return redirect(url_for('admin.users'))
    if not rubric_id_raw:
        flash('Выберите рубрику.', 'warning')
        return redirect(url_for('admin.users'))

    target    = User.query.get_or_404(int(user_id_raw))
    rubric_id = int(rubric_id_raw)

    if target.role == 'org':
        target.rubric_id = rubric_id
        db.session.commit()
        flash(f'Организация «{target.full_name}» прикреплена к рубрике.', 'success')
    elif target.role == 'expert':
        exists = RubricExpert.query.filter_by(rubric_id=rubric_id, user_id=target.id).first()
        if exists:
            flash('Этот эксперт уже назначен на эту рубрику.', 'warning')
        else:
            db.session.add(RubricExpert(rubric_id=rubric_id, user_id=target.id))
            db.session.commit()
            flash(f'Эксперт «{target.full_name}» прикреплён к рубрике.', 'success')
    else:
        flash('Нельзя добавить пользователя с этой ролью.', 'warning')

    return redirect(url_for('admin.users'))


@admin_bp.route('/rubric/remove-user/<int:target_id>', methods=['POST'])
@role_required('admin')
def remove_from_rubric(target_id):
    target = User.query.get_or_404(target_id)

    if target.role == 'org' and target.rubric_id:
        target.rubric_id = None
        db.session.commit()
        flash(f'Организация «{target.full_name}» откреплена от рубрики.', 'info')
    elif target.role == 'expert':
        rubric_id_raw = request.form.get('rubric_id', '').strip()
        q = RubricExpert.query.filter_by(user_id=target.id)
        if rubric_id_raw:
            q = q.filter_by(rubric_id=int(rubric_id_raw))
        re_row = q.first()
        if re_row:
            db.session.delete(re_row)
            db.session.commit()
            flash(f'Эксперт «{target.full_name}» откреплён от рубрики.', 'info')
        else:
            flash('Назначение не найдено.', 'warning')
    else:
        flash('Пользователь не привязан ни к одной рубрике.', 'warning')

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

    all_docs = Document.query.order_by(Document.updated_at.desc()).all()

    docs_stats = []
    for doc in all_docs:
        docs_stats.append({
            'doc':               doc,
            'total_comments':    Comment.query.filter_by(document_id=doc.id).count(),
            'new_comments':      Comment.query.filter_by(document_id=doc.id, status='new').count(),
            'accepted_comments': Comment.query.filter_by(document_id=doc.id, status='accepted').count(),
        })

    doc_ids = [d.id for d in all_docs]
    status_counts   = {k: sum(1 for d in all_docs if d.status == k) for k in DOCUMENT_STATUSES}
    recent_comments = (Comment.query
                       .filter(Comment.document_id.in_(doc_ids))
                       .order_by(Comment.created_at.desc()).limit(10).all()
                       if doc_ids else [])

    total_experts = User.query.filter_by(role='expert').count()
    total_orgs    = User.query.filter(User.role.in_(['org', 'organization'])).count()
    total_users   = total_experts + total_orgs

    return render_template('admin/monitoring.html',
                           docs_stats=docs_stats,
                           status_counts=status_counts,
                           recent_comments=recent_comments,
                           DOCUMENT_STATUSES=DOCUMENT_STATUSES,
                           total_users=total_users,
                           total_experts=total_experts,
                           total_orgs=total_orgs,
                           user=user)


# ── Rubric Proposals ─────────────────────────────────────────────────────────

@admin_bp.route('/rubric-proposals')
@role_required('admin')
def rubric_proposals():
    pending  = RubricProposal.query.filter_by(is_reviewed=False)\
                                   .order_by(RubricProposal.created_at.desc()).all()
    reviewed = RubricProposal.query.filter_by(is_reviewed=True)\
                                   .order_by(RubricProposal.created_at.desc()).limit(20).all()
    return render_template('admin/rubric_proposals.html',
                           pending=pending, reviewed=reviewed, user=get_current_user())


@admin_bp.route('/rubrics/create-direct', methods=['POST'])
@role_required('admin')
def create_rubric_direct():
    code        = request.form.get('code',        '').strip().upper()
    name        = request.form.get('name',        '').strip()
    description = request.form.get('description', '').strip()
    if not code or not name:
        flash('Код и название обязательны.', 'warning')
        return redirect(url_for('admin.rubric_proposals'))
    if Rubric.query.filter_by(code=code).first():
        flash(f'Рубрика с кодом «{code}» уже существует.', 'danger')
        return redirect(url_for('admin.rubric_proposals'))
    db.session.add(Rubric(code=code, name=name, description=description or None))
    db.session.commit()
    flash(f'Рубрика «{code} — {name}» успешно создана.', 'success')
    return redirect(url_for('admin.rubric_proposals'))


@admin_bp.route('/rubric-proposals/<int:proposal_id>/approve', methods=['POST'])
@role_required('admin')
def approve_rubric_proposal(proposal_id):
    proposal = RubricProposal.query.get_or_404(proposal_id)
    if not Rubric.query.filter_by(code=proposal.code).first():
        db.session.add(Rubric(code=proposal.code, name=proposal.name,
                              description=proposal.description or ''))
    proposal.is_reviewed = True
    proposal.is_approved = True
    db.session.commit()
    flash(f'Рубрика «{proposal.code} — {proposal.name}» создана.', 'success')
    return redirect(url_for('admin.rubric_proposals'))


@admin_bp.route('/rubric-proposals/<int:proposal_id>/reject', methods=['POST'])
@role_required('admin')
def reject_rubric_proposal(proposal_id):
    proposal = RubricProposal.query.get_or_404(proposal_id)
    proposal.is_reviewed = True
    proposal.is_approved = False
    db.session.commit()
    flash('Предложение по добавлению рубрики отклонено.', 'info')
    return redirect(url_for('admin.rubric_proposals'))
