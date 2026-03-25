"""Expert statistics computation — no DB changes needed, computed from Comment data."""
from collections import defaultdict
from datetime import datetime


# ── Level definitions ──────────────────────────────────────────────────────────
LEVELS = [
    (0,  30,  'Специалист',      'secondary', 'person'),
    (30, 50,  'Эксперт',         'primary',   'person-badge'),
    (50, 70,  'Ведущий эксперт', 'success',   'person-check-fill'),
    (70, 101, 'Топ-эксперт',     'warning',   'trophy-fill'),
]

# ── Badge definitions ──────────────────────────────────────────────────────────
BADGE_DEFS = [
    ('quality_master',  'Мастер качества',    'patch-check-fill',       'warning', 'Качество правок ≥ 80%'),
    ('speed_demon',     'Оперативность',       'lightning-charge-fill',  'info',    'Эффективность ≥ 80%'),
    ('prolific',        'Высокая активность',  'chat-square-text-fill',  'primary', '10 и более замечаний'),
    ('veteran',         'Опытный эксперт',     'award-fill',             'success', 'Комментировал 5+ документов'),
    ('standard_master', 'Специалист по ГОСТ',  'journal-bookmark-fill',  'danger',  'Работа со стандартами ГОСТ Р'),
    ('consistent',      'Всегда в срок',       'graph-up',               'success', 'Эффективность ≥ 90%'),
]

DOC_TYPE_WEIGHT = {
    'standard':   1.5,
    'normative':  1.3,
    'technical':  1.2,
    'methodical': 1.1,
}

MONTH_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
               'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']


def compute_expert_stats(expert):
    """Return a dict of all stats for the given expert User object."""
    from app.models import Comment, Document, Rubric

    all_comments = Comment.query.filter_by(user_id=expert.id).all()
    reviewed = [c for c in all_comments
                if c.status in ('accepted', 'accepted_partly', 'rejected')]
    accepted = [c for c in reviewed if c.status == 'accepted']
    partial  = [c for c in reviewed if c.status == 'accepted_partly']
    rejected = [c for c in reviewed if c.status == 'rejected']

    # ── Quality (0–100) ────────────────────────────────────────────────────────
    if reviewed:
        quality = round((len(accepted) * 1.0 + len(partial) * 0.5) / len(reviewed) * 100, 1)
    else:
        quality = 0.0

    # ── Unique documents ───────────────────────────────────────────────────────
    doc_ids = list({c.document_id for c in all_comments})
    docs = Document.query.filter(Document.id.in_(doc_ids)).all() if doc_ids else []
    docs_by_id = {d.id: d for d in docs}

    # ── Experience (0–100) — weighted doc complexity ───────────────────────────
    exp_raw = sum(DOC_TYPE_WEIGHT.get(d.doc_type, 1.0) for d in docs)
    experience = round(min(exp_raw / 30.0 * 100, 100.0), 1)

    # ── Efficiency (0–100) — commenting before deadline ───────────────────────
    eff_scores = []
    for c in all_comments:
        doc = docs_by_id.get(c.document_id)
        if doc and doc.discussion_deadline:
            c_date = c.created_at.date() if isinstance(c.created_at, datetime) else c.created_at
            days_before = (doc.discussion_deadline - c_date).days
            if days_before >= 0:
                eff_scores.append(1.0)
            elif days_before >= -3:
                eff_scores.append(0.5)
            else:
                eff_scores.append(0.0)
        else:
            eff_scores.append(0.75)  # no deadline → neutral
    efficiency = round(sum(eff_scores) / len(eff_scores) * 100, 1) if eff_scores else 75.0

    # ── Final rating ───────────────────────────────────────────────────────────
    rating = round(quality * 0.45 + experience * 0.30 + efficiency * 0.25, 1)

    # ── Monthly trend (last 6 active months) ───────────────────────────────────
    monthly = defaultdict(lambda: {'accepted': 0, 'partial': 0, 'rejected': 0, 'total': 0})
    for c in all_comments:
        key = c.created_at.strftime('%Y-%m')
        monthly[key]['total'] += 1
        if c.status == 'accepted':
            monthly[key]['accepted'] += 1
        elif c.status == 'accepted_partly':
            monthly[key]['partial'] += 1
        elif c.status == 'rejected':
            monthly[key]['rejected'] += 1

    sorted_months = sorted(monthly.keys())[-6:]
    monthly_labels, monthly_quality, monthly_counts = [], [], []
    for m in sorted_months:
        d  = monthly[m]
        rv = d['accepted'] + d['partial'] + d['rejected']
        q  = round((d['accepted'] * 1.0 + d['partial'] * 0.5) / rv * 100, 1) if rv else 0
        yr, mo = m.split('-')
        monthly_labels.append(MONTH_NAMES[int(mo) - 1] + ' ' + yr[-2:])
        monthly_quality.append(q)
        monthly_counts.append(d['total'])

    # Trend
    if len(monthly_quality) >= 2:
        diff = monthly_quality[-1] - monthly_quality[-2]
        trend       = '↗' if diff > 2 else ('↘' if diff < -2 else '→')
        trend_label = 'рост' if diff > 2 else ('снижение' if diff < -2 else 'стабильно')
        trend_color = 'success' if diff > 2 else ('danger' if diff < -2 else 'secondary')
    else:
        trend, trend_label, trend_color = '→', 'стабильно', 'secondary'

    # ── Rubric breakdown ───────────────────────────────────────────────────────
    rubric_stats = []
    rubric_ids = list({d.rubric_id for d in docs if d.rubric_id})
    for rid in rubric_ids:
        from app.models import Rubric as _Rubric
        rubric = _Rubric.query.get(rid)
        if not rubric:
            continue
        rdoc_ids = {d.id for d in docs if d.rubric_id == rid}
        rc = [c for c in reviewed if c.document_id in rdoc_ids]
        ra = sum(1 for c in rc if c.status == 'accepted')
        rp = sum(1 for c in rc if c.status == 'accepted_partly')
        rq = round((ra + rp * 0.5) / len(rc) * 100, 1) if rc else 0
        rubric_stats.append({
            'rubric':    rubric,
            'doc_count': len(rdoc_ids),
            'quality':   rq,
            'count':     len(rc),
        })

    # ── Gamification ───────────────────────────────────────────────────────────
    level_info = _get_level(rating)
    badges     = _get_badges(quality, efficiency, len(all_comments), docs)

    return {
        # Counts
        'total_comments':   len(all_comments),
        'reviewed_count':   len(reviewed),
        'accepted_count':   len(accepted),
        'partial_count':    len(partial),
        'rejected_count':   len(rejected),
        'unique_docs_count': len(docs),
        'approved_docs_count': sum(1 for d in docs if d.status == 'approved'),
        # Scores
        'quality':    quality,
        'experience': experience,
        'efficiency': efficiency,
        'rating':     rating,
        # Trend
        'monthly_labels':  monthly_labels,
        'monthly_quality': monthly_quality,
        'monthly_counts':  monthly_counts,
        'trend':       trend,
        'trend_label': trend_label,
        'trend_color': trend_color,
        # Breakdown
        'rubric_stats': rubric_stats,
        # Gamification
        'level':  level_info,
        'badges': badges,
    }


def _get_level(rating):
    for lo, hi, name, color, icon in LEVELS:
        if lo <= rating < hi:
            progress = round((rating - lo) / (hi - lo) * 100) if hi > lo else 100
            next_name = None
            for lo2, hi2, n2, _, _ in LEVELS:
                if lo2 == hi:
                    next_name = n2
                    break
            return {
                'name': name, 'color': color, 'icon': icon,
                'progress': progress, 'next_threshold': hi, 'next_name': next_name,
            }
    return {
        'name': 'Топ-эксперт', 'color': 'warning', 'icon': 'trophy-fill',
        'progress': 100, 'next_threshold': None, 'next_name': None,
    }


def _get_badges(quality, efficiency, total_comments, docs):
    earned = set()
    if quality >= 80:
        earned.add('quality_master')
    if efficiency >= 80:
        earned.add('speed_demon')
    if total_comments >= 10:
        earned.add('prolific')
    if len(docs) >= 5:
        earned.add('veteran')
    if any(d.doc_type == 'standard' for d in docs):
        earned.add('standard_master')
    if efficiency >= 90:
        earned.add('consistent')

    return [
        {'key': k, 'name': n, 'icon': ic, 'color': cl, 'desc': d, 'earned': k in earned}
        for k, n, ic, cl, d in BADGE_DEFS
    ]
