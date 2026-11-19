import secrets
from werkzeug.security import generate_password_hash
from app import app
from db import get_db
from views.routes import path_length_km

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

ROUTES = [
    {
        "title": "Большая Валдайская тропа",
        "region": "Новгородская область",
        "difficulty": "medium",
        "days": 4,
        "season": "spring_autumn",
        "terrain": "forest",
        "description": "Живописный лесной и озёрный маршрут по территории Валдайского национального парка. Тропа оборудована деревянными настилами, смотровыми площадками, информационными стендами и обустроенными стоянками у воды.",
        "restrictions": "Требуется разрешение на посещение национального парка «Валдайский».",
        "source_url": "https://valdaypark.ru",
        "source_checked": "2026-10-15",
        "open_from": "2026-05-01",
        "open_to": "2026-11-01",
        "surface": "Лесная тропа, деревянные настилы, грунт",
        "max_slope": "Умеренный (до 12°)",
        "has_steps": 1,
        "rest_points": "Оборудованные базовые лагеря с беседками и настилами каждые 10–12 км",
        "points": [[57.9742, 33.2528], [58.0215, 33.2890], [58.0890, 33.3412], [58.1520, 33.3980], [58.2105, 33.4310]],
    },
    {
        "title": "Большая Байкальская тропа: Листвянка — Большие Коты",
        "region": "Иркутская область",
        "difficulty": "medium",
        "days": 2,
        "season": "summer",
        "terrain": "mountain",
        "description": "Классический участок вдоль берега Байкала через Прибайкальский национальный парк. Маршрут сочетает лесной серпантин с панорамными видами на озеро и скальные прижимы.",
        "restrictions": "Оформление пропуска в ФГБУ «Заповедное Прибайкалье».",
        "source_url": "https://baikaltrail.org",
        "source_checked": "2026-09-20",
        "open_from": "2026-05-15",
        "open_to": "2026-10-15",
        "surface": "Утоптанный грунт, каменистые участки",
        "max_slope": "Крутой подъём на перевал Скрипер (до 20°)",
        "has_steps": 1,
        "rest_points": "Смотровые площадки и оборудованные стоянки в пади Сенная",
        "points": [[51.8552, 104.8891], [51.8790, 104.9450], [51.9035, 105.0642]],
    },
    {
        "title": "Экотропа «Сестрорецкое болото»",
        "region": "Санкт-Петербург",
        "difficulty": "easy",
        "days": 1,
        "season": "any",
        "terrain": "water",
        "description": "Доступный кольцевой маршрут по верховому болоту с широкими деревянными настилами. Отлично подходит для спокойной прогулки выходного дня всей семьёй и наблюдения за птицами.",
        "restrictions": "Запрещён сход с деревянных настилов и разведение костров.",
        "source_url": "https://oopt.spb.ru",
        "source_checked": "2026-11-01",
        "open_from": None,
        "open_to": None,
        "surface": "Ровный деревянный настил и утрамбованная лесная дорожка",
        "max_slope": "Пологий (до 3°)",
        "has_steps": 0,
        "rest_points": "Смотровые вышки, скамейки вдоль настила каждые 500 метров",
        "points": [[60.1235, 29.9942], [60.1289, 30.0021], [60.1320, 30.0095], [60.1245, 29.9960]],
    },
    {
        "title": "Восхождение на гору Большой Иремель",
        "region": "Республика Башкортостан",
        "difficulty": "hard",
        "days": 2,
        "season": "summer",
        "terrain": "mountain",
        "description": "Маршрут на вторую по высоте вершину Южного Урала через тайгу, зону криволесья и обширные курумники на предвершинном плато.",
        "restrictions": "Регистрация на КПП природного парка «Иремель».",
        "source_url": "https://iremel-park.ru",
        "source_checked": "2026-08-18",
        "open_from": None,
        "open_to": None,
        "surface": "Лесная дорога, корни, крупный курумник",
        "max_slope": "Крутой (до 28° на финальном взлёте)",
        "has_steps": 0,
        "rest_points": "Оборудованные стоянки у подножия и на границе леса",
        "points": [[54.4810, 58.7720], [54.5025, 58.8110], [54.5198, 58.8425]],
    },
]

DEFAULTS = {
    "restrictions": None, "source_url": None, "source_checked": None,
    "open_from": None, "open_to": None, "surface": None, "max_slope": None,
    "has_steps": 0, "rest_points": None,
}

with app.app_context():
    db = get_db()
    db.execute("DELETE FROM gear_items")
    db.executemany(
        "INSERT INTO gear_items (name, category, season, terrain, min_days) VALUES (?, ?, ?, ?, ?)",
        GEAR,
    )

    user = db.execute("SELECT id FROM users WHERE username = 'catalog'").fetchone()
    if user is None:
        author_id = db.execute(
            "INSERT INTO users (username, password_hash) VALUES ('catalog', ?)",
            (generate_password_hash(secrets.token_urlsafe(32)),),
        ).lastrowid
    else:
        author_id = user["id"]

    db.execute("DELETE FROM routes WHERE author_id = ?", (author_id,))
    for idx, r in enumerate(ROUTES):
        data = {
            **DEFAULTS, **r, "author_id": author_id,
            "length_km": path_length_km(r["points"]), "is_public": 1,
        }
        cur = db.execute(
            """INSERT INTO routes
               (author_id, title, region, length_km, difficulty, days, season, terrain,
                description, restrictions, source_url, source_checked, open_from, open_to,
                is_public, surface, max_slope, has_steps, rest_points, views)
               VALUES (:author_id, :title, :region, :length_km, :difficulty, :days, :season,
                :terrain, :description, :restrictions, :source_url, :source_checked, :open_from,
                :open_to, :is_public, :surface, :max_slope, :has_steps, :rest_points, :views)""",
            {**data, "views": (len(ROUTES) - idx) * 42},
        )
        db.executemany(
            "INSERT INTO route_points (route_id, position, lat, lon) VALUES (?, ?, ?, ?)",
            [(cur.lastrowid, i, lat, lon) for i, (lat, lon) in enumerate(r["points"])],
        )
    db.commit()
    print("Готово: снаряжение", len(GEAR), "шт., маршрутов каталога", len(ROUTES))
