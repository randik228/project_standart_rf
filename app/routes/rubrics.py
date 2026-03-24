from flask import Blueprint, render_template
from app.models import Rubric, RubricExpert, Document, User
from app.utils import login_required, get_current_user

rubrics_bp = Blueprint('rubrics', __name__, url_prefix='/rubrics')


@rubrics_bp.route('/')
@login_required
def index():
    user    = get_current_user()
    rubrics = Rubric.query.all()
    return render_template('rubrics/index.html', rubrics=rubrics, user=user)


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
