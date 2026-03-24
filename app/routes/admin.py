from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User, Document, Comment, Rubric, RubricExpert, DOCUMENT_STATUSES
from app.utils import role_required, get_current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@role_required('admin')
def users():
    user      = get_current_user()
    all_users = User.query.order_by(User.role, User.full_name).all()
    return render_template('admin/users.html', users=all_users, user=user)


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
    exists = RubricExpert.query.filter_by(rubric_id=rubric_id, user_id=user_id).first()
    if not exists:
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
