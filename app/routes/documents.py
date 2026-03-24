import os
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import (User, Document, DocumentVersion, Comment, DocumentStage,
                        Rubric, Notification, DOCUMENT_STATUSES, DOCUMENT_TYPES)
from app.utils import login_required, role_required, get_current_user

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

STAGES_TEMPLATE = [
    (1, 'Черновик',     'Подготовка и оформление текста документа организацией'),
    (2, 'Публикация',   'Размещение документа на портале. Открытие доступа к комментариям от Экспертов'),
    (3, 'Согласование', 'Согласование с заинтересованными федеральными органами'),
    (4, 'Утверждение',  'Официальное утверждение и введение в действие'),
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
        title     = request.form.get('title', '').strip()
        number    = request.form.get('number', '').strip()
        rubric_id = request.form.get('rubric_id') or None
        doc_type  = request.form.get('doc_type', 'standard')
        desc      = request.form.get('description', '').strip()
        dl_str    = request.form.get('discussion_deadline', '')

        errors = []
        if not title:
            errors.append('Наименование документа обязательно.')
        if not number:
            errors.append('Обозначение / номер документа обязателен.')
        if not desc:
            errors.append('Аннотация / описание обязательны.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('documents/add.html', rubrics=rubrics,
                                   DOCUMENT_TYPES=DOCUMENT_TYPES, user=user,
                                   form_data=request.form)

        deadline = None
        if dl_str:
            try:
                deadline = date.fromisoformat(dl_str)
            except ValueError:
                pass

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

        # Optional file upload at creation time
        file = request.files.get('file')
        if file and file.filename and _allowed_file(file.filename):
            version_number = request.form.get('version_number', '1.0').strip() or '1.0'
            filename  = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(doc.id))
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)
            db.session.add(DocumentVersion(
                document_id=doc.id, version_number=version_number,
                file_name=filename, file_path=f'uploads/{doc.id}/{filename}',
                file_size=os.path.getsize(save_path), uploaded_by=user.id,
            ))

        db.session.commit()
        flash('Документ создан как черновик.', 'success')
        return redirect(url_for('documents.detail', doc_id=doc.id))

    return render_template('documents/add.html', rubrics=rubrics,
                           DOCUMENT_TYPES=DOCUMENT_TYPES, user=user, form_data={})


@documents_bp.route('/<int:doc_id>/set-status', methods=['POST'])
@login_required
def set_status(doc_id):
    user = get_current_user()
    doc  = Document.query.get_or_404(doc_id)

    if doc.author_id != user.id and user.role != 'admin':
        flash('Нет прав для изменения статуса.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    new_status = request.form.get('status')
    valid = ['draft', 'published', 'review', 'approved', 'rejected']
    if new_status not in valid:
        flash('Недопустимый статус.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    # Role-based transition rules
    admin_only = {'approved', 'rejected'}

    # Allowed org transitions: draft→published, published→review, rejected→published
    ORG_TRANSITIONS = {
        'draft':     {'published'},
        'published': {'review'},
        'rejected':  {'published'},
    }

    if new_status in admin_only and user.role != 'admin':
        flash('Утверждать и отклонять документы может только Куратор ЭС.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    if user.role == 'org':
        allowed_targets = ORG_TRANSITIONS.get(doc.status, set())
        if new_status not in allowed_targets:
            flash('Недостаточно прав или недопустимый переход статуса.', 'danger')
            return redirect(url_for('documents.detail', doc_id=doc_id))

    # Require uploaded file before publishing
    if new_status == 'published' and not doc.latest_version():
        flash('Нельзя опубликовать документ без загруженного файла. Загрузите файл в разделе «Версии».', 'warning')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    STATUS_STAGE = {
        'draft': 1, 'published': 2,
        'review': 3, 'approved': 4, 'rejected': 3,
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

    if user.role == 'org':
        flash('Организации не могут подавать замечания. Используйте ответ разработчика.', 'warning')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    ctype              = request.form.get('comment_type', 'remark')
    structural_element = request.form.get('structural_element', '').strip()
    letter_details     = request.form.get('letter_details', '').strip()
    text               = request.form.get('text', '').strip()
    proposed_text      = request.form.get('proposed_text', '').strip()
    justification      = request.form.get('justification', '').strip()

    if not text:
        flash('Текст замечания не может быть пустым.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    db.session.add(Comment(
        document_id=doc.id, user_id=user.id,
        comment_type=ctype, structural_element=structural_element or None,
        letter_details=letter_details or None, text=text,
        proposed_text=proposed_text or None, justification=justification or None,
        status='new',
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
    valid_statuses = ('new', 'accepted', 'accepted_partly', 'rejected')
    if new_status in valid_statuses:
        comment.status = new_status
        db.session.commit()
        flash('Статус замечания обновлён.', 'success')
    return redirect(url_for('documents.detail', doc_id=doc_id))


@documents_bp.route('/<int:doc_id>/comment/<int:comment_id>/response', methods=['POST'])
@role_required('admin', 'org')
def save_comment_response(doc_id, comment_id):
    comment  = Comment.query.get_or_404(comment_id)
    response = request.form.get('developer_response', '').strip()
    comment.developer_response = response or None
    db.session.commit()
    flash('Ответ разработчика сохранён.', 'success')
    return redirect(url_for('documents.detail', doc_id=doc_id))


ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route('/<int:doc_id>/upload', methods=['POST'])
@role_required('admin', 'org')
def upload_version(doc_id):
    user = get_current_user()
    doc  = Document.query.get_or_404(doc_id)

    if doc.author_id != user.id and user.role != 'admin':
        flash('Нет прав для загрузки файлов к этому документу.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    file = request.files.get('file')
    if not file or file.filename == '':
        flash('Файл не выбран.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    if not _allowed_file(file.filename):
        flash('Недопустимый тип файла. Разрешены: PDF, DOC, DOCX, XLS, XLSX, ZIP, RAR.', 'danger')
        return redirect(url_for('documents.detail', doc_id=doc_id))

    version_number = request.form.get('version_number', '').strip() or '1.0'
    note           = request.form.get('note', '').strip()

    filename  = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(doc_id))
    os.makedirs(upload_dir, exist_ok=True)

    save_path = os.path.join(upload_dir, filename)
    file.save(save_path)
    file_size = os.path.getsize(save_path)

    db.session.add(DocumentVersion(
        document_id=doc.id, version_number=version_number,
        file_name=filename, file_path=f'uploads/{doc_id}/{filename}',
        file_size=file_size, uploaded_by=user.id,
        note=note or None,
    ))
    db.session.commit()
    flash(f'Версия {version_number} успешно загружена.', 'success')
    return redirect(url_for('documents.detail', doc_id=doc_id))


@documents_bp.route('/<int:doc_id>/delete', methods=['POST'])
@role_required('admin')
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    # Delete related records
    Comment.query.filter_by(document_id=doc_id).delete()
    DocumentVersion.query.filter_by(document_id=doc_id).delete()
    DocumentStage.query.filter_by(document_id=doc_id).delete()
    Notification.query.filter(Notification.link == f'/documents/{doc_id}').delete()
    db.session.delete(doc)
    db.session.commit()
    flash(f'Документ «{doc.title[:60]}» удалён.', 'info')
    return redirect(url_for('documents.list_documents'))
