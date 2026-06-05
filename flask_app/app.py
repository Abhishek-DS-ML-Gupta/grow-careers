from flask import Flask, render_template, redirect, url_for
import sqlite3
import os


def get_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')


def get_objects():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.name, o.category, o.market_value_inr, o.is_active,
               p.id as plan_id, p.name as plan_name, p.price_inr, p.validity_days,
               p.total_income_inr, p.daily_income_inr, p.is_limited, p.is_active as plan_active
        FROM plans_tradeobject o
        LEFT JOIN plans_investmentplan p ON p.object_id = o.id AND p.is_active = 1
        WHERE o.is_active = 1
        ORDER BY o.id DESC, p.`order` ASC, p.name ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    objects = {}
    for row in rows:
        obj_id = row['id']
        if obj_id not in objects:
            objects[obj_id] = {
                'id': obj_id,
                'name': row['name'],
                'category': row['category'],
                'market_value_inr': row['market_value_inr'],
                'plans': [],
            }
        if row['plan_id']:
            objects[obj_id]['plans'].append({
                'id': row['plan_id'],
                'name': row['plan_name'],
                'price_inr': row['price_inr'],
                'validity_days': row['validity_days'],
                'total_income_inr': row['total_income_inr'],
                'daily_income_inr': row['daily_income_inr'],
                'is_limited': bool(row['is_limited']),
                'is_active': row['plan_active'],
            })
    return list(objects.values())


def create_app():
    app = Flask(__name__)
    app.secret_key = 'flask-demo-secret-key-change-in-production'

    @app.route('/')
    def index():
        objects = get_objects()
        return render_template('flask_grid.html', objects=objects)

    @app.route('/coming-soon')
    def coming_soon():
        return redirect(url_for('index'))

    return app


app = create_app()

if __name__ == '__main__':
    app.run(port=5001, debug=True)
