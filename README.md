# EcoBuild

**EcoBuild: AI-Based Building Energy Efficiency Analysis System**

> *Design Smarter. Compare Before You Build.*

EcoBuild is an academic decision-support prototype that uses machine learning to estimate building heating and cooling loads and allows users to explore building configurations through What-If Analysis.

## Technology Stack

- **Backend:** Python 3.13, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Frontend:** Bootstrap 5, HTML5, CSS3, Vanilla JavaScript
- **ML:** scikit-learn (GradientBoostingRegressor), Pandas, NumPy, Joblib
- **Database:** SQLite (dev) / PostgreSQL-ready (production)
- **Dataset:** UCI Energy Efficiency dataset (ENB2012)

## Quick Start

```bash
# 1. Clone and enter directory
cd EcoBuild

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
copy .env.example .env
# Edit .env and set a real SECRET_KEY

# 5. Initialize database
flask db init
flask db migrate -m "initial schema"
flask db upgrade

# 6. Run development server
flask run
```

Visit http://localhost:5000

## Project Structure

```
EcoBuild/
├── app.py               # Flask application factory
├── config.py            # Configuration (dev/prod)
├── requirements.txt
├── .env.example
├── README.md
├── dataset/             # ENB2012_data.xlsx
├── ml/                  # train_model.py, evaluate_model.py
├── models/              # Trained .joblib models + JSON metadata
├── plots/               # Generated training plots
├── templates/           # Jinja2 HTML templates
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── migrations/          # Flask-Migrate/Alembic
```

## Disclaimer

EcoBuild is an academic decision-support prototype. Predictions are estimates based on benchmark data and are not professional engineering certification or guaranteed real-world energy consumption.
