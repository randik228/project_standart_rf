from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import (User, Document, DocumentVersion, Comment, DocumentStage,
                        Rubric, Notification, DOCUMENT_STATUSES, DOCUMENT_TYPES)
from app.utils import login_required, role_required, get_current_user

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

STAGES_TEMPLATE = [
    (1, 'Разработка',          'Подготовка и оформление текста документа'),
    (2, 'Публикация',          'Размещение документа на портале'),
    (3, 'Открытое обсуждение', 'Сбор замечаний и предложений от экспертного сообщества'),
    (4, 'Сводка предложений',  'Систематизация и обработка поступивших замечаний'),
    (5, 'Согласование',        'Согласование с заинтересованными федеральными органами'),
    (6, 'Утверждение',         'Официальное утверждение и введение в действие'),
]


@documents_bp.route('/')
@login_required
def list_documents():
    user = get_current_user()

    q = Document.query
    status_f = request.args.get('status', '')
    rubric_f = request.args.get('rubric', '')
    type_f   = request.args.get('type', '')
    search   = request.args.get('search', '').strip()

    if status_f:
        q = q.filter(Document.status == status_f)
    if rubric_f:
        q = q.filter(Document.rubric_id == int(rubric_f))
    if type_f:
        q = q.filter(Document.doc_type == type_f)
    if search:
        q = q.filter(Document.title.ilike(f'%{search}%') |
                     Document.number.ilike(f'%{search}%'))

    documents = q.order_by(Document.updated_at.desc()).all()
    rubrics   = Rubric.query.all()

    return render_template('documents/list.html',
                           documents=documents, rubrics=rubrics,
                           DOCUMENT_STATUSES=DOCUMENT_STATUSES,
                           DOCUMENT_TYPES=DOCUMENT_TYPES,
                           status_filter=status_f, rubric_filter=rubric_f,
                           type_filter=type_f, search=search, user=user)


@documents_bp.route('/<int:doc_id>')
@login_required
def detail(doc_id):
    user = get_current_user()
    doc  = Document.query.get_or_404(doc_id)
    return render_template('documents/detail.html', doc=doc, user=user,
                           DOCUMENT_STATUSES=DOCUMENT_STATUSES,
                           DOCUMENT_TYPES=DOCUMENT_TYPES)


@documents_bp.route('/add', methods=['GET', 'POST'])
@role_required('admin', 'org')
def add():
    user    = get_current_user()
    rubrics = Rubric.query.all()

    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        number   = request.form.get('number', '').strip()
        rubric_id = request.form.get('rubric_id') or None
        doc_type  = request.form.get('doc_type', 'standard')
        desc      = request.form.get('description', '').strip()
        dl_str    = request.form.get('discussion_deadline', '')

        deadline = None
        if dl_str:
            try:
                deadline = date.fromisoformat(dl_str)
            except ValueError:
                pass

        if not title:
            flash('Название документа обязательно.', 'danger')
            return render_template('documents/add.html', rubrics=rubrics,
                                   DOCUMENT_TYPES=DOCUMENT_TYPES, user=user)

        doc = Document(title=title, number=number, rubric_id=rubric_id,
                       author_id=user.id, status='draft', doc_type=doc_type,
                       description=desc, discussion_deadline=deadline)
        db.session.add(doc)
        db.session.flush()

        for order, name, stage_desc in STAGES_TEMPLATE:
            db.session.add(DocumentStage(
                document_id=doc.id, name=name, order=order,
                status='active' if order == 1 else 'pending',
                description=stage_desc,
                date=date.today() if order == 1 else None,
            ))

        db.session.commit()
        flash('Документ создан как черновик.', 'success')
        return redirect(url_for('documents.detail', doc_id=doc.id))

    return render_template('documents/add.html', rubrics=rubrics,
                           DOCUMENT_TYPES=DOCUMENT_TYPES, user=user)


@documents_bp.route('/<int:doc_id>/set-status', methods=['POST'])
@login_required
def set_status(doc_id):
    user = get_current_user()
    doc  = Document.query.get_or_404(doc_id)

    if doc.author_id != user.id and user.role != 'admin':
        flash('Нет прав для изменения статуса.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    new_status = request.form.get('status')
    valid = ['draft', 'published', 'discussion', 'review', 'approved', 'rejected']
    if new_status not in valid:
        flash('Недопустимый статус.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    STATUS_STAGE = {
        'draft': 1, 'published': 2, 'discussion': 3,
        'review': 5, 'approved': 6, 'rejected': 3,
    }
    active_order = STATUS_STAGE.get(new_status, 1)

    for stage in doc.stages:
        if stage.order < active_order:
            stage.status = 'completed'
            if not stage.date:
                stage.date = date.today() - timedelta(days=(active_order - stage.order) * 14)
        elif stage.order == active_order:
            stage.status = 'active'
            if not stage.date:
                stage.date = date.today()
        else:
            if new_status not in ('approved', 'rejected'):
                stage.status = 'pending'
                stage.date   = None

    doc.status     = new_status
    doc.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Статус документа изменён на «{DOCUMENT_STATUSES[new_status][0]}».', 'success')
    return redirect(url_for('documents.detail', doc_id=doc_id))


@documents_bp.route('/<int:doc_id>/comment', methods=['POST'])
@login_required
def add_comment(doc_id):
    user = get_current_user()
    doc  = Document.query.get_or_404(doc_id)

    ctype   = request.form.get('comment_type', 'remark')
    section = request.form.get('section', '').strip()
    text    = request.form.get('text', '').strip()

    if not text:
        flash('Текст замечания не может быть пустым.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    db.session.add(Comment(
        document_id=doc.id, user_id=user.id,
        comment_type=ctype, section=section, text=text, status='new',
    ))

    # Уведомление автору документа
    type_labels = {'remark': 'замечание', 'proposal': 'предложение', 'question': 'вопрос'}
    db.session.add(Notification(
        user_id=doc.author_id,
        title='Новое замечание к документу',
        text=f'По документу «{doc.title[:60]}» поступило '
             f'{type_labels.get(ctype, "замечание")} от {user.full_name}',
        is_read=False, notification_type='info',
        link=f'/documents/{doc_id}',
    ))

    db.session.commit()
    flash('Ваше замечание успешно добавлено.', 'success')
    return redirect(url_for('documents.detail', doc_id=doc_id))


@documents_bp.route('/<int:doc_id>/comment/<int:comment_id>/status', methods=['POST'])
@role_required('admin', 'org')
def update_comment_status(doc_id, comment_id):
    comment    = Comment.query.get_or_404(comment_id)
    new_status = request.form.get('status')
    if new_status in ('new', 'reviewed', 'accepted', 'rejected'):
        comment.status = new_status
        db.session.commit()
        flash('Статус замечания обновлён.', 'success')
    return redirect(url_for('documents.detail', doc_id=doc_id))
