from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User, Message
from app.utils import login_required, get_current_user

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')


@messages_bp.route('/')
@login_required
def index():
    user  = get_current_user()
    inbox = (Message.query.filter_by(receiver_id=user.id)
             .order_by(Message.created_at.desc()).all())
    sent  = (Message.query.filter_by(sender_id=user.id)
             .order_by(Message.created_at.desc()).all())
    return render_template('messages/index.html', inbox=inbox, sent=sent, user=user)


@messages_bp.route('/<int:msg_id>')
@login_required
def view(msg_id):
    user = get_current_user()
    msg  = Message.query.get_or_404(msg_id)
    if msg.receiver_id == user.id and not msg.is_read:
        msg.is_read = True
        db.session.commit()
    return render_template('messages/view.html', msg=msg, user=user)


@messages_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    user  = get_current_user()
    users = User.query.filter(User.id != user.id).order_by(User.full_name).all()

    prefill_to = request.args.get('to', '')

    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        subject     = request.form.get('subject', '').strip()
        text        = request.form.get('text', '').strip()

        if not receiver_id or not text:
            flash('Укажите получателя и текст сообщения.', 'danger')
        else:
            db.session.add(Message(
                sender_id=user.id, receiver_id=int(receiver_id),
                subject=subject or '(без темы)', text=text,
            ))
            db.session.commit()
            flash('Сообщение отправлено.', 'success')
            return redirect(url_for('messages.index'))

    return render_template('messages/compose.html',
                           users=users, user=user, prefill_to=prefill_to)
