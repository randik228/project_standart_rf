from flask import Blueprint, render_template, redirect, url_for, abort
from app.models import User, Document, Comment, Notification, RubricExpert, DOCUMENT_STATUSES, RubricProposal
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
        total_docs      = Document.query.count()
        discussion_docs = Document.query.filter_by(status='published').count()
        new_comments    = Comment.query.filter_by(status='new').count()
        total_experts   = User.query.filter_by(role='expert').count()
        total_orgs      = User.query.filter(User.role.in_(['org', 'organization'])).count()
        recent_docs     = Document.query.order_by(Document.updated_at.desc()).limit(6).all()
        recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
        status_counts   = {k: Document.query.filter_by(status=k).count() for k in DOCUMENT_STATUSES}
        pending_rubric_proposals = RubricProposal.query.filter_by(is_reviewed=False).count()

        return render_template('dashboard/admin.html',
                               user=user,
                               total_docs=total_docs, discussion_docs=discussion_docs,
                               new_comments=new_comments, total_experts=total_experts,
                               total_orgs=total_orgs,
                               recent_docs=recent_docs, recent_comments=recent_comments,
                               status_counts=status_counts, DOCUMENT_STATUSES=DOCUMENT_STATUSES,
                               pending_rubric_proposals=pending_rubric_proposals)

    elif user.role == 'organization':
        from app.models import OrgFavoriteDocument, OrgFavoriteRubric, ExpertProposal
        fav_doc_ids    = {f.document_id for f in OrgFavoriteDocument.query.filter_by(org_id=user.id).all()}
        fav_rubric_ids = {f.rubric_id   for f in OrgFavoriteRubric.query.filter_by(org_id=user.id).all()}
        my_experts     = User.query.filter_by(org_id=user.id, role='expert').all()
        pending_proposals = ExpertProposal.query.filter_by(org_id=user.id, is_reviewed=False)\
                                                .order_by(ExpertProposal.created_at.desc()).limit(5).all()
        recent_fav_docs = (Document.query
                           .filter(Document.id.in_(fav_doc_ids),
                                   Document.status.in_(['published', 'review', 'approved']))
                           .order_by(Document.updated_at.desc()).limit(6).all()
                           if fav_doc_ids else [])
        return render_template('dashboard/organization.html',
                               user=user,
                               my_experts=my_experts,
                               pending_proposals=pending_proposals,
                               fav_doc_ids=fav_doc_ids,
                               fav_rubric_ids=fav_rubric_ids,
                               recent_fav_docs=recent_fav_docs,
                               total_docs=len(fav_doc_ids),
                               DOCUMENT_STATUSES=DOCUMENT_STATUSES)

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
        from app.models import OrgFavoriteDocument
        rubric_ids = [re.rubric_id for re in
                      RubricExpert.query.filter_by(user_id=user.id).all()]
        all_docs = Document.query.filter(
            Document.rubric_id.in_(rubric_ids),
            Document.status.in_(['published', 'review'])
        ).order_by(Document.updated_at.desc()).all() if rubric_ids else []

        # Priority: org-favorites first
        if user.org_id:
            fav_doc_ids = {f.document_id for f in
                           OrgFavoriteDocument.query.filter_by(org_id=user.org_id).all()}
            my_docs = sorted(all_docs,
                             key=lambda d: (0 if d.id in fav_doc_ids else 1, -d.updated_at.timestamp()))
        else:
            fav_doc_ids = set()
            my_docs = all_docs

        my_comments = Comment.query.filter_by(user_id=user.id)\
                                   .order_by(Comment.created_at.desc()).limit(5).all()
        my_rubrics  = RubricExpert.query.filter_by(user_id=user.id).all()
        from app.utils_stats import compute_expert_stats
        stats = compute_expert_stats(user)
        return render_template('dashboard/expert.html',
                               user=user, my_docs=my_docs, fav_doc_ids=fav_doc_ids,
                               my_comments=my_comments, my_rubrics=my_rubrics,
                               total_docs=len(my_docs),
                               discussion_docs=sum(1 for d in my_docs if d.status == 'published'),
                               new_comments=Comment.query.filter_by(user_id=user.id, status='new').count(),
                               total_experts=0,
                               recent_docs=my_docs[:6], recent_comments=[],
                               status_counts={k: 0 for k in DOCUMENT_STATUSES},
                               DOCUMENT_STATUSES=DOCUMENT_STATUSES,
                               stats=stats)


@main_bp.route('/stats')
@login_required
def expert_stats():
    """Full statistics page — accessible only by the expert themselves."""
    user = get_current_user()
    if user.role != 'expert':
        abort(403)
    from app.utils_stats import compute_expert_stats
    stats = compute_expert_stats(user)
    return render_template('stats/expert_full.html', user=user, stats=stats)
