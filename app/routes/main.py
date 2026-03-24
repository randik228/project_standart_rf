from flask import Blueprint, render_template, redirect, url_for
from app.models import User, Document, Comment, Notification, RubricExpert, DOCUMENT_STATUSES
from app.utils import login_required, get_current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()

    # Общая статистика
    total_docs       = Document.query.count()
    discussion_docs  = Document.query.filter_by(status='discussion').count()
    new_comments     = Comment.query.filter_by(status='new').count()
    total_experts    = User.query.filter_by(role='expert').count()
    recent_docs      = Document.query.order_by(Document.updated_at.desc()).limit(6).all()
    recent_comments  = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()

    status_counts = {k: Document.query.filter_by(status=k).count()
                     for k in DOCUMENT_STATUSES}

    ctx = dict(
        user=user,
        total_docs=total_docs, discussion_docs=discussion_docs,
        new_comments=new_comments, total_experts=total_experts,
        recent_docs=recent_docs, recent_comments=recent_comments,
        status_counts=status_counts, DOCUMENT_STATUSES=DOCUMENT_STATUSES,
    )

    if user.role == 'admin':
        return render_template('dashboard/admin.html', **ctx)

    elif user.role == 'org':
        my_docs = Document.query.filter_by(author_id=user.id)\
                                .order_by(Document.updated_at.desc()).all()
        ctx['my_docs'] = my_docs
        return render_template('dashboard/org.html', **ctx)

    else:  # expert
        rubric_ids = [re.rubric_id for re in
                      RubricExpert.query.filter_by(user_id=user.id).all()]
        my_docs = Document.query.filter(
            Document.rubric_id.in_(rubric_ids),
            Document.status.in_(['discussion', 'review', 'published'])
        ).order_by(Document.updated_at.desc()).all()
        my_comments = Comment.query.filter_by(user_id=user.id)\
                                   .order_by(Comment.created_at.desc()).limit(5).all()
        my_rubrics  = RubricExpert.query.filter_by(user_id=user.id).all()
        ctx.update(my_docs=my_docs, my_comments=my_comments, my_rubrics=my_rubrics)
        return render_template('dashboard/expert.html', **ctx)
