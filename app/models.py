from datetime import datetime
from app import db


DOCUMENT_STATUSES = {
    'draft':     ('Черновик',          'secondary', 'pencil'),
    'published': ('Публикация',        'primary',   'upload'),
    'review':    ('Загрузка версии',   'info',      'cloud-upload'),
    'approved':  ('Утверждён',         'success',   'check-circle-fill'),
    'rejected':  ('Отклонён',          'danger',    'x-circle-fill'),
}

DOCUMENT_TYPES = {
    'standard':   'Стандарт (ГОСТ Р)',
    'normative':  'Нормативно-правовой',
    'methodical': 'Методический',
    'technical':  'Нормативно-технический',
}

COMMENT_TYPES = {
    'remark':   ('Замечание',   'danger'),
    'proposal': ('Предложение', 'primary'),
    'question': ('Вопрос',      'info'),
}

COMMENT_STATUSES = {
    'new':             ('Новое',            'secondary'),
    'accepted':        ('Принято',          'success'),
    'accepted_partly': ('Принято частично', 'primary'),
    'rejected':        ('Отклонено',        'danger'),
}


class User(db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False, default='demo123')
    role         = db.Column(db.String(20), nullable=False)   # admin | org | expert
    full_name    = db.Column(db.String(200))
    organization = db.Column(db.String(300))
    position     = db.Column(db.String(200))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    phone        = db.Column(db.String(20))
    is_active    = db.Column(db.Boolean, default=True)
    org_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # For admin: rubric they manage; for org: rubric they belong to
    rubric_id    = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=True)

    documents     = db.relationship('Document', backref='author', lazy=True,
                                    foreign_keys='Document.author_id')
    comments      = db.relationship('Comment', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def get_initials(self):
        if self.full_name:
            parts = self.full_name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            return self.full_name[:2].upper()
        return self.username[:2].upper()

    def role_label(self):
        return {'admin': 'Сис. администратор', 'org': 'Разработчик', 'organization': 'Организация', 'expert': 'Эксперт'}.get(self.role, self.role)

    def unread_notifications(self):
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def unread_messages(self):
        return Message.query.filter_by(receiver_id=self.id, is_read=False).count()


class Rubric(db.Model):
    __tablename__ = 'rubrics'

    id          = db.Column(db.Integer, primary_key=True)
    code        = db.Column(db.String(20), unique=True, nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship('Document', backref='rubric', lazy=True)

    def expert_count(self):
        return RubricExpert.query.filter_by(rubric_id=self.id).count()

    def document_count(self):
        return Document.query.filter_by(rubric_id=self.id).count()


class Document(db.Model):
    __tablename__ = 'documents'

    id                  = db.Column(db.Integer, primary_key=True)
    title               = db.Column(db.String(500), nullable=False)
    number              = db.Column(db.String(100))
    rubric_id           = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=True)
    author_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status              = db.Column(db.String(30), default='draft')
    doc_type            = db.Column(db.String(50), default='standard')
    description         = db.Column(db.Text)
    discussion_deadline = db.Column(db.Date)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = db.relationship('DocumentVersion', backref='document', lazy=True,
                               order_by='DocumentVersion.uploaded_at.desc()')
    comments = db.relationship('Comment', backref='document', lazy=True,
                               order_by='Comment.created_at.desc()')
    stages   = db.relationship('DocumentStage', backref='document', lazy=True,
                               order_by='DocumentStage.order')

    def status_info(self):
        return DOCUMENT_STATUSES.get(self.status, ('Неизвестно', 'secondary'))

    def type_label(self):
        return DOCUMENT_TYPES.get(self.doc_type, self.doc_type)

    def comments_count(self):
        return Comment.query.filter_by(document_id=self.id).count()

    def new_comments_count(self):
        return Comment.query.filter_by(document_id=self.id, status='new').count()

    def latest_version(self):
        return DocumentVersion.query.filter_by(document_id=self.id)\
                                    .order_by(DocumentVersion.uploaded_at.desc()).first()


class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'

    id             = db.Column(db.Integer, primary_key=True)
    document_id    = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    version_number = db.Column(db.String(20), default='1.0')
    file_name      = db.Column(db.String(300))
    file_path      = db.Column(db.String(500))
    file_size      = db.Column(db.Integer, default=0)
    uploaded_by    = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at    = db.Column(db.DateTime, default=datetime.utcnow)
    note           = db.Column(db.Text)

    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def file_size_kb(self):
        return round(self.file_size / 1024) if self.file_size else 0


class Comment(db.Model):
    __tablename__ = 'comments'

    id                 = db.Column(db.Integer, primary_key=True)
    document_id        = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id            = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_type       = db.Column(db.String(20), default='remark')  # remark | proposal | question
    structural_element = db.Column(db.String(200))   # структурный элемент (раздел, пункт)
    letter_details     = db.Column(db.String(300))   # номер и дата письма организации
    text               = db.Column(db.Text, nullable=False)   # замечание / предложение
    proposed_text      = db.Column(db.Text)          # предлагаемая редакция
    justification      = db.Column(db.Text)          # обоснование
    developer_response = db.Column(db.Text)          # ответ разработчика
    response_at        = db.Column(db.DateTime, nullable=True)  # дата и время ответа разработчика
    status             = db.Column(db.String(20), default='new')
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    def type_info(self):
        return COMMENT_TYPES.get(self.comment_type, (self.comment_type, 'secondary'))

    def status_info(self):
        return COMMENT_STATUSES.get(self.status, (self.status, 'secondary'))


class DocumentStage(db.Model):
    __tablename__ = 'document_stages'

    id          = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    order       = db.Column(db.Integer, default=0)
    status      = db.Column(db.String(20), default='pending')  # pending | active | completed
    date        = db.Column(db.Date)
    description = db.Column(db.Text)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title             = db.Column(db.String(300), nullable=False)
    text              = db.Column(db.Text)
    is_read           = db.Column(db.Boolean, default=False)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    link              = db.Column(db.String(300))
    notification_type = db.Column(db.String(30), default='info')  # info | warning | success | danger


class Message(db.Model):
    __tablename__ = 'messages'

    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject     = db.Column(db.String(300))
    text        = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    sender   = db.relationship('User', foreign_keys=[sender_id],   backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


class RubricExpert(db.Model):
    __tablename__ = 'rubric_experts'

    id          = db.Column(db.Integer, primary_key=True)
    rubric_id   = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    rubric = db.relationship('Rubric', backref='expert_assignments')
    user   = db.relationship('User', backref='rubric_assignments')


class OrgFavoriteRubric(db.Model):
    """Рубрики, интересные Организации."""
    __tablename__ = 'org_favorite_rubrics'
    id        = db.Column(db.Integer, primary_key=True)
    org_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rubric = db.relationship('Rubric', backref='org_favorites')

class OrgFavoriteDocument(db.Model):
    """Документы, отмеченные Организацией как интересные."""
    __tablename__ = 'org_favorite_documents'
    id          = db.Column(db.Integer, primary_key=True)
    org_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class ExpertProposal(db.Model):
    """Эксперт предлагает документ на рассмотрение своей Организации."""
    __tablename__ = 'expert_proposals'
    id          = db.Column(db.Integer, primary_key=True)
    expert_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    org_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    note        = db.Column(db.Text)
    is_reviewed = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    expert   = db.relationship('User', foreign_keys=[expert_id], backref='sent_proposals')
    document = db.relationship('Document', backref='expert_proposals')


class RubricProposal(db.Model):
    """Разработчик предлагает добавить новую рубрику (на рассмотрение сис. администратора)."""
    __tablename__ = 'rubric_proposals'
    id          = db.Column(db.Integer, primary_key=True)
    org_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code        = db.Column(db.String(20), nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    note        = db.Column(db.Text)
    is_reviewed = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    org         = db.relationship('User', foreign_keys=[org_id], backref='rubric_proposals')
