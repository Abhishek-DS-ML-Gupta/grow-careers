# ObjectTrade Demo

A Django + Flask demo project inspired by object trading plan UIs.  
**Educational use only. No real money, payments, wallets, or investments.**

## Stack

- **Backend A**: Django 5.x (main site, auth, admin, plans)
- **Backend B**: Flask (plan display page, reads same SQLite DB)
- **Styling**: Tailwind CSS (milky blue modern theme)
- **Database**: SQLite (via Django ORM)

## Features

- Trade objects: Vehicle, Property, Electronics, Other
- Admin-managed plans per object (price, validity, total income, daily income)
- User register/login
- User dashboard showing investments
- Invest flow (demo only)
- Flask mirror page on port 5001

## Project Structure

```
grow_demo/
├── manage.py
├── db.sqlite3
├── grow_demo/
│   ├── settings.py
│   └── urls.py
├── plans/
│   ├── models.py
│   ├── admin.py
│   ├── views.py
│   ├── serializers.py
│   └── templates/plans/
│       ├── base.html
│       ├── grid.html
│       ├── login.html
│       ├── signup.html
│       ├── dashboard.html
│       ├── invest.html
│       └── coming_soon.html
├── flask_app/
│   ├── app.py
│   └── templates/flask_grid.html
└── templates/
    └── base.html
```

## Run

```bash
# Django
cd C:\Users\Admin\Desktop\traderound\grow_demo
python manage.py runserver 8000

# Flask
python flask_app/app.py
```

## URLs

- `http://127.0.0.1:8000/plan/` - Plans page
- `http://127.0.0.1:8000/dashboard/` - User dashboard
- `http://127.0.0.1:8000/admin/` - Admin panel
- `http://127.0.0.1:5001/` - Flask mirror

## Seed Data

Run in Django shell:

```bash
python manage.py shell
```

```python
from plans.models import TradeObject, InvestmentPlan

car = TradeObject.objects.create(name='Toyota Camry 2024', category='vehicle', market_value_inr=2500000)
house = TradeObject.objects.create(name='2BHK Flat Mumbai', category='property', market_value_inr=8500000)
laptop = TradeObject.objects.create(name='MacBook Pro M3', category='electronics', market_value_inr=180000)

plans = [
    (car, [('Basic', 50000, 30, 65000, 2167), ('Premium', 100000, 45, 140000, 3111)]),
    (house, [('Starter', 500000, 60, 750000, 12500), ('Growth', 1000000, 90, 1600000, 17777)]),
    (laptop, [('Lite', 10000, 15, 13000, 866), ('Pro', 25000, 30, 35000, 1166)]),
]

for obj, obj_plans in plans:
    for idx, (name, price, validity, total, daily) in enumerate(obj_plans, start=1):
        InvestmentPlan.objects.create(object=obj, name=name, price_inr=price, validity_days=validity, total_income_inr=total, daily_income_inr=daily, order=idx)
```

## Disclaimer

This is a demo/learning project.  
No real investments, payments, or returns.  
Not affiliated with any real trading platform.
