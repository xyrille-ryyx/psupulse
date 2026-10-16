# PSU Pulse

Weekly student feedback → text mining and sentiment analysis → trend dashboards, alerts and weekly reports.

Built with Flask + MySQL (XAMPP). Sentiment analysis uses a **lightweight lexicon- and rule-based
model** for English, Filipino and Taglish, written in plain Python. There are no heavy ML libraries
or model downloads, and it runs instantly on any laptop.

## Setup (Windows + XAMPP)

1. Start **MySQL** in the XAMPP Control Panel.
2. In this folder:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Check `.env` (DB_USER / DB_PASSWORD / DB_NAME). XAMPP's default is `root` with no password.
4. Create the database, either way:
   - **phpMyAdmin:** open http://localhost/phpmyadmin → **Import** → choose `database\psupulse.sql` → **Go**
     (creates the `psupulse` database, its tables and the `admin / admin12345` account), or
   - **Script:** `python scripts\init_db.py`

   Optional demo data (synthetic comments): `python scripts\seed_data.py --reset`
5. Run: `python run.py` and open http://127.0.0.1:5000

Demo logins (after seeding): `admin / admin12345`, and `osa.reyes`, `head.it`, `faculty.cruz`,
`student01` … `student45`, all with the password `password123`.

## Weekly flow (Section 4.2)

Admin opens the week's window → students submit anonymous comments on their courses, or on a
transaction at a university office (Cashier, Registrar, ...; offices are managed under Admin → Units) → admin clicks **Close & process**
on the Admin overview → comments are classified and grouped by topic →
results are aggregated by week and unit → alerts are raised → the weekly report is generated →
staff review trends and record the action taken on each alert.

## Folder map

| Path | Architecture component |
|---|---|
| `app/routes/feedback.py` | Feedback Collection Module |
| `app/ml/` | Sentiment Analysis Engine + Topic Grouping (preprocess, lexicon, sentiment, topics, keywords, evaluation) |
| `app/utils/processing.py` | Aggregation and Trend Service + Alerting Module |
| `app/routes/dashboard.py`, `app/routes/reports.py`, `app/utils/reports.py` | Dashboard and Report Module |
| `app/routes/alerts.py` | Alert follow-up (action taken and tracked) |
| `app/routes/auth.py`, `app/utils/decorators.py`, `app/utils/scope.py` | Access Control Module |
| `app/utils/privacy.py` | Anonymization (PII filter, one-way submission token) |
| `app/routes/admin.py` | Users, units, windows, settings, change log (Phase G/H), analyzer lab |
| `app/models/` | Data architecture (Section 4.3.2) |
| `database/psupulse.sql` | **Import this in phpMyAdmin**: creates the `psupulse` database, all tables and the admin account |

## Scripts

| Script | Purpose |
|---|---|
| `init_db.py [--reset]` | Create the MySQL database, tables and the first admin |
| `seed_data.py [--reset]` | Demo units, users, 6 weeks of synthetic comments |
| `export_schema.py` | Regenerate `database/psupulse.sql` after changing the models (new columns on existing tables also go in `app/models/upgrades.py`) |

## Evaluation (Chapter 5.2)

Label at least 300 real comments in a CSV with columns `text,label,annotator_2`, then upload the file
in **Admin → Analyzer lab** to get accuracy, precision, recall, F1 and the confusion matrix.
`database/sample_labeled_feedback.csv` is a small sample for testing only. Don't report results from it.
