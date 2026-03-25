"""Routes for the 'organization' role: expert management, proposals, favorite rubrics."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import (User, Rubric, RubricExpert,
                        OrgFavoriteRubric, ExpertProposal, DOCUMENT_STATUSES)
from app.utils import role_required, get_current_user

org_bp = Blueprint('org', __name__, url_prefix='/org')


# ── Experts ──────────────────────────────────────────────────────────────────

@org_bp.route('/experts')
@role_required('organization')
def experts():
    user = get_current_user()
    my_experts = User.query.filter_by(org_id=user.id, role='expert').all()
    all_rubrics = Rubric.query.order_by(Rubric.code).all()
    return render_template('org/experts.html',
                           my_experts=my_experts,
                           all_rubrics=all_rubrics,
                           user=user)


@org_bp.route('/experts/create', methods=['POST'])
@role_required('organization')
def create_expert():
    org = get_current_user()
    full_name    = request.form.get('full_name',    '').strip()
    email        = request.form.get('email',        '').strip()
    username     = request.form.get('username',     '').strip()
    password     = request.form.get('password',     '').strip()
    organization = request.form.get('organization', '').strip()
    position     = request.form.get('position',     '').strip()
    phone        = request.form.get('phone',        '').strip()

    if not all([full_name, email, username, password]):
        flash('Заполните все обязательные поля.', 'warning')
        return redirect(url_for('org.experts'))
    if User.query.filter_by(username=username).first():
        flash(f'Логин «{username}» уже занят.', 'danger')
        return redirect(url_for('org.experts'))
    if User.query.filter_by(email=email).first():
        flash(f'Email «{email}» уже используется.', 'danger')
        return redirect(url_for('org.experts'))

    expert = User(full_name=full_name, email=email, username=username,
                  password=password, role='expert', org_id=org.id,
                  organization=organization or org.organization,
                  position=position or None, phone=phone or None)
    db.session.add(expert)
    db.session.commit()
    flash(f'Эксперт «{full_name}» создан.', 'success')
    return redirect(url_for('org.experts'))


@org_bp.route('/experts/<int:expert_id>/toggle', methods=['POST'])
@role_required('organization')
def toggle_expert(expert_id):
    org    = get_current_user()
    expert = User.query.get_or_404(expert_id)
    if expert.org_id != org.id:
        flash('Нет доступа.', 'danger')
        return redirect(url_for('org.experts'))
    expert.is_active = not expert.is_active
    db.session.commit()
    state = 'активирован' if expert.is_active else 'деактивирован'
    flash(f'Эксперт {expert.full_name} {state}.', 'info')
    return redirect(url_for('org.experts'))


@org_bp.route('/experts/<int:expert_id>/assign-rubric', methods=['POST'])
@role_required('organization')
def assign_rubric(expert_id):
    org       = get_current_user()
    expert    = User.query.get_or_404(expert_id)
    rubric_id = request.form.get('rubric_id', '').strip()
    if expert.org_id != org.id:
        flash('Нет доступа.', 'danger')
        return redirect(url_for('org.experts'))
    if not rubric_id:
        flash('Выберите рубрику.', 'warning')
        return redirect(url_for('org.experts'))
    rid = int(rubric_id)
    if not RubricExpert.query.filter_by(rubric_id=rid, user_id=expert_id).first():
        db.session.add(RubricExpert(rubric_id=rid, user_id=expert_id))
        db.session.commit()
        flash('Рубрика назначена эксперту.', 'success')
    else:
        flash('Эксперт уже в этой рубрике.', 'warning')
    return redirect(url_for('org.experts'))


@org_bp.route('/experts/<int:expert_id>/unassign-rubric/<int:rubric_id>', methods=['POST'])
@role_required('organization')
def unassign_rubric(expert_id, rubric_id):
    org    = get_current_user()
    expert = User.query.get_or_404(expert_id)
    if expert.org_id != org.id:
        flash('Нет доступа.', 'danger')
        return redirect(url_for('org.experts'))
    re = RubricExpert.query.filter_by(rubric_id=rubric_id, user_id=expert_id).first()
    if re:
        db.session.delete(re)
        db.session.commit()
        flash('Рубрика откреплена от эксперта.', 'info')
    return redirect(url_for('org.experts'))


# ── Favorite Rubrics ──────────────────────────────────────────────────────────

@org_bp.route('/favorite-rubric/<int:rubric_id>/toggle', methods=['POST'])
@role_required('organization')
def toggle_favorite_rubric(rubric_id):
    org = get_current_user()
    existing = OrgFavoriteRubric.query.filter_by(org_id=org.id, rubric_id=rubric_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Рубрика убрана из избранных.', 'info')
    else:
        db.session.add(OrgFavoriteRubric(org_id=org.id, rubric_id=rubric_id))
        db.session.commit()
        flash('Рубрика добавлена в избранные.', 'success')
    return redirect(request.referrer or url_for('rubrics.index'))


# ── Expert Proposals ──────────────────────────────────────────────────────────

@org_bp.route('/proposals')
@role_required('organization')
def proposals():
    org = get_current_user()
    pending   = ExpertProposal.query.filter_by(org_id=org.id, is_reviewed=False)\
                                    .order_by(ExpertProposal.created_at.desc()).all()
    reviewed  = ExpertProposal.query.filter_by(org_id=org.id, is_reviewed=True)\
                                    .order_by(ExpertProposal.created_at.desc()).limit(20).all()
    return render_template('org/proposals.html',
                           pending=pending, reviewed=reviewed,
                           DOCUMENT_STATUSES=DOCUMENT_STATUSES, user=org)


@org_bp.route('/proposals/<int:proposal_id>/mark-reviewed', methods=['POST'])
@role_required('organization')
def mark_proposal_reviewed(proposal_id):
    org      = get_current_user()
    proposal = ExpertProposal.query.get_or_404(proposal_id)
    if proposal.org_id != org.id:
        flash('Нет доступа.', 'danger')
        return redirect(url_for('org.proposals'))
    proposal.is_reviewed = True
    db.session.commit()
    flash('Предложение отмечено как рассмотренное.', 'success')
    return redirect(url_for('org.proposals'))


@org_bp.route('/expert-stats/<int:expert_id>')
@role_required('organization')
def expert_stats(expert_id):
    """Simplified expert stats — visible to the expert's own organisation."""
    org    = get_current_user()
    expert = User.query.get_or_404(expert_id)
    if expert.org_id != org.id:
        flash('Нет доступа.', 'danger')
        return redirect(url_for('org.experts'))
    from app.utils_stats import compute_expert_stats
    stats = compute_expert_stats(expert)
    return render_template('stats/expert_org.html', user=org, expert=expert, stats=stats)
