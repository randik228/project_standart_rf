from datetime import datetime, date, timedelta
from app import db
from app.models import (User, Rubric, Document, DocumentVersion, Comment,
                        DocumentStage, Notification, Message, RubricExpert)


def seed_data():
    if User.query.count() > 0:
        return

    print("[seed] Заполнение базы демо-данными...")

    # ── Users ─────────────────────────────────────────────────────────────────
    admin = User(username='admin', email='admin@standart-rf.ru', password='admin123',
                 role='admin', full_name='Администратор Системы',
                 organization='Портал «Стандарт РФ»', position='Системный администратор')

    org1 = User(username='mintrans', email='mintrans@gov.ru', password='demo123',
                role='org', full_name='Иванов Сергей Николаевич',
                organization='Министерство транспорта РФ',
                position='Начальник отдела стандартизации')

    org2 = User(username='rosstandart', email='rosstandart@gov.ru', password='demo123',
                role='org', full_name='Петрова Анна Викторовна',
                organization='Росстандарт',
                position='Руководитель направления ИТС')

    expert1 = User(username='smirnov', email='smirnov@ncts.ru', password='demo123',
                   role='expert', full_name='Смирнов Алексей Петрович',
                   organization='НЦТС (Нац. центр транспортной безопасности)',
                   position='Ведущий эксперт по ИТС')

    expert2 = User(username='kozlov', email='kozlov@its-expert.ru', password='demo123',
                   role='expert', full_name='Козлов Дмитрий Игоревич',
                   organization='НИПИ ИТС',
                   position='Руководитель проектного отдела')

    expert3 = User(username='sokolova', email='sokolova@avtodor.ru', password='demo123',
                   role='expert', full_name='Соколова Мария Андреевна',
                   organization='ГК «Автодор»',
                   position='Эксперт по цифровой инфраструктуре')

    expert4 = User(username='morozov', email='morozov@tsniis.ru', password='demo123',
                   role='expert', full_name='Морозов Игорь Владимирович',
                   organization='ЦНИИС',
                   position='Д.т.н., профессор')

    db.session.add_all([admin, org1, org2, expert1, expert2, expert3, expert4])
    db.session.flush()

    # ── Rubrics ───────────────────────────────────────────────────────────────
    rubrics_raw = [
        ('ИТС',  'Интеллектуальные транспортные системы',
         'Стандарты и методические документы в области разработки, внедрения и эксплуатации ИТС'),
        ('БДД',  'Безопасность дорожного движения',
         'Нормативные документы по обеспечению безопасности на дорогах'),
        ('УДД',  'Управление дорожным движением',
         'Документы, регламентирующие системы и методы управления транспортными потоками'),
        ('ЦТИ',  'Цифровая транспортная инфраструктура',
         'Стандарты цифровизации дорожной инфраструктуры, V2X-коммуникации, подключённые дороги'),
        ('ЭМТ',  'Экологический мониторинг транспорта',
         'Методические документы по мониторингу экологического воздействия транспорта'),
    ]
    rubrics = []
    for code, name, desc in rubrics_raw:
        r = Rubric(code=code, name=name, description=desc)
        db.session.add(r)
        rubrics.append(r)
    db.session.flush()

    # ── Documents ─────────────────────────────────────────────────────────────
    docs_raw = [
        dict(title='ГОСТ Р 58948-2020. ИТС. Требования к информационному взаимодействию подсистем',
             number='ГОСТ Р 58948-2020', rubric=rubrics[0], author=org1,
             status='approved', doc_type='standard',
             desc='Стандарт устанавливает требования к информационному взаимодействию подсистем ИТС, '
                  'включая протоколы обмена данными, форматы сообщений и требования к интеграционным платформам.',
             deadline=date.today() - timedelta(days=90), days_ago=120),

        dict(title='МР-15-2024. Методические рекомендации по внедрению систем мониторинга дорожного покрытия',
             number='МР-15-2024', rubric=rubrics[3], author=org1,
             status='discussion', doc_type='methodical',
             desc='Методические рекомендации определяют порядок внедрения автоматизированных систем '
                  'непрерывного мониторинга состояния дорожного покрытия с использованием сенсорных сетей.',
             deadline=date.today() + timedelta(days=21), days_ago=30),

        dict(title='РД 3112199-1073-98 (изм. 2024). Организация движения в зонах дорожных работ',
             number='РД 3112199-1073-98', rubric=rubrics[2], author=org2,
             status='review', doc_type='normative',
             desc='Документ регламентирует организацию временных схем дорожного движения в зонах '
                  'проведения дорожно-строительных и ремонтных работ.',
             deadline=date.today() + timedelta(days=14), days_ago=45),

        dict(title='ГОСТ Р 59337-2023. Системы дорожного мониторинга. Требования к комплексам видеонаблюдения',
             number='ГОСТ Р 59337-2023', rubric=rubrics[0], author=org2,
             status='published', doc_type='standard',
             desc='Стандарт устанавливает технические требования к комплексам видеонаблюдения, '
                  'применяемым в системах дорожного мониторинга.',
             deadline=date.today() + timedelta(days=30), days_ago=20),

        dict(title='МР-08-2024. Методика расчёта экономической эффективности внедрения ИТС',
             number='МР-08-2024', rubric=rubrics[0], author=org1,
             status='draft', doc_type='methodical',
             desc='Методика предназначена для оценки экономической эффективности проектов по внедрению '
                  'ИТС на федеральных автомобильных дорогах.',
             deadline=None, days_ago=5),

        dict(title='ГОСТ Р 57576-2024. ЦУДД. Требования к программно-аппаратному комплексу',
             number='ГОСТ Р 57576-2024', rubric=rubrics[2], author=org2,
             status='discussion', doc_type='standard',
             desc='Настоящий стандарт устанавливает требования к составу и характеристикам '
                  'программно-аппаратного комплекса центров управления дорожным движением.',
             deadline=date.today() + timedelta(days=45), days_ago=15),

        dict(title='СП 34.13330.2022. Автомобильные дороги. Актуализированная редакция',
             number='СП 34.13330.2022', rubric=rubrics[1], author=org1,
             status='approved', doc_type='technical',
             desc='Актуализированная редакция свода правил устанавливает требования к проектированию '
                  'автомобильных дорог общего пользования.',
             deadline=date.today() - timedelta(days=180), days_ago=200),
    ]

    docs = []
    for d in docs_raw:
        doc = Document(
            title=d['title'], number=d['number'],
            rubric_id=d['rubric'].id, author_id=d['author'].id,
            status=d['status'], doc_type=d['doc_type'], description=d['desc'],
            discussion_deadline=d['deadline'],
            created_at=datetime.now() - timedelta(days=d['days_ago']),
            updated_at=datetime.now() - timedelta(days=max(1, d['days_ago'] // 4)),
        )
        db.session.add(doc)
        docs.append(doc)
    db.session.flush()

    # ── Document Versions ─────────────────────────────────────────────────────
    versions = [
        DocumentVersion(document_id=docs[0].id, version_number='1.0',
                        file_name='ГОСТ_Р_58948-2020.pdf', file_size=2456789,
                        uploaded_by=org1.id, uploaded_at=datetime.now()-timedelta(days=120)),
        DocumentVersion(document_id=docs[1].id, version_number='1.0',
                        file_name='МР-15-2024_v1.0.pdf', file_size=1234567,
                        uploaded_by=org1.id, uploaded_at=datetime.now()-timedelta(days=30)),
        DocumentVersion(document_id=docs[1].id, version_number='1.1',
                        file_name='МР-15-2024_v1.1.pdf', file_size=1345678,
                        uploaded_by=org1.id, uploaded_at=datetime.now()-timedelta(days=10),
                        note='Внесены правки по результатам первичного рассмотрения'),
        DocumentVersion(document_id=docs[2].id, version_number='2.0',
                        file_name='РД_3112199-1073-98_ред2024.pdf', file_size=3456789,
                        uploaded_by=org2.id, uploaded_at=datetime.now()-timedelta(days=45)),
        DocumentVersion(document_id=docs[3].id, version_number='1.0',
                        file_name='ГОСТ_Р_59337-2023.pdf', file_size=2123456,
                        uploaded_by=org2.id, uploaded_at=datetime.now()-timedelta(days=20)),
        DocumentVersion(document_id=docs[5].id, version_number='1.0',
                        file_name='ГОСТ_Р_57576-2024_проект.pdf', file_size=1987654,
                        uploaded_by=org2.id, uploaded_at=datetime.now()-timedelta(days=15)),
        DocumentVersion(document_id=docs[6].id, version_number='1.0',
                        file_name='СП_34.13330.2022.pdf', file_size=5432100,
                        uploaded_by=org1.id, uploaded_at=datetime.now()-timedelta(days=200)),
    ]
    db.session.add_all(versions)

    # ── Document Stages ───────────────────────────────────────────────────────
    STAGES_TEMPLATE = [
        (1, 'Разработка',          'Подготовка и оформление текста документа'),
        (2, 'Публикация',          'Размещение документа на портале'),
        (3, 'Открытое обсуждение', 'Сбор замечаний и предложений от экспертного сообщества'),
        (4, 'Сводка предложений',  'Систематизация и обработка поступивших замечаний'),
        (5, 'Согласование',        'Согласование с заинтересованными федеральными органами'),
        (6, 'Утверждение',         'Официальное утверждение и введение в действие'),
    ]
    STATUS_ACTIVE_STAGE = {
        'draft': 1, 'published': 2, 'discussion': 3,
        'review': 5, 'approved': 6, 'rejected': 3,
    }

    for doc in docs:
        active = STATUS_ACTIVE_STAGE.get(doc.status, 1)
        base_date = doc.created_at.date()
        for order, name, desc in STAGES_TEMPLATE:
            if order < active:
                st, d = 'completed', base_date + timedelta(days=(order - 1) * 14)
            elif order == active:
                st, d = 'active', base_date + timedelta(days=(order - 1) * 14)
            else:
                st, d = 'pending', None
            db.session.add(DocumentStage(
                document_id=doc.id, name=name, order=order,
                status=st, date=d, description=desc
            ))
    db.session.flush()

    # ── Comments ──────────────────────────────────────────────────────────────
    comments_raw = [
        # МР-15-2024 (discussion)
        (docs[1], expert1, 'remark',   'п. 3.2',
         'В пункте 3.2 необходимо уточнить требования к минимальному количеству датчиков '
         'на 1 км дороги. Предлагаю установить норматив не менее 4 датчиков/км для дорог 1-й категории.',
         'new', 5),
        (docs[1], expert2, 'proposal', 'п. 5.1',
         'Предлагаю дополнить раздел 5.1 требованиями к системе архивирования данных. '
         'Срок хранения данных мониторинга должен составлять не менее 3 лет с обязательным резервным копированием.',
         'reviewed', 48),
        (docs[1], expert3, 'question', 'Общие положения',
         'Каким образом данная методика соотносится с действующим ГОСТ Р 58948-2020? '
         'Необходимо добавить раздел по гармонизации с существующей нормативной базой.',
         'new', 12),
        (docs[1], expert4, 'remark',   'Приложение А',
         'Приложение А содержит устаревшие технические характеристики сенсоров. '
         'Рекомендую актуализировать таблицу А.1 с учётом современных решений.',
         'accepted', 120),

        # ГОСТ Р 57576-2024 (discussion)
        (docs[5], expert1, 'proposal', 'п. 7.3',
         'В требованиях к ПАК ЦУДД необходимо предусмотреть поддержку протокола NTCIP 1211 '
         'для взаимодействия с системами регулирования дорожным движением.',
         'new', 2),
        (docs[5], expert2, 'remark',   'п. 4.1.2',
         'Требования к отказоустойчивости системы (99,9% доступности) недостаточны для объектов '
         'критической инфраструктуры. Предлагаю повысить до 99,95%.',
         'new', 8),

        # РД (review)
        (docs[2], expert3, 'remark',   'п. 2.4',
         'Необходимо уточнить требования к светоотражающим элементам ограждений в ночное время.',
         'reviewed', 72),
    ]

    for doc, user, ctype, section, text, status, hours_ago in comments_raw:
        db.session.add(Comment(
            document_id=doc.id, user_id=user.id, comment_type=ctype,
            section=section, text=text, status=status,
            created_at=datetime.now() - timedelta(hours=hours_ago),
        ))
    db.session.flush()

    # ── Rubric Experts ────────────────────────────────────────────────────────
    assignments = [
        (rubrics[0], expert1), (rubrics[0], expert2), (rubrics[0], expert4),
        (rubrics[1], expert1), (rubrics[1], expert3),
        (rubrics[2], expert2), (rubrics[2], expert3),
        (rubrics[3], expert3), (rubrics[3], expert4),
        (rubrics[4], expert1),
    ]
    for rubric, user in assignments:
        db.session.add(RubricExpert(rubric_id=rubric.id, user_id=user.id))

    # ── Notifications ─────────────────────────────────────────────────────────
    notifications = [
        Notification(user_id=expert1.id, is_read=False, notification_type='info',
                     title='Новый документ на обсуждение',
                     text=f'Опубликован документ МР-15-2024 по рубрике ИТС. Срок подачи замечаний: '
                          f'{(date.today()+timedelta(days=21)).strftime("%d.%m.%Y")}',
                     link='/documents/2', created_at=datetime.now()-timedelta(hours=3)),
        Notification(user_id=expert1.id, is_read=True, notification_type='success',
                     title='Ваше замечание принято',
                     text='Замечание по документу МР-15-2024 (Приложение А) принято к включению в сводку',
                     link='/documents/2', created_at=datetime.now()-timedelta(days=1)),
        Notification(user_id=expert1.id, is_read=False, notification_type='warning',
                     title='Срок обсуждения истекает',
                     text='До окончания срока обсуждения МР-15-2024 осталось 21 день',
                     link='/documents/2', created_at=datetime.now()-timedelta(hours=6)),
        Notification(user_id=org1.id, is_read=False, notification_type='info',
                     title='Новое замечание к документу',
                     text='По документу МР-15-2024 поступило замечание от эксперта Смирнова А.П.',
                     link='/documents/2', created_at=datetime.now()-timedelta(hours=5)),
        Notification(user_id=org1.id, is_read=True, notification_type='info',
                     title='Новое предложение к документу',
                     text='По документу МР-15-2024 поступило предложение от эксперта Козлова Д.И.',
                     link='/documents/2', created_at=datetime.now()-timedelta(days=2)),
        Notification(user_id=org2.id, is_read=False, notification_type='warning',
                     title='Документ ожидает публикации',
                     text='Документ ГОСТ Р 59337-2023 находится в статусе «Опубликован» — '
                          'откройте обсуждение для сбора замечаний',
                     link='/documents/4', created_at=datetime.now()-timedelta(hours=2)),
        Notification(user_id=admin.id, is_read=False, notification_type='info',
                     title='Активность обсуждений',
                     text='За последние 24 часа поступило 6 новых замечаний по документам',
                     created_at=datetime.now()-timedelta(hours=1)),
    ]
    db.session.add_all(notifications)

    # ── Messages ──────────────────────────────────────────────────────────────
    messages = [
        Message(sender_id=org1.id, receiver_id=expert1.id,
                subject='Запрос на рецензию МР-15-2024',
                text=f'Уважаемый Алексей Петрович!\n\n'
                     f'Просим Вас рассмотреть проект методических рекомендаций МР-15-2024 и предоставить '
                     f'экспертное заключение в срок до {(date.today()+timedelta(days=14)).strftime("%d.%m.%Y")}.\n\n'
                     f'С уважением,\nИванов С.Н.\nМинистерство транспорта РФ',
                is_read=True, created_at=datetime.now()-timedelta(days=3)),
        Message(sender_id=expert1.id, receiver_id=org1.id,
                subject='Re: Запрос на рецензию МР-15-2024',
                text='Уважаемый Сергей Николаевич!\n\n'
                     'Подтверждаю получение документа. Рецензия будет предоставлена в указанный срок. '
                     'Предварительно могу отметить, что раздел 3 требует существенной доработки '
                     'в части требований к плотности датчиков.\n\n'
                     'С уважением,\nСмирнов А.П.\nНЦТС',
                is_read=False, created_at=datetime.now()-timedelta(days=1)),
        Message(sender_id=org2.id, receiver_id=expert2.id,
                subject='Приглашение в рабочую группу по ГОСТ Р 57576-2024',
                text='Уважаемый Дмитрий Игоревич!\n\n'
                     'Приглашаем Вас принять участие в работе экспертной группы по рассмотрению '
                     'проекта стандарта ГОСТ Р 57576-2024. Первое заседание планируется '
                     f'на {(date.today()+timedelta(days=7)).strftime("%d.%m.%Y")}.\n\n'
                     'С уважением,\nПетрова А.В.\nРосстандарт',
                is_read=False, created_at=datetime.now()-timedelta(hours=4)),
    ]
    db.session.add_all(messages)

    db.session.commit()
    print("[seed] База данных успешно заполнена демо-данными.")
