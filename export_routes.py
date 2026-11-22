"""Выгружает проверенные маршруты автора в seed_data.json и копирует обложки в seed_photos/.
Запуск: python export_routes.py ИМЯ   (то же имя, что и в python seed.py ИМЯ)"""
import glob
import json
import os
import shutil
import sys

from app import app
from db import get_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Поля таблицы routes, которые попадают в seed_data.json
FIELDS = ("title", "region", "difficulty", "days", "season", "terrain", "length_km", "description",
          "restrictions", "source_url", "source_checked", "open_from", "open_to", "surface",
          "max_slope", "has_steps", "rest_points", "is_closed")

owner = sys.argv[1] if len(sys.argv) > 1 else "catalog"
with app.app_context():
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE username = ?", (owner,)).fetchone()
    if user is None:
        sys.exit(f"Пользователь «{owner}» не найден.")
    os.makedirs(os.path.join(BASE_DIR, "seed_photos"), exist_ok=True)

    result = []
    # Берём только проверенные (curated) маршруты автора, нумеруем их с единицы
    for n, r in enumerate(db.execute(
            "SELECT * FROM routes WHERE author_id = ? AND kind = 'curated' ORDER BY id",
            (user["id"],)), 1):
        pts = db.execute("SELECT kind, lat, lon, name, note FROM route_points "
                         "WHERE route_id = ? ORDER BY position", (r["id"],)).fetchall()
        item = {k: r[k] for k in FIELDS}
        item["photo"] = f"route{n}"  # имя файла обложки в seed_photos/
        item["points"] = [[p["lat"], p["lon"]] for p in pts if p["kind"] == "path"]
        item["places"] = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "note": p["note"]}
                          for p in pts if p["kind"] == "place"]
        # Копируем обложку маршрута (static/img/routes/<id>.*) в seed_photos/route<n>.*
        for f in glob.glob(os.path.join(BASE_DIR, "static", "img", "routes", f"{r['id']}.*")):
            shutil.copyfile(f, os.path.join(BASE_DIR, "seed_photos",
                                            f"route{n}" + os.path.splitext(f)[1]))
        result.append(item)

    with open(os.path.join(BASE_DIR, "seed_data.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print("Выгружено маршрутов:", len(result))
