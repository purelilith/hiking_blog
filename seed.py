import secrets

from werkzeug.security import generate_password_hash

from app import app
from db import get_db
from views.routes import path_length_km

# (название, категория, сезон, местность, минимум дней)
# сезон: any / summer / winter / spring_autumn
# местность: any / forest / mountain / city / water
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

# Реальные маршруты по шаблону (данные только из проверенных источников!).
ROUTES = [
    # {
    #     "title": "...", "region": "...", "difficulty": "easy",   # easy / medium / hard
    #     "days": 1, "season": "any", "terrain": "city",
    #     "description": "...", "restrictions": "...", "source_url": "https://...",
    #     "source_checked": "2026-11-17", "open_from": None, "open_to": None,
    #     "surface": "...", "max_slope": "...", "has_steps": 0, "rest_points": "...",
    #     "points": [[55.75, 37.62], [55.76, 37.63]],
    # },
]

DEFAULTS = {"restrictions": None, "source_url": None, "source_checked": None,
            "open_from": None, "open_to": None, "surface": None, "max_slope": None,
            "has_steps": 0, "rest_points": None}

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
    for r in ROUTES:
        data = {**DEFAULTS, **r, "author_id": author_id,
                "length_km": path_length_km(r["points"]), "is_public": 1}
        cur = db.execute(
            """INSERT INTO routes
               (author_id, title, region, length_km, difficulty, days, season, terrain,
                description, restrictions, source_url, source_checked, open_from, open_to,
                is_public, surface, max_slope, has_steps, rest_points)
               VALUES (:author_id, :title, :region, :length_km, :difficulty, :days, :season,
                :terrain, :description, :restrictions, :source_url, :source_checked, :open_from,
                :open_to, :is_public, :surface, :max_slope, :has_steps, :rest_points)""",
            data,
        )
        db.executemany(
            "INSERT INTO route_points (route_id, position, lat, lon) VALUES (?, ?, ?, ?)",
            [(cur.lastrowid, i, lat, lon) for i, (lat, lon) in enumerate(r["points"])],
        )
    db.commit()
    print("Готово: снаряжение", len(GEAR), "шт., маршрутов каталога", len(ROUTES))

