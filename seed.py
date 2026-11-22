import secrets
from werkzeug.security import generate_password_hash
from app import app
from db import get_db
from views.routes import path_length_km
import glob, os, shutil, sys

GEAR = [
    ("Рюкзак по размеру", "Основное", "any", "any", 1),
    ("Бутылка с питьевой водой", "Вода и еда", "any", "any", 1),
    ("Перекус (орехи, батончики)", "Вода и еда", "any", "any", 1),
    ("Аптечка с личными лекарствами", "Здоровье", "any", "any", 1),
    ("Телефон и внешний аккумулятор", "Связь и навигация", "any", "any", 1),
    ("Скачанная офлайн-карта маршрута", "Связь и навигация", "any", "any", 1),
    ("Документы и немного наличных", "Основное", "any", "any", 1),
    ("Удобная разношенная обувь", "Одежда и обувь", "any", "any", 1),
    ("Головной убор", "Одежда и обувь", "summer", "any", 1),
    ("Солнцезащитные очки", "Защита", "summer", "any", 1),
    ("Крем от солнца", "Защита", "summer", "any", 1),
    ("Лёгкая дышащая одежда", "Одежда и обувь", "summer", "any", 1),
    ("Средство от комаров и клещей", "Защита", "summer", "forest", 1),
    ("Тёплая куртка", "Одежда и обувь", "spring_autumn", "any", 1),
    ("Дождевик", "Одежда и обувь", "spring_autumn", "any", 1),
    ("Запасные носки", "Одежда и обувь", "spring_autumn", "any", 1),
    ("Перчатки", "Одежда и обувь", "spring_autumn", "any", 1),
    ("Термобельё", "Одежда и обувь", "winter", "any", 1),
    ("Тёплая шапка", "Одежда и обувь", "winter", "any", 1),
    ("Тёплые варежки", "Одежда и обувь", "winter", "any", 1),
    ("Утеплённая непромокаемая обувь", "Одежда и обувь", "winter", "any", 1),
    ("Термос с горячим напитком", "Вода и еда", "winter", "any", 1),
    ("Грелки для рук", "Здоровье", "winter", "any", 1),
    ("Свисток", "Безопасность", "any", "forest", 1),
    ("Треккинговые палки", "Основное", "any", "mountain", 1),
    ("Ботинки с протектором", "Одежда и обувь", "any", "mountain", 1),
    ("Ветровка", "Одежда и обувь", "any", "mountain", 1),
    ("Налобный фонарь", "Безопасность", "any", "mountain", 1),
    ("Непромокаемый чехол для телефона", "Защита", "any", "water", 1),
    ("Сменная обувь для воды", "Одежда и обувь", "summer", "water", 1),
    ("Палатка", "Ночёвка", "any", "any", 2),
    ("Спальный мешок", "Ночёвка", "any", "any", 2),
    ("Коврик", "Ночёвка", "any", "any", 2),
    ("Горелка и посуда", "Вода и еда", "any", "any", 2),
    ("Запас еды на все дни", "Вода и еда", "any", "any", 2),
    ("Средства очистки воды", "Вода и еда", "any", "any", 2),
    ("Налобный фонарь с запасными батарейками", "Безопасность", "any", "any", 2),
]

# ---- Настройки ----
# Фото обложек лежат в seed_photos/ (valdai.jpg, baikal.jpg, sestroretsk.jpg, iremel.jpg).
# Маршруты записываются на пользователя из команды: python seed.py ИМЯ
# (тогда вы сможете их править на сайте). Без имени используется служебный пользователь catalog.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.join(BASE_DIR, "seed_photos")
ROUTE_IMG_DIR = os.path.join(BASE_DIR, "static", "img", "routes")
OWNER = sys.argv[1] if len(sys.argv) > 1 else "catalog"
CHECKED = "2026-11-22"  # дата, когда проверены источники

# length_km взята из источников. Линии маршрута нет: нарисуйте её на сайте через «Редактировать».
ROUTES = [
    {
        "photo": "valdai",
        "title": "Большая Валдайская тропа (центральный участок)",
        "region": "Новгородская область",
        "difficulty": "easy", "days": 4, "season": "summer", "terrain": "forest",
        "length_km": 52,
        "description": (
            "Маркированный маршрут по территории национального парка «Валдайский». "
            "По данным путеводителя на август 2026 года вся тропа составляет 77 км: 52 км центрального "
            "участка и 25 км северного, старт у них общий, у информационного центра. Центральный участок "
            "проходят за 3–5 дней. Каждый километр отмечен, оборудованные стоянки расположены через "
            "12–14 км, по пути есть источники воды, но нет магазинов."
        ),
        "restrictions": (
            "Нужны пропуск в национальный парк и билет на размещение на стоянках. По данным одного из "
            "обзоров вход стоил 250 ₽ (цену уточняйте). Тропа доступна с мая по ноябрь, лучше идти "
            "до конца сентября."
        ),
        "source_url": "https://t-j.ru/bolshaya-valdayskaya-tropa/",
        "source_checked": CHECKED,
        "open_from": "2026-05-01", "open_to": "2026-11-30",
        "rest_points": "Оборудованные стоянки через каждые 12–14 км",
        "places": [
            {"name": "Валдай (ближайший город)", "lat": 57.9811, "lon": 33.2475,
             "note": "Ориентир, координаты приблизительные."},
            {"name": "Большая Валдайская тропа (ориентир из путеводителя)", "lat": 57.83369, "lon": 33.085895,
             "note": "Координаты из путеводителя, уточните на карте."},
        ],
    },
    {
        "photo": "baikal",
        "title": "Большая Байкальская тропа: Листвянка — Большие Коты",
        "region": "Иркутская область",
        "difficulty": "medium", "days": 1, "season": "summer", "terrain": "mountain",
        "length_km": 24,
        "description": (
            "Один из самых популярных и обустроенных участков Большой Байкальской тропы вдоль "
            "юго-западного берега Байкала, на территории Прибайкальского национального парка. "
            "Маршрут начинается в Листвянке с долгого подъёма примерно на 3,5 км, дальше идёт по "
            "гребням и склонам с видами на озеро. Обычно проходится за один день. Источники называют "
            "длину от 24 до 25 км."
        ),
        "restrictions": (
            "ВНИМАНИЕ: в сентябре 2026 года нацпарк «Заповедное Прибайкалье» закрыл маршрут из-за "
            "активности медведей; по сообщениям СМИ от 22.09.2026 он закрыт как минимум до середины "
            "октября. Сообщений о повторном открытии на дату проверки не найдено: перед выходом "
            "уточняйте статус на официальном сайте нацпарка. Для посещения участка в нацпарке нужно "
            "заранее оформлять разрешение."
        ),
        "source_url": "https://www.kommersant.ru/doc/8936573",
        "source_checked": CHECKED,
        "surface": "Грунтовая тропа; бывает скользкой, особенно после заморозков",
        "max_slope": "Долгий подъём (около 3,5 км) в начале маршрута",
        "places": [
            {"name": "Листвянка (старт)", "lat": 51.8667, "lon": 104.8333,
             "note": "Ориентир, координаты приблизительные."},
            {"name": "Большие Коты (финиш)", "lat": 51.9022, "lon": 105.0697,
             "note": "Ориентир, координаты приблизительные."},
        ],
    },
    {
        "photo": "sestroretsk",
        "title": "Экотропа «Сестрорецкое болото»",
        "region": "Санкт-Петербург",
        "difficulty": "easy", "days": 1, "season": "any", "terrain": "water",
        "length_km": 3.5,
        "description": (
            "Короткая экологическая тропа по государственному природному заказнику «Сестрорецкое "
            "болото». Большая часть пути проложена по деревянным настилам на сваях, они чередуются с "
            "участками лесной тропы по песчаным дюнам и древним береговым валам. Вдоль маршрута стоят "
            "информационные стенды и смотровые площадки. Источники называют длину от 3 до 3,5 км."
        ),
        "restrictions": (
            "Вход бесплатный. Не сходите с настила и тропы: вокруг топкое болото, отклоняться от "
            "маршрута опасно. В заказнике встречаются гадюки."
        ),
        "source_url": "https://travel.yandex.ru/journal/sestroretsk/",
        "source_checked": CHECKED,
        "surface": "Деревянные настилы на сваях и участки лесной тропы по сухим дюнам",
        "has_steps": 1,
        "rest_points": "Смотровые площадки",
        "places": [
            {"name": "Белоостров (рядом начало тропы)", "lat": 60.15, "lon": 30.0,
             "note": "Ориентир, координаты приблизительные."},
        ],
    },
    {
        "photo": "iremel",
        "title": "Большой Иремель (природный парк «Иремель»)",
        "region": "Республика Башкортостан",
        "difficulty": "medium", "days": 2, "season": "any", "terrain": "mountain",
        "length_km": 25,
        "description": (
            "Вторая по высоте вершина Южного Урала, 1582 м, в центре природного парка «Иремель». "
            "Маршрут от села Тюлюк около 25 км по описанию. Туристические агентства организуют поездки "
            "на внедорожниках до КПП, дальше до вершины около 8 км пешком. В парке обитают медведи: "
            "зимой они спят, летом стараются не встречаться с людьми."
        ),
        "restrictions": (
            "Посетителям разрешено находиться только в туристической зоне и на территории палаточных "
            "лагерей; в остальных зонах парка находиться запрещено. Правила посещения, плату и "
            "регистрацию уточняйте на официальном сайте парка."
        ),
        "source_url": "https://www.sportmaster.ru/media/articles/turisticheskie-pohody-v-gory-urala-vershina-iremel/",
        "source_checked": CHECKED,
        "places": [
            {"name": "Большой Иремель (вершина, 1582 м)", "lat": 54.52, "lon": 58.84,
             "note": "Ориентир, координаты приблизительные."},
        ],
    },
]

DEFAULTS = {
    "restrictions": None, "source_url": None, "source_checked": None, "open_from": None,
    "open_to": None, "surface": None, "max_slope": None, "has_steps": 0, "rest_points": None,
}


def remove_route_images(route_id):
    for f in glob.glob(os.path.join(ROUTE_IMG_DIR, f"{route_id}.*")):
        os.remove(f)


def copy_cover(route_id, key):
    """Копирует seed_photos/<key>.jpg в static/img/routes/<номер маршрута>.jpg."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        src = os.path.join(PHOTO_DIR, f"{key}.{ext}")
        if os.path.exists(src):
            os.makedirs(ROUTE_IMG_DIR, exist_ok=True)
            shutil.copyfile(src, os.path.join(ROUTE_IMG_DIR, f"{route_id}.{ext}"))
            return True
    print(f"  нет фото seed_photos/{key}.jpg (будет заглушка)")
    return False


with app.app_context():
    db = get_db()

    # Снаряжение
    db.execute("DELETE FROM gear_items")
    db.executemany(
        "INSERT INTO gear_items (name, category, season, terrain, min_days) VALUES (?, ?, ?, ?, ?)",
        GEAR,
    )

    # Автор маршрутов
    user = db.execute("SELECT id FROM users WHERE username = ?", (OWNER,)).fetchone()
    if user is not None:
        author_id = user["id"]
    elif OWNER == "catalog":
        author_id = db.execute(
            "INSERT INTO users (username, password_hash) VALUES ('catalog', ?)",
            (generate_password_hash(secrets.token_urlsafe(32)),),
        ).lastrowid
    else:
        sys.exit(f"Пользователь «{OWNER}» не найден. Сначала зарегистрируйтесь на сайте.")

    # Повторный запуск заменяет только эти маршруты (по названию), остальные не трогает
    for r in ROUTES:
        for row in db.execute("SELECT id FROM routes WHERE author_id = ? AND title = ?",
                              (author_id, r["title"])).fetchall():
            remove_route_images(row["id"])
            db.execute("DELETE FROM routes WHERE id = ?", (row["id"],))

    for idx, r in enumerate(ROUTES):
        data = {**DEFAULTS, **r, "author_id": author_id, "is_public": 1,
                "views": (len(ROUTES) - idx) * 42}
        cur = db.execute(
            """INSERT INTO routes
               (author_id, title, region, length_km, difficulty, days, season, terrain,
                description, restrictions, source_url, source_checked, open_from, open_to,
                is_public, surface, max_slope, has_steps, rest_points, views)
               VALUES (:author_id, :title, :region, :length_km, :difficulty, :days, :season,
                :terrain, :description, :restrictions, :source_url, :source_checked, :open_from,
                :open_to, :is_public, :surface, :max_slope, :has_steps, :rest_points, :views)""",
            data,
        )
        route_id = cur.lastrowid
        db.executemany(
            "INSERT INTO route_points (route_id, position, kind, lat, lon, name, note) "
            "VALUES (?, ?, 'place', ?, ?, ?, ?)",
            [(route_id, i, p["lat"], p["lon"], p["name"], p.get("note"))
             for i, p in enumerate(r.get("places", []))],
        )
        copy_cover(route_id, r.get("photo"))
    db.commit()
    print("Готово: снаряжение", len(GEAR), "шт., маршрутов", len(ROUTES))