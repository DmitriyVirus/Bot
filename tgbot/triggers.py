COMMANDS_LIST = (
    "/bot - вызов меню бота",
    "/detron - инфо о свержении",
    "/macros - инфо о макросах",
    "/hi - приветствие клана", 
    "/kto - вывод информации о человеке",
    "/inst - сбор в инсты",
    "/bye1 - прощание тип 1",
    "/bye2 - прощание тип 2",
    "/fu - осуждение за мат", 
    "/dno - пираты",
    "/nakol - наказание", 
    "/klaar - жаба",
    "/kris - игрушка с ножиком",
    "/gg1 - веселая песенка",
    "/leo - все...",
    "/help - Список всех команд"
)

NAME_TABLE = {
    "Аня (Elisan)":{"name": "Аня(Elisan)", "tgnick": "Аня (Elisan)", "nick": "@muse_queen", "about": "Кл, Местный боженька. Средний сум."},
    "Евгений(ХныкКи)":{"name": "Евгений(ХныкКи)", "tgnick": "Евгений(ХныкКи)", "nick": "@disika", "about": "Второй после боженьки. Местный сенсей. Ответит на любые вопросы по игре. Активный."},
    "Павел":{"name": "Павел(Обезгномливание)", "tgnick": "Павел", "nick": "@Pavel1234455", "about": "ПромежУточный сум. Водит на блески, может поделится какой-то информацией(не всегда полезной). Подскажет по сумам. Активный."},
    "Крис":{"name": "Кристина(СерыеГлазки)", "tgnick": "Крис", "nick": "@krisdnk", "about": "Тонкий высокоуровневый хил. Активная."},
    "Леонид Инженер":{"name": "Леонид(ТуманныйТор)", "tgnick": "Леонид Инженер", "nick": "нет", "about": "Высокоуровневый сум. Активный."},
    "Дмитрий":{"name": "Дмитрий(маКароноВирус)", "tgnick": "Дмитрий", "nick": "@DDestopia", "about": "Хил. Тонкий. Болтливй."},
    "Игорь (ФунтАпельсинов)":{"name": "Игорь(ФунтАпельсинов)", "tgnick": "Игорь (ФунтАпельсинов)", "nick": "@Just_Reck", "about": "Тироняшка. Вроде живой."},
    "Shaadun":{"name": "Вячеслав(DumSpiroSpero)", "tgnick": "Shaadun", "nick": "нет", "about": "Ис - варкраер. Активный."},
    "Jki Olh":{"name": "Александр(Клаар)", "tgnick": "Jki Olh", "nick": "нет", "about": "Убигий клоун-жаба. Агуша. Активный."},
    "Лёха Большой":{"name": "Алексей(Анфетаминчик)", "tgnick": "Лёха Большой", "nick": "нет", "about": "Высокоуровневый нож. Активен, но молчаливый."},
    "Zloy":{"name": "Вячеслав(Saela)", "tgnick": "Zloy", "nick": "нет", "about": "ДА. Тонковатый но активный."},
    "Max":{"name": "Максим(Вспомогашка)", "tgnick": "Max", "nick": "нет", "about": "ПП. Молчаливый, тонкий, сонный."},
    "Иван Глущенко Ivan Hlushchenko":{"name": "Иван(xNicEBabYx)", "tgnick": "Иван Глущенко Ivan Hlushchenko", "nick": "нет", "about": "Высокуровневый дк. Молчаливый"},
    "Александр":{"name": "Александр(Piuv)", "tgnick": "Александр", "nick": "нет", "about": "Свс, не очень прочный, молчаливый."},
    "Евгений":{"name": "Евгений(Ямалой)", "tgnick": "Евгений", "nick": "нет", "about": "Высокоуровневый лук. Молчун."},
    "Oleh Lukin":{"name": "Олег(ECL)", "tgnick": "Oleh Lukin", "nick": "нет", "about": "Средний дк. Молчун."},
    "Sopore":{"name": "Константин(Sopore)", "tgnick": "Sopore", "nick": "@iSopore", "about": "ПП. Средней прочности. Активный."},
    "GP":{"name": "Георгий(ZeRama)", "tgnick": "GP", "nick": "нет", "about": "Нож. Он есть."},
    "Witcher792":{"name": "Владимир(Призывуля215)", "tgnick": "Witcher792", "nick": "нет", "about": "Самонер. Он есть."},
    "Rocky NV":{"name": "Дамир(EvelyneNV)", "tgnick": "Rocky NV", "nick": "нет", "about": "Средний самонер. Средней активности."},
    "Бишоп":{"name": "Павел(DDextrim)", "tgnick": "Бишоп", "nick": "нет", "about": "ПП. Он есть."},
    "Hylio":{"name": "Роман(ХоаН)", "tgnick": "Hylio", "nick": "нет", "about": "Дк. Он есть."},
    "Алена Лапихина":{"name": "Алена(АЗиЗа)", "tgnick": "Алена Лапихина", "nick": "@alenka_azi", "about": "Бд. Она есть."},
    "Artem Yakovlev":{"name": "Артем(DeathDior)", "tgnick": "Artem Yakovlev", "nick": "@svao92", "about": "Дк. Он есть."},
    "Андрей🍅":{"name": "Андрей(Greshnyy)", "tgnick": "Андрей🍅", "nick": "@Andrey_kisel72", "about": "Дк. Он есть."},
    "Sergey None":{"name": "Сергей(Butchery)", "tgnick": "Sergey None)", "nick": "@ru_vehement", "about": "Вл. Он есть."},
    "Михаил [Remorse]":{"name": "Михаил(Remorse)", "tgnick": "Михаил [Remorse]", "nick": "@RemorseADV", "about": "Мультипрофный чел. Он есть."}
}

DEBUG_BOT = (
    "/getid - получить id текущего чата",
    "/getidbot - получить id сообщения",
    "/goodmornigeverydayGG - утреннее приветствие"
)

WELCOME_TEXT = (
    "Быть в основе — означает участвовать в жизни и развитии клана.\n\n"
    "Мы:\n"
    "- Качаем учеников\n"
    "- Делимся полезной информацией\n"
    "- Отвечаем на вопросы\n"
    "- Участвуем в клановых мероприятиях\n"
    "- Организуем сборы\n"
    "- Помогаем с прокачкой\n"
    "- Приводим новых людей\n"
    "- Проводим собеседования\n"
    "- Разбираемся с варами\n\n"
    "Если ты новичок, покажи, как можешь помочь клану стать сильнее. "
    "Прокачка своих персонажей и выполнение миссий — это то, что каждый делает по умолчанию.\n\n"
    "Если ты уже в основе, но не участвуешь в жизни клана, тебя могут заменить. "
    "Наиболее активные участники всегда в приоритете. 💪"
)

TRIGGERS = {
    "кому ты служишь": "Мой хояин слишком известен, чтобы его называть! Можете звать его просто - Солнцеликий!",
    "кто у нас тут главный": "Наша великая насяльника и глава клана - *Elisan*, в простонародье - *Анна*.",
    "основные наши правила": (
        "1. Не носить серьгу Линдвиора, если носишь её, то получаешь анальное зондирование.\n"
        "2. Не заливать вар никому.\n"
        "*3. Не ругаться с КЛ.*\n"
        "*4. Уважать мнение солнцеликого ЕГО.*"
    ),
    "код красный тут матюки": {
        "text": "У нас так не принято, подонок!\n",
        "image": "https://memepedia.ru/wp-content/uploads/2021/02/bonk-mem-bonk-8.jpg"
    },
    "на кол посадить": {
        "text": "Вот так его!!!\n",
        "gif": "https://lastfm.freetls.fastly.net/i/u/ar0/4192f84a3d4a4828c8c836229da960df.gif"
    },
}

FIRST = (
    "😎   Привет, я бот-помощник клана DareDevils!😎\n\n"
    "🙌Я приветствую новичков, слежу за порядком и делаю рассылки по активностям.\n\n"
    "📚Также у меня есть некоторая база данных по игре, я могу рассказать о нас и отвечать на некоторые команды.\n\n"
    "👇Нажимай на кнопки внизу, чтобы получить больше информации.👇"
)

DAREDEVILS = (
    "Мы дружный и веселый клан, который играет в Lineage II на сервере Айрин.\n"
    "👇Вот несколько полезных ссылок, рассказывающих о нас:\n\n"
    '📝<a href="https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=977389999#gid=977389999">Структура клана</a>📝\n\n'
    '🧛<a href="https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=1017631947#gid=1017631947">Состав клана</a>🧙\n\n'
    '🗺️<a href="https://www.google.com/maps/d/viewer?mid=129ywh4oGGwPzaB-hhszzZqh2iG7JPzM&ll=54.49364624759098%2C71.6847242&z=4">География клана</a>🗺️\n\n'
    '🏆<a href="https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=833263188#gid=833263188">Ранги и привилегии</a>🏆\n\n'
    '🌐<a href="https://bot-virus-l2.vercel.app/">Наш сайт</a>'
)

ABOUT = (
    "Я бот, разработанный персонажем @DDestopia.\n"
    "Если нужно что-то доделать или поменять, пишите ему в личку.\n\n"
    '<a href="https://github.com/DmitriyVirus/Bot/tree/main">GitHub</a>\n\n'
    "Copyright ©2024. All rights reserved."
)

ABOUT_GAME = (
    "✍️Здесь записанны основные данные которые есть у нас об игре:\n\n"
    '🧑‍🎓<a href="https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=1945579481#gid=1945579481">Базовая полезная информация по бусту персонажа и по созданию аккаунтов с твинами</a>🧑‍🎓\n\n'
    '📔<a href="https://l2central.info/main/guides/1350.html#:~:text=%D0%A0%D0%B0%D0%B7%D0%B1%D0%BE%D0%B9%D0%BD%D0%B8%D0%BA%D0%B8%20%D0%9E%D0%B4%D0%B0%D0%BB%D0%B0%20%E2%80%93%20%D0%BB%D0%BE%D0%B2%D0%BA%D0%B8%D0%B5%20%D0%B8%20%D0%BE%D1%87%D0%B5%D0%BD%D1%8C,%D0%BF%D0%BE%20%D0%BE%D0%B4%D0%BD%D0%BE%D0%B9%20%D1%86%D0%B5%D0%BB%D0%B8%20%D0%B2%20%D0%B8%D0%B3%D1%80%D0%B5.">Библия любого ножа</a>📔\n\n'
    '📊<a href="https://docs.google.com/spreadsheets/d/11zzBp2SOl8gXw2fcTR07fOqm3aiyO-MXG6IbILdRZTU/edit?pli=1&gid=934369758#gid=934369758">Таблица необходимого атрибута атаки/защиты</a>📊\n\n'
    '🤑💰💸<a href="https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=423847096#gid=423847096">Информация по акциям и ивентам</a>💸💰🤑\n\n'
    "Советуем посетить несколько YouTube каналов для общего развития:\n\n"
    "Канал шейха Джонни 👉 <a href='https://www.youtube.com/@iJohny'>Джони TV</a>\n"
    "Его Telegram 👉 <a href='https://t.me/JohnyTV'>Джони TV - Lineage 2</a>\n\n"
    "Канал умника Либры 👉 <a href='https://www.youtube.com/@Libre123'>Libre Library</a>\n\n"
    "Если интересно что-либо более конкретное, на сложные вопросы могут ответить товарищи 🕵️‍♂️Евгений(@disika) и 🧑‍🔬Павел(@Pavel1234455)."
) 

DETRON = (
    "🤔🤨Что же такое этот Детрон?🤔🤨\n"
    "Ну, давайте разбиратся. Для начала посмотрим несколько обучающих видео на YouTube:\n\n"
    '<a href="https://www.youtube.com/watch?v=XpBO_iHaoAc">Гайд по детрону\свержение</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=IPEma2luoKY">Свержение в LineAge 2 main</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=w3Wmg14slik">Гайд на тему Фарм Личных очков свержения</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=W9reyVPPCPk">Гайд Источники Первоначального Огня</a>\n\n'
)

MACROS = (
    "🥵🥵Как настроить макросы для кача?🥵🥵\n"
    "Для начала необходимо посмотреть несколько обучающих видео на YouTube:\n\n"
    '<a href="https://www.youtube.com/watch?v=L-Vibtwjhqk">Макрос на два спота ЧЕРЕЗ ОДНОГО ПЕТА</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=p8iZX5D29t0">Фарм магом двух спотов</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=hSFkl6azj5o">Настройка макросной мыши для фарма в 2 Спота</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=0ImTG71aRmA">Макрос для фарма сумом на 2 спота</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=E7js0XaaYDw">Макрос для фарма на 2 спота, мышь 4Tech X7</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=N859ufwJAfQ"> Макрос для Bloody (Oscar) на 2 спота для сума</a>\n\n'
    '<a href="https://www.youtube.com/watch?v=0_KPNNP9Cdg">Макрос для фарма на 2 спота, 1 пет</a>\n\n'
)
