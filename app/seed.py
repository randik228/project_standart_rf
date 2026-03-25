from datetime import datetime, date, timedelta
from app import db
from app.models import (User, Rubric, Document, DocumentVersion, Comment,
                        DocumentStage, Notification, Message, RubricExpert,
                        OrgFavoriteRubric, OrgFavoriteDocument, ExpertProposal)


def seed_data():
    if User.query.count() > 0:
        return

    print("[seed] Заполнение базы демо-данными...")

    # ── Users ─────────────────────────────────────────────────────────────────
    # rubric_id assigned after rubrics are flushed (see below)
    admin = User(username='admin', email='svistelnikov@rosdornii.ru', password='admin123',
                 role='admin', full_name='Свистельников Александр Анатольевич',
                 organization='ФАУ «РОСДОРНИИ»',
                 position='Заместитель начальника управления методологии ИТС')

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

    org_company = User(username='techcorp', email='techcorp@example.ru', password='demo123',
                       role='organization', full_name='Сидорова Елена Михайловна',
                       organization='ООО «ТехКорп»', position='Директор по развитию')

    org_autodor = User(username='autodororg', email='autodor@org.ru', password='demo123',
                       role='organization', full_name='Новикова Ирина Сергеевна',
                       organization='ГК «Автодор»', position='Директор проектного офиса')

    db.session.add_all([admin, org1, org2, org_company, org_autodor,
                        expert1, expert2, expert3, expert4])
    db.session.flush()

    # ── Rubrics ───────────────────────────────────────────────────────────────
    # (rubric_id for admin/orgs is set after flush below)
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

    # Assign rubrics: admin → ИТС (rubrics[0])
    #                 org1  → ИТС (rubrics[0])
    #                 org2  → УДД (rubrics[2])
    admin.rubric_id = rubrics[0].id
    org1.rubric_id  = rubrics[0].id
    org2.rubric_id  = rubrics[2].id
    db.session.flush()

    # Все эксперты привязаны к организациям
    expert1.org_id = org_company.id
    expert2.org_id = org_company.id
    expert3.org_id = org_autodor.id
    expert4.org_id = org_company.id
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
             status='published', doc_type='methodical',
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
             status='published', doc_type='standard',
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
        (1, 'Загружено',                 'Подготовка и оформление текста документа разработчиком'),
        (2, 'Публикация',                'Размещение документа на портале. Открытие доступа к комментариям от Экспертов'),
        (3, 'Загрузка итоговой версии',  'Загрузка окончательного варианта документа с учётом поступивших замечаний'),
        (4, 'Утверждение',               'Официальное утверждение и введение в действие'),
    ]
    STATUS_ACTIVE_STAGE = {
        'draft': 1, 'published': 2,
        'review': 3, 'approved': 4, 'rejected': 3,
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
    # Fields: doc, author, type, structural_element, letter_details, text, proposed_text, justification, developer_response, status, hours_ago
    comments_raw = [
        # МР-15-2024 (discussion)
        dict(doc=docs[1], author=expert1, ctype='remark',
             el='п. 3.2', letter='Исх. №147 от 12.03.2024',
             text='В пункте 3.2 необходимо уточнить требования к минимальному количеству датчиков на 1 км дороги.',
             proposed='Дополнить п. 3.2: «Минимальное количество датчиков для дорог 1-й категории — не менее 4 ед./км».',
             just='Действующие европейские нормы EN 17429 предусматривают именно такую плотность датчиков.',
             response=None, status='new', hours=5),

        dict(doc=docs[1], author=expert2, ctype='proposal',
             el='п. 5.1', letter='Исх. №23 от 14.03.2024',
             text='Предлагаю дополнить раздел 5.1 требованиями к системе архивирования данных мониторинга.',
             proposed='Срок хранения данных — не менее 3 лет, с обязательным резервным копированием не реже 1 раза в сутки.',
             just='Требование согласуется с Постановлением Правительства РФ №1217 о хранении данных транспортного мониторинга.',
             response='Принято. Будет включено в п. 5.1.3 в следующей редакции.', status='accepted', hours=48),

        dict(doc=docs[1], author=expert3, ctype='question',
             el='Раздел 1. Общие положения', letter=None,
             text='Каким образом данная методика соотносится с действующим ГОСТ Р 58948-2020? Необходимо добавить раздел по гармонизации.',
             proposed=None,
             just='Отсутствие ссылок на ГОСТ Р 58948-2020 создаёт риск противоречий при практическом применении.',
             response=None, status='new', hours=12),

        dict(doc=docs[1], author=expert4, ctype='remark',
             el='Приложение А', letter='Исх. №89 от 05.03.2024',
             text='Приложение А содержит устаревшие технические характеристики сенсоров (таблица А.1 датирована 2018 годом).',
             proposed='Актуализировать таблицу А.1 с учётом современных решений (не старше 2022 г.).',
             just='Использование устаревших характеристик приведёт к занижению требований к закупаемому оборудованию.',
             response='Принято. Таблица А.1 будет обновлена в следующей редакции.', status='accepted', hours=120),

        # ГОСТ Р 57576-2024 (discussion)
        dict(doc=docs[5], author=expert1, ctype='proposal',
             el='п. 7.3', letter='Исх. №152 от 18.03.2024',
             text='В требованиях к ПАК ЦУДД необходимо предусмотреть поддержку протокола NTCIP 1211.',
             proposed='Дополнить п. 7.3 подпунктом: «ПАК должен поддерживать протокол NTCIP 1211 v2.0 и выше».',
             just='Протокол NTCIP 1211 является международным стандартом взаимодействия ЦУДД и широко применяется в зарубежной практике.',
             response=None, status='new', hours=2),

        dict(doc=docs[5], author=expert2, ctype='remark',
             el='п. 4.1.2', letter='Исх. №31 от 20.03.2024',
             text='Требования к отказоустойчивости системы (99,9% доступности) недостаточны для объектов критической инфраструктуры.',
             proposed='Изменить значение доступности в п. 4.1.2 с 99,9% на 99,95%.',
             just='СТО 59012820.29.160.10.003-2017 для объектов КИИ требует доступность не ниже 99,95%.',
             response=None, status='new', hours=8),

        # РД (review)
        dict(doc=docs[2], author=expert3, ctype='remark',
             el='п. 2.4', letter=None,
             text='Необходимо уточнить требования к светоотражающим элементам ограждений в ночное время.',
             proposed='В п. 2.4 добавить: «Световозвращающие элементы должны соответствовать ГОСТ Р 52290 кл. III».',
             just='Действующий ГОСТ Р 52290 устанавливает более высокие требования, чем указано в тексте документа.',
             response='Принято частично. Ссылка на ГОСТ Р 52290 будет добавлена, класс уточним при согласовании.', status='accepted_partly', hours=72),
    ]

    for c in comments_raw:
        db.session.add(Comment(
            document_id=c['doc'].id, user_id=c['author'].id, comment_type=c['ctype'],
            structural_element=c['el'], letter_details=c['letter'],
            text=c['text'], proposed_text=c['proposed'], justification=c['just'],
            developer_response=c['response'], status=c['status'],
            created_at=datetime.now() - timedelta(hours=c['hours']),
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

    # OrgFavoriteRubric: org_company likes ИТС and УДД; org_autodor likes УДД and ЦТИ
    db.session.add(OrgFavoriteRubric(org_id=org_company.id, rubric_id=rubrics[0].id))
    db.session.add(OrgFavoriteRubric(org_id=org_company.id, rubric_id=rubrics[2].id))
    db.session.add(OrgFavoriteRubric(org_id=org_autodor.id, rubric_id=rubrics[2].id))
    db.session.add(OrgFavoriteRubric(org_id=org_autodor.id, rubric_id=rubrics[3].id))

    # OrgFavoriteDocument: org_company отметила несколько документов
    from app.models import OrgFavoriteDocument
    db.session.add(OrgFavoriteDocument(org_id=org_company.id, document_id=docs[3].id))  # ГОСТ Р 59337-2023
    db.session.add(OrgFavoriteDocument(org_id=org_company.id, document_id=docs[5].id))  # ГОСТ Р 57576-2024

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
