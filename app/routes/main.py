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

    if user.role == 'admin':
        rid = user.rubric_id
        if rid:
            doc_q = Document.query.filter(Document.rubric_id == rid)

            total_docs      = doc_q.count()
            discussion_docs = doc_q.filter(Document.status == 'published').count()
            new_comments    = (Comment.query
                               .join(Document, Comment.document_id == Document.id)
                               .filter(Document.rubric_id == rid, Comment.status == 'new')
                               .count())
            total_experts   = RubricExpert.query.filter_by(rubric_id=rid).count()
            recent_docs     = (Document.query.filter(Document.rubric_id == rid)
                               .order_by(Document.updated_at.desc()).limit(6).all())
            recent_comments = (Comment.query
                               .join(Document, Comment.document_id == Document.id)
                               .filter(Document.rubric_id == rid)
                               .order_by(Comment.created_at.desc()).limit(5).all())
            status_counts   = {k: Document.query.filter(Document.rubric_id == rid,
                                                         Document.status == k).count()
                               for k in DOCUMENT_STATUSES}
        else:
            total_docs = discussion_docs = new_comments = total_experts = 0
            recent_docs = recent_comments = []
            status_counts = {k: 0 for k in DOCUMENT_STATUSES}

        return render_template('dashboard/admin.html',
                               user=user,
                               total_docs=total_docs, discussion_docs=discussion_docs,
                               new_comments=new_comments, total_experts=total_experts,
                               recent_docs=recent_docs, recent_comments=recent_comments,
                               status_counts=status_counts, DOCUMENT_STATUSES=DOCUMENT_STATUSES)

    elif user.role == 'org':
        my_docs = Document.query.filter_by(author_id=user.id)\
                                .order_by(Document.updated_at.desc()).all()
        total_docs      = len(my_docs)
        discussion_docs = sum(1 for d in my_docs if d.status == 'published')
        new_comments    = Comment.query.join(Document, Comment.document_id == Document.id)\
                                       .filter(Document.author_id == user.id,
                                               Comment.status == 'new').count()
        status_counts   = {k: sum(1 for d in my_docs if d.status == k)
                           for k in DOCUMENT_STATUSES}
        return render_template('dashboard/org.html',
                               user=user, my_docs=my_docs,
                               total_docs=total_docs, discussion_docs=discussion_docs,
                               new_comments=new_comments, total_experts=0,
                               recent_docs=my_docs[:6], recent_comments=[],
                               status_counts=status_counts, DOCUMENT_STATUSES=DOCUMENT_STATUSES)

    else:  # expert
        rubric_ids = [re.rubric_id for re in
                      RubricExpert.query.filter_by(user_id=user.id).all()]
        my_docs = Document.query.filter(
            Document.rubric_id.in_(rubric_ids),
            Document.status.in_(['published', 'review'])
        ).order_by(Document.updated_at.desc()).all()
        my_comments = Comment.query.filter_by(user_id=user.id)\
                                   .order_by(Comment.created_at.desc()).limit(5).all()
        my_rubrics  = RubricExpert.query.filter_by(user_id=user.id).all()
        total_docs      = len(my_docs)
        discussion_docs = sum(1 for d in my_docs if d.status == 'published')
        new_comments    = Comment.query.filter_by(user_id=user.id, status='new').count()
        status_counts   = {k: sum(1 for d in my_docs if d.status == k)
                           for k in DOCUMENT_STATUSES}
        return render_template('dashboard/expert.html',
                               user=user, my_docs=my_docs,
                               my_comments=my_comments, my_rubrics=my_rubrics,
                               total_docs=total_docs, discussion_docs=discussion_docs,
                               new_comments=new_comments, total_experts=0,
                               recent_docs=my_docs[:6], recent_comments=[],
                               status_counts=status_counts, DOCUMENT_STATUSES=DOCUMENT_STATUSES)
