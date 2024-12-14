COMMANDS_LIST = (
    "/bot - вызов меню бота",
    "/help - Список всех команд"
    "/hi - приветствие клана", 
    "/kto - вывод информации о человеке",
    "/inst - сбор в инсты",
    "/bye1 - прощание тип 1",
    "/bye2 - прощание тип 2",
    "/fu - осуждение за мат", 
    "/dno - пираты",
    "/nakol - наказание", 
    "/klaar - жаба"
)

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

HELP_TEXT_HEADER = (
    "*Привет, дружище! Я Бот этого чата и слежу за тобой!*\n\n"
    "Я приветствую новичков, слежу за порядком и делаю рассылки по активностям.\n\n"
    "Также я могу ответить на следующие фразы:\n"
)

NAME_TABLE = {
    "Аня (Elisan)":{"name": "Аня(Elisan)", "tgnick": "Аня (Elisan)", "nick": "@muse_queen", "about": "Кл, Местный боженька. Средний сум."},
    "Евгений(ХныкКи)":{"name": "Евгений(ХныкКи)", "tgnick": "Евгений(ХныкКи)", "nick": "@disika", "about": "Второй после боженьки. Местный сенсей. Ответит на любые вопросы по игре. Активный."},
    "Павел":{"name": "Павел(Обезгномливание)", "tgnick": "Павел", "nick": "@Pavel1234455", "about": "ПромежУточный сум. Водит на блески, может поделится какой-то информацией(не всегда полезной). Подскажет по сумам. Активный."},
    "Крис":{"name": "Кристина(СерыеГлазки)", "tgnick": "Крис", "nick": "@krisdnk", "about": "Тонкий высокоуровневый хил. Активная."},
    "Леонид Инженер":{"name": "Леонид(ТуманныйТор)", "tgnick": "Леонид Инженер", "nick": "нет", "about": "Высокоуровневый сум. Активный."},
    "Дмитрий":{"name": "Дмитрий(маКароноВирус)", "tgnick": "Дмитрий", "nick": "@DDestopia", "about": "Хил. Тонкий. Болтливй."},
    "Игорь (ФунтАпельсинов)":{"name": "Игорь(ФунтАпельсинов)", "tgnick": "Игорь (ФунтАпельсинов)", "nick": "@Just_Reck", "about": "Слабый сум. Тонковатый, но активный."},
    "Shaadun":{"name": "Вячеслав(DumSpiroSpero)", "tgnick": "Shaadun", "nick": "нет", "about": "Слабая агуша. Активный."},
    "Jki Olh":{"name": "Александр(Клаар)", "tgnick": "Jki Olh", "nick": "нет", "about": "Сильный высокоуровневый дк. Активный."},
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
    "сергей алексее":{"name": "Сергей(iNeer)", "tgnick": "сергей алексее", "nick": "@GinoLanetty", "about": "Нож. Он есть."},
    "Алена Лапихина":{"name": "Алена(АЗиЗа)", "tgnick": "Алена Лапихина", "nick": "@alenka_azi", "about": "Бд. Она есть."},
    "Artem Yakovlev":{"name": "Артем(DeathDior)", "tgnick": "Artem Yakovlev", "nick": "@svao92", "about": "Дк. Он есть."},
    "Андрей🍅":{"name": "Андрей(Greshnyy)", "tgnick": "Андрей🍅", "nick": "@Andrey_kisel72", "about": "Дк. Он есть."},
    "Sergey None":{"name": "Сергей(Butchery)", "tgnick": "Sergey None)", "nick": "@ru_vehement", "about": "Вл. Он есть."},
    "Михаил [Remorse]":{"name": "Михаил(Remorse)", "tgnick": "Михаил [Remorse]", "nick": "@RemorseADV", "about": "В активном поиске профессии. У него есть лук. Он есть."}
}

ALIASES = {
    "Аня (Elisan)": ["Elisan", "Элисан", "Анна"],
    "Евгений(ХныкКи)": ["ХныкКи", "Хныки", "Женя"],
    "Павел": ["Обезгномливание", "гном", "Шантиметр", "Павлуша"],
    "Sopore": ["Константин", "Сапоре", "Сопоре"],
    "Крис": ["Кристина", "СерыеГлазки", "Глазки"],
    "Леонид Инженер": ["Леонид", "Инженер", "Тор", "Аотис", "Аникет", "Бафалка", "БафалкаМоя", "ТуманныйТор"],
    "Дмитрий": ["маКароноВирус", "ТолстоклювыйГусь", "БезумнаяКраяква", "БоберШатун", "Гусь", "Вирус", "Дима"],
    "Игорь (ФунтАпельсинов)": ["ФунтАпельсинов", "Фунт"],
    "Shaadun": ["DumSpiroSpero", "Dum"],
    "Jki Olh": ["Клаар", "Jki", "Olh"],
    "Лёха Большой": ["Анфетаминчик", "Леха"],
    "Zloy": ["Слава", "Saela"],
    "Max": ["Максим", "Макс", "Вспомогашка", "Самсенашел"],
    "Иван Глущенко Ivan Hlushchenko": ["Иван", "Ваня", "xNicEBabYx", "nice", "найс"],
    "Александр": ["Piuv",],
    "Евгений": ["Ямалой", "Малой"],
    "Oleh Lukin": ["Олег","ECL", "Oleh"],
    "GP": ["Георгий", "ZeRama", "Гоша"],
    "Witcher792": ["Владимир", "Призывуля215", "Призывуля", "Witcher", "Вичер"],
    "Rocky NV": ["Дамир", "Rocky", "EvelyneNV", "Evelyne"],
    "Бишоп": ["DDextrim", "Экстрим"],
    "Hylio": ["Роман", "ХоаН", "Рома"],
    "сергей алексее": ["Сергей", "iNeer", "neer", "ниир"],
    "Алена Лапихина": ["Алена", "АЗиЗа"],
    "Artem Yakovlev": ["Артем", "DeathDior", "Artem"],
    "Андрей🍅": ["Андрей", "Greshnyy",],
    "Sergey None": ["Sergey", "Сергей", "Butchery"],
    "Михаил [Remorse]": ["Михаил", "Remorse" "[Remorse]"]
}

# Словарь соответствия id -> имя
USER_MAPPING = {
    559273200: "Дмитрий(маКароноВирус)",
    638155657: "Вячеслав(DumSpiroSpero)",
    1141764502: "Аня(Elisan)",
    1034353655: "Вячеслав(Saela)",
    809946596: "Кристина(СерыеГлазки)",
    5263336963: "Леонид(ТуманныйТор)",
    1687314254: "Игорь(ФунтАпельсинов)",
    1207400705: "Евгений(ХныкКи)",
    1705787763: "Александр(Piuv)",
    442475543: "Александр(Клаар)",
    923927066: "Михаил(Remorse)",
    901197619: "Дамир(EvelyneNV)",
}

FIRST = (
    "Привет, я помощник клана DareDevils!\n"
    "Я могу многое подсказать по игре, рассказать о нас и отвечать на некоторые команды.\n\n"
    "Вот несколько полезных ссылок рассказывающих о нас:\n\n"
    "<a href='https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=977389999#gid=977389999'>Структура клана</a>\n"
    "<a href='https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=1017631947#gid=1017631947'>Состав клана</a>\n"
    "<a href='https://www.google.com/maps/d/viewer?mid=129ywh4oGGwPzaB-hhszzZqh2iG7JPzM&ll=54.49364624759098%2C71.6847242&z=4'>География клана</a>\n"
    "<a href='https://docs.google.com/spreadsheets/d/1YVuchkaFxnK6swm2n8W4Syy0nM2WqgmlhrBQ8WHxqvY/edit?gid=833263188#gid=833263188'>Ранги и привилегии</a>\n\n"
    "Нажимай на кнопки внизу, чтобы получить больше информации."
)


ABOUT = (
    "Я бот, разработанный персонажем @DDestopia.\n\n"
    "Если нужно что-то доделать или поменять, пишите ему в личку.\n\n"
    '<a href="https://github.com/DmitriyVirus/Bot/tree/main">GitHub</a>\n\n'
    "Copyright ©2024. All rights reserved."
)



