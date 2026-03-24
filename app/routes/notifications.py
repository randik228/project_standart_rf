from flask import Blueprint, render_template, redirect, url_for, request
from app import db
from app.models import Notification
from app.utils import login_required, get_current_user

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    user  = get_current_user()
    notifs = (Notification.query
              .filter_by(user_id=user.id)
              .order_by(Notification.created_at.desc())
              .all())
    return render_template('notifications/index.html', notifications=notifs, user=user)


@notifications_bp.route('/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    user  = get_current_user()
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id == user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(request.referrer or url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('notifications.index'))
