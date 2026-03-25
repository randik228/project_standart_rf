from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Rubric, RubricExpert, Document, User, RubricProposal
from app.utils import login_required, get_current_user, role_required

rubrics_bp = Blueprint('rubrics', __name__, url_prefix='/rubrics')


@rubrics_bp.route('/')
@login_required
def index():
    user    = get_current_user()
    rubrics = Rubric.query.all()
    return render_template('rubrics/index.html', rubrics=rubrics, user=user)


@rubrics_bp.route('/propose', methods=['GET', 'POST'])
@role_required('org')
def propose_rubric():
    org = get_current_user()

    if request.method == 'GET':
        # Показываем форму; параметр next — куда вернуться после отправки
        next_url = request.args.get('next', '')
        my_proposals = RubricProposal.query.filter_by(org_id=org.id)\
                                           .order_by(RubricProposal.created_at.desc()).all()
        return render_template('rubrics/propose.html',
                               user=org, next_url=next_url,
                               my_proposals=my_proposals)

    # POST
    code        = request.form.get('code', '').strip().upper()
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    note        = request.form.get('note', '').strip()
    next_url    = request.form.get('next_url', '')

    if not code or not name:
        flash('Укажите код и наименование рубрики.', 'warning')
        return redirect(url_for('rubrics.propose_rubric', next=next_url))
    if Rubric.query.filter_by(code=code).first():
        flash(f'Рубрика с кодом «{code}» уже существует в системе.', 'warning')
        return redirect(url_for('rubrics.propose_rubric', next=next_url))
    if RubricProposal.query.filter_by(org_id=org.id, code=code, is_reviewed=False).first():
        flash(f'Вы уже отправляли запрос на рубрику «{code}» — он ещё на рассмотрении.', 'warning')
        return redirect(url_for('rubrics.propose_rubric', next=next_url))

    db.session.add(RubricProposal(
        org_id=org.id, code=code, name=name,
        description=description or None, note=note or None,
    ))
    db.session.commit()
    flash(f'Запрос на создание рубрики «{code} — {name}» отправлен администратору.', 'success')
    return redirect(next_url or url_for('rubrics.index'))


@rubrics_bp.route('/<int:rubric_id>')
@login_required
def detail(rubric_id):
    user   = get_current_user()
    rubric = Rubric.query.get_or_404(rubric_id)
    docs   = Document.query.filter_by(rubric_id=rubric_id)\
                           .order_by(Document.updated_at.desc()).all()
    experts = [re.user for re in
               RubricExpert.query.filter_by(rubric_id=rubric_id).all()]
    from app.models import DOCUMENT_STATUSES
    return render_template('rubrics/detail.html',
                           rubric=rubric, docs=docs, experts=experts,
                           DOCUMENT_STATUSES=DOCUMENT_STATUSES, user=user)
