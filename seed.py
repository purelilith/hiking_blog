"""Начальные данные: чек-лист снаряжения и проверенные маршруты.

Запуск (после `flask --app app init-db`):
    python seed.py [ИМЯ]

Маршруты берутся из seed_data.json (его создаёт export_routes.py), обложки из seed_photos/routeN.jpg.
У каждого маршрута есть линия на карте ("points") и названные места ("places").
Автор маршрутов: пользователь ИМЯ (он должен уже существовать, чтобы вы могли править маршруты
на сайте) или, если имя не указано, служебный пользователь DEFAULT_OWNER со случайным паролем:
войти под ним нельзя, а маршруты видят все, в том числе неавторизованные посетители.
Повторный запуск безопасен: маршруты с теми же названиями у того же автора заменяются.
"""
import glob
import json
import os
import secrets
import shutil
import sys

from werkzeug.security import generate_password_hash

# Windows-консоль в старой кодировке не должна ронять скрипт из-за символов вроде «—»
try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass

from app import app
from db import get_db

# Под этим именем в каталоге будут показаны маршруты, если запустить `python seed.py` без имени.
# Можно заменить на свой ник (3–32 символа: буквы, цифры, «.», «_», «-»).
DEFAULT_OWNER = "catalog"

# Паспорт доступности. Значения подставляются, только если в seed_data.json поле пустое
# (так данные не теряются, даже если файл выгрузили с пустыми полями). Ключ — название маршрута.
# Здесь только то, что известно из источников; чего нет, лучше оставить пустым, чем придумать.
PASSPORT = {
    'Большая Валдайская тропа (центральный участок)': {
        "rest_points": "Оборудованные стоянки через каждые 12–14 км",
    },
    'Большая Байкальская тропа: Листвянка — Большие Коты': {
        "surface": "Грунтовая тропа; бывает скользкой, особенно после заморозков",
        "max_slope": "Долгий подъём (около 3,5 км) в начале маршрута",
    },
    'Экотропа «Сестрорецкое болото»': {
        "surface": "Деревянные настилы на сваях и участки лесной тропы по сухим дюнам",
        "has_steps": 1,
        "rest_points": "Смотровые площадки",
    },
    'Большой Иремель (природный парк «Иремель»)': {
        "surface": "Лесная тропа, выше горная тундра; на подъёме курумник (каменная россыпь), "
                   "камни помечены краской",
        "max_slope": "Самый трудный участок: подъём по курумнику к вершине; "
                     "цифры уклона в источниках не указаны",
        "has_steps": 1,  # ступеней нет, но камни и россыпь делают путь непригодным для «без ступенек»
        "rest_points": "Кордон (КПП) природного парка перед пешим подъёмом; "
                       "обустроенные места отдыха на тропе в источниках не названы",
    },
}

# Снаряжение: (название, категория, сезон, местность, с какого числа дней нужно)
# Сезон и местность 'any' значат «подходит всегда»
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

# ---- Пути и настройки ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "seed_data.json")
PHOTO_DIR = os.path.join(BASE_DIR, "seed_photos")
ROUTE_IMG_DIR = os.path.join(BASE_DIR, "static", "img", "routes")
OWNER = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OWNER

REQUIRED = ("title", "region", "length_km", "difficulty", "description")
DIFFICULTIES = ("easy", "medium", "hard")

# Значения для полей, которых нет в seed_data.json
DEFAULTS = {
    "days": 1, "season": "any", "terrain": "any",
    "restrictions": None, "source_url": None, "source_checked": None,
    "open_from": None, "open_to": None, "surface": None, "max_slope": None,
    "has_steps": 0, "rest_points": None, "kind": "curated", "is_closed": 0,
}


def load_routes():
    """Читает и проверяет seed_data.json; при ошибке завершает скрипт понятным сообщением."""
    if not os.path.exists(JSON_PATH):
        sys.exit("Не найден seed_data.json. Получите файл из репозитория "
                 "или создайте его командой: python export_routes.py ИМЯ")
    with open(JSON_PATH, encoding="utf-8-sig") as f:
        routes = json.load(f)
    if not isinstance(routes, list) or not routes:
        sys.exit("seed_data.json пуст или имеет неверный формат (ожидается список маршрутов).")
    for i, r in enumerate(routes, 1):
        # Подставляем паспорт доступности в пустые поля
        for field, value in PASSPORT.get(r.get("title"), {}).items():
            if r.get(field) in (None, "", 0):
                r[field] = value
        missing = [k for k in REQUIRED if r.get(k) in (None, "")]
        if missing:
            sys.exit(f"Маршрут №{i}: не заполнены поля {', '.join(missing)}.")
        if r["difficulty"] not in DIFFICULTIES:
            sys.exit(f"Маршрут «{r['title']}»: сложность должна быть одной из {DIFFICULTIES}.")
        if not any(r.get(k) for k in ("surface", "max_slope", "rest_points")):
            print(f"  ! у маршрута «{r['title']}» не заполнен паспорт доступности")
        if len(r.get("points", [])) < 2:
            print(f"  ! у маршрута «{r['title']}» меньше двух точек линии: на карте не будет пути")
    return routes


def find_cover(key):
    """Путь к seed_photos/<key>.(jpg|jpeg|png|webp) или None."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        path = os.path.join(PHOTO_DIR, f"{key}.{ext}")
        if key and os.path.exists(path):
            return path
    return None


def remove_route_images(route_id):
    """Удаляет обложки маршрута из static/img/routes (в том числе забытые от старых запусков)."""
    for f in glob.glob(os.path.join(ROUTE_IMG_DIR, f"{route_id}.*")):
        os.remove(f)


def copy_cover(route_id, key):
    """Копирует обложку в static/img/routes/<номер маршрута>.<расширение>."""
    src = find_cover(key)
    if src is None:
        print(f"  ! нет файла seed_photos/{key}.jpg: у маршрута будет заглушка")
        return
    os.makedirs(ROUTE_IMG_DIR, exist_ok=True)
    remove_route_images(route_id)
    shutil.copyfile(src, os.path.join(ROUTE_IMG_DIR, f"{route_id}{os.path.splitext(src)[1]}"))


ROUTES = load_routes()

with app.app_context():
    db = get_db()

    # База должна быть создана заранее
    has_tables = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'routes'").fetchone()
    if has_tables is None:
        sys.exit("База не создана. Сначала выполните: flask --app app init-db")

    # Автор маршрутов: существующий пользователь или служебный (создаётся при необходимости)
    user = db.execute("SELECT id FROM users WHERE username = ?", (OWNER,)).fetchone()
    if user is not None:
        author_id = user["id"]
    elif OWNER == DEFAULT_OWNER:
        author_id = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (DEFAULT_OWNER, generate_password_hash(secrets.token_urlsafe(32))),
        ).lastrowid
    else:
        sys.exit(f"Пользователь «{OWNER}» не найден. Сначала зарегистрируйтесь на сайте "
                 f"или запустите без имени (автор будет «{DEFAULT_OWNER}»).")

    try:
        # Снаряжение: список заменяется целиком
        db.execute("DELETE FROM gear_items")
        db.executemany(
            "INSERT INTO gear_items (name, category, season, terrain, min_days) "
            "VALUES (?, ?, ?, ?, ?)", GEAR)

        # Повторный запуск заменяет только эти маршруты (по названию), остальные не трогает
        for r in ROUTES:
            for row in db.execute("SELECT id FROM routes WHERE author_id = ? AND title = ?",
                                  (author_id, r["title"])).fetchall():
                remove_route_images(row["id"])
                db.execute("DELETE FROM routes WHERE id = ?", (row["id"],))  # точки и фото уйдут каскадом

        covers = []  # (id маршрута, ключ обложки): копируем файлы только после успешной записи в базу
        for idx, r in enumerate(ROUTES):
            # Просмотры по убыванию, чтобы на главной порядок совпадал с порядком в файле
            data = {**DEFAULTS, **r, "author_id": author_id, "is_public": 1,
                    "views": (len(ROUTES) - idx) * 42}
            route_id = db.execute(
                """INSERT INTO routes
                   (author_id, title, region, length_km, difficulty, days, season, terrain,
                    description, restrictions, source_url, source_checked, open_from, open_to,
                    is_public, surface, max_slope, has_steps, rest_points, views, kind, is_closed)
                   VALUES (:author_id, :title, :region, :length_km, :difficulty, :days, :season,
                    :terrain, :description, :restrictions, :source_url, :source_checked,
                    :open_from, :open_to, :is_public, :surface, :max_slope, :has_steps,
                    :rest_points, :views, :kind, :is_closed)""",
                data,
            ).lastrowid

            # Линия маршрута (path) и названные места (place)
            db.executemany(
                "INSERT INTO route_points (route_id, position, kind, lat, lon) "
                "VALUES (?, ?, 'path', ?, ?)",
                [(route_id, i, lat, lon) for i, (lat, lon) in enumerate(r.get("points", []))],
            )
            db.executemany(
                "INSERT INTO route_points (route_id, position, kind, lat, lon, name, note) "
                "VALUES (?, ?, 'place', ?, ?, ?, ?)",
                [(route_id, i, p["lat"], p["lon"], p["name"], p.get("note"))
                 for i, p in enumerate(r.get("places", []))],
            )
            covers.append((route_id, r.get("photo")))
            print(f"  + {r['title']}: линия {len(r.get('points', []))} т., "
                  f"мест {len(r.get('places', []))}")
        db.commit()
    except Exception:
        db.rollback()  # при ошибке в базе не остаётся половины данных
        raise

    for route_id, key in covers:
        copy_cover(route_id, key)
    print(f"Готово: снаряжение {len(GEAR)} шт., маршрутов {len(ROUTES)}, автор «{OWNER}».")