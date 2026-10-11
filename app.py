import csv
import io
import os

from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from zoneinfo import ZoneInfo

from cs50 import SQL
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "A variável de ambiente SECRET_KEY precisa ser configurada."
    )

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

csrf = CSRFProtect(app)

db = SQL("sqlite:///financehub.db")

BRAZIL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def today_in_brazil():
    """Return today's date in Brazil."""
    return datetime.now(BRAZIL_TIMEZONE).date()


def login_required(f):
    """Require authentication."""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get("user_id"):
            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function


def format_brl(value):
    """Format values as Brazilian currency."""

    formatted = f"{value:,.2f}"

    formatted = formatted.replace(",", "X")
    formatted = formatted.replace(".", ",")
    formatted = formatted.replace("X", ".")

    return f"R$ {formatted}"


def validate_amount(amount_text):
    """Validate a positive monetary amount with at most two decimals."""

    try:
        amount = Decimal(amount_text)
    except (InvalidOperation, ValueError, TypeError):
        return None

    if not amount.is_finite() or amount <= 0:
        return None

    if amount != amount.quantize(Decimal("0.01")):
        return None

    return amount


def validate_transaction_date(date_text):
    """Validate a transaction date in YYYY-MM-DD format."""

    try:
        parsed_date = datetime.strptime(
            date_text, "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return None

    if parsed_date.isoformat() != date_text:
        return None

    return parsed_date


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def index():
    """Display dashboard with financial period filters."""

    if not session.get("user_id"):
        return render_template("index.html")

    now = today_in_brazil()

    selected_month = request.args.get("month", type=str)
    selected_year = request.args.get("year", type=str)

    all_periods = request.args.get("period") == "all"

    if all_periods:

        month = None
        year = None
        period_label = "Todo o período"

    else:

        try:
            month = int(selected_month) if selected_month else now.month
            year = int(selected_year) if selected_year else now.year

            if month < 1 or month > 12:
                raise ValueError

            if year < 2000 or year > 2100:
                raise ValueError

        except ValueError:
            month = now.month
            year = now.year

        month_names = [
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        ]

        period_label = f"{month_names[month - 1]} de {year}"

    if all_periods:

        transactions = db.execute(
            """
            SELECT type, category, amount
            FROM transactions
            WHERE user_id = ?
            """,
            session["user_id"],
        )

    else:

        period_start = f"{year:04d}-{month:02d}-01"

        if month == 12:
            period_end = f"{year + 1:04d}-01-01"
        else:
            period_end = f"{year:04d}-{month + 1:02d}-01"

        transactions = db.execute(
            """
            SELECT type, category, amount
            FROM transactions
            WHERE user_id = ?
              AND transaction_date >= ?
              AND transaction_date < ?
            """,
            session["user_id"],
            period_start,
            period_end,
        )

    income = Decimal("0.00")
    expenses = Decimal("0.00")

    expenses_by_category = {}

    for transaction in transactions:

        amount = Decimal(str(transaction["amount"]))

        if transaction["type"] == "income":
            income += amount

        elif transaction["type"] == "expense":

            expenses += amount

            category = transaction["category"]

            expenses_by_category[category] = (
                expenses_by_category.get(
                    category, Decimal("0.00")
                ) + amount
            )

    balance = income - expenses

    category_labels = list(expenses_by_category.keys())

    category_values = [
        float(expenses_by_category[category])
        for category in category_labels
    ]

    return render_template(
        "index.html",
        balance=format_brl(balance),
        income=format_brl(income),
        expenses=format_brl(expenses),
        chart_income=float(income),
        chart_expenses=float(expenses),
        category_labels=category_labels,
        category_values=category_values,
        selected_month=month,
        selected_year=year,
        all_periods=all_periods,
        period_label=period_label,
        current_year=now.year,
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate user."""

    if request.method == "POST":

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:

            flash("Preencha todos os campos.", "danger")
            return redirect("/login")

        users = db.execute(
            "SELECT * FROM users WHERE username = ?",
            username,
        )

        if len(users) != 1 or not check_password_hash(
            users[0]["password_hash"], password
        ):

            flash("Usuário ou senha incorretos.", "danger")
            return redirect("/login")

        session.clear()

        session["user_id"] = users[0]["id"]
        session["username"] = users[0]["username"]

        flash("Login realizado com sucesso!", "success")

        return redirect("/")

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    """Log user out."""

    session.clear()

    flash("Você saiu da sua conta.", "success")

    return redirect("/login")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user."""

    if request.method == "POST":

        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()

        password = request.form.get("password") or ""
        confirmation = request.form.get("confirmation") or ""

        if not username or not email or not password:

            flash("Preencha todos os campos.", "danger")
            return redirect("/register")

        if password != confirmation:

            flash("As senhas não coincidem.", "danger")
            return redirect("/register")

        if len(password) < 8:

            flash(
                "A senha deve ter pelo menos 8 caracteres.",
                "danger",
            )
            return redirect("/register")

        existing = db.execute(
            """
            SELECT id FROM users
            WHERE username = ? OR email = ?
            """,
            username,
            email,
        )

        if existing:

            flash(
                "Nome de usuário ou e-mail já cadastrado.",
                "danger",
            )
            return redirect("/register")

        password_hash = generate_password_hash(password)

        db.execute(
            """
            INSERT INTO users
            (username, email, password_hash)
            VALUES (?, ?, ?)
            """,
            username,
            email,
            password_hash,
        )

        flash(
            "Conta criada com sucesso! Faça seu login.",
            "success",
        )

        return redirect("/login")

    return render_template("register.html")


# ============================================================
# NEW TRANSACTION
# ============================================================

@app.route("/transaction", methods=["GET", "POST"])
@login_required
def transaction():
    """Register income or expense with a transaction date."""

    if request.method == "POST":

        transaction_type = request.form.get("type")

        category = (
            request.form.get("category") or ""
        ).strip()

        description = (
            request.form.get("description") or ""
        ).strip()

        amount_text = (
            request.form.get("amount") or ""
        ).strip()

        date_text = (
            request.form.get("transaction_date") or ""
        ).strip()

        if transaction_type not in ("income", "expense"):

            flash("Selecione um tipo válido.", "danger")
            return redirect("/transaction")

        if not category or not description:

            flash("Preencha todos os campos.", "danger")
            return redirect("/transaction")

        amount = validate_amount(amount_text)

        if amount is None:

            flash(
                "Digite um valor positivo com até duas casas decimais.",
                "danger",
            )
            return redirect("/transaction")

        transaction_date = validate_transaction_date(date_text)

        if transaction_date is None:

            flash("Selecione uma data válida.", "danger")
            return redirect("/transaction")

        db.execute(
            """
            INSERT INTO transactions
            (
                user_id,
                type,
                category,
                description,
                amount,
                transaction_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            session["user_id"],
            transaction_type,
            category,
            description,
            str(amount),
            transaction_date.isoformat(),
        )

        flash(
            "Movimentação registrada com sucesso!",
            "success",
        )

        return redirect("/")

    return render_template(
        "transaction.html",
        today=today_in_brazil().isoformat(),
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.route("/history")
@login_required
def history():
    """Display transaction history with advanced filters."""

    user_id = session["user_id"]

    search = (request.args.get("search") or "").strip()
    transaction_type = (request.args.get("type") or "").strip()
    category = (request.args.get("category") or "").strip()
    month = (request.args.get("month") or "").strip()
    year = (request.args.get("year") or "").strip()

    if transaction_type not in ("income", "expense"):
        transaction_type = ""

    if month:

        try:
            month_number = int(month)
            month = (
                str(month_number)
                if 1 <= month_number <= 12
                else ""
            )

        except ValueError:
            month = ""

    if year:

        try:
            year_number = int(year)
            year = (
                str(year_number)
                if 2000 <= year_number <= 2100
                else ""
            )

        except ValueError:
            year = ""

    categories_rows = db.execute(
        """
        SELECT DISTINCT category
        FROM transactions
        WHERE user_id = ?
        ORDER BY category
        """,
        user_id,
    )

    categories = [
        row["category"]
        for row in categories_rows
    ]

    years_rows = db.execute(
        """
        SELECT DISTINCT SUBSTR(transaction_date, 1, 4) AS year
        FROM transactions
        WHERE user_id = ?
          AND transaction_date IS NOT NULL
        ORDER BY year DESC
        """,
        user_id,
    )

    years = [
        row["year"]
        for row in years_rows
    ]

    filters = {
        "search": search,
        "type": transaction_type,
        "category": category,
        "month": month,
        "year": year,
    }

    query = """
        SELECT
            id,
            type,
            category,
            description,
            amount,
            created_at,
            transaction_date
        FROM transactions
        WHERE user_id = ?
    """

    parameters = [user_id]

    if search:

        query += " AND LOWER(description) LIKE ?"
        parameters.append(f"%{search.lower()}%")

    if transaction_type:

        query += " AND type = ?"
        parameters.append(transaction_type)

    if category:

        query += " AND category = ?"
        parameters.append(category)

    if month:

        query += " AND SUBSTR(transaction_date, 6, 2) = ?"
        parameters.append(f"{int(month):02d}")

    if year:

        query += " AND SUBSTR(transaction_date, 1, 4) = ?"
        parameters.append(year)

    query += " ORDER BY transaction_date DESC, id DESC"

    transactions = db.execute(query, *parameters)

    for transaction in transactions:

        transaction["formatted_amount"] = format_brl(
            Decimal(str(transaction["amount"]))
        )

    return render_template(
        "history.html",
        transactions=transactions,
        filters=filters,
        categories=categories,
        years=years,
    )


# ============================================================
# DELETE TRANSACTION
# ============================================================

@app.route(
    "/delete/<int:transaction_id>",
    methods=["POST"],
)
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction belonging to the logged-in user."""

    transaction = db.execute(
        """
        SELECT id FROM transactions
        WHERE id = ? AND user_id = ?
        """,
        transaction_id,
        session["user_id"],
    )

    if not transaction:

        flash("Movimentação não encontrada.", "danger")
        return redirect("/history")

    db.execute(
        """
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
        """,
        transaction_id,
        session["user_id"],
    )

    flash(
        "Movimentação excluída com sucesso!",
        "success",
    )

    return redirect("/history")


# ============================================================
# EDIT TRANSACTION
# ============================================================

@app.route(
    "/edit/<int:transaction_id>",
    methods=["GET", "POST"],
)
@login_required
def edit_transaction(transaction_id):
    """Edit a transaction belonging to the logged-in user."""

    transactions = db.execute(
        """
        SELECT
            id,
            type,
            category,
            description,
            amount,
            transaction_date
        FROM transactions
        WHERE id = ? AND user_id = ?
        """,
        transaction_id,
        session["user_id"],
    )

    if not transactions:

        flash("Movimentação não encontrada.", "danger")
        return redirect("/history")

    transaction = transactions[0]

    if request.method == "POST":

        transaction_type = request.form.get("type")

        category = (
            request.form.get("category") or ""
        ).strip()

        description = (
            request.form.get("description") or ""
        ).strip()

        amount_text = (
            request.form.get("amount") or ""
        ).strip()

        date_text = (
            request.form.get("transaction_date") or ""
        ).strip()

        if transaction_type not in ("income", "expense"):

            flash("Selecione um tipo válido.", "danger")
            return redirect(request.path)

        if not category or not description:

            flash("Preencha todos os campos.", "danger")
            return redirect(request.path)

        amount = validate_amount(amount_text)

        if amount is None:

            flash(
                "Digite um valor positivo com até duas casas decimais.",
                "danger",
            )
            return redirect(request.path)

        transaction_date = validate_transaction_date(date_text)

        if transaction_date is None:

            flash("Selecione uma data válida.", "danger")
            return redirect(request.path)

        db.execute(
            """
            UPDATE transactions
            SET
                type = ?,
                category = ?,
                description = ?,
                amount = ?,
                transaction_date = ?
            WHERE id = ? AND user_id = ?
            """,
            transaction_type,
            category,
            description,
            str(amount),
            transaction_date.isoformat(),
            transaction_id,
            session["user_id"],
        )

        flash(
            "Movimentação atualizada com sucesso!",
            "success",
        )

        return redirect("/history")

    return render_template(
        "edit.html",
        transaction=transaction,
    )


# ============================================================
# FINANCIAL REPORTS
# ============================================================

@app.route("/reports")
@login_required
def reports():
    """Display annual financial reports."""

    current_year = today_in_brazil().year

    selected_year = request.args.get("year", type=int)

    if selected_year is None or not 2000 <= selected_year <= 2100:
        selected_year = current_year

    years_rows = db.execute(
        """
        SELECT DISTINCT SUBSTR(transaction_date, 1, 4) AS year
        FROM transactions
        WHERE user_id = ?
          AND transaction_date IS NOT NULL
        ORDER BY year DESC
        """,
        session["user_id"],
    )

    years = sorted(
        {current_year, selected_year}
        | {
            int(row["year"])
            for row in years_rows
            if row["year"]
        },
        reverse=True,
    )

    transactions = db.execute(
        """
        SELECT type, amount, transaction_date
        FROM transactions
        WHERE user_id = ?
          AND transaction_date >= ?
          AND transaction_date < ?
        """,
        session["user_id"],
        f"{selected_year:04d}-01-01",
        f"{selected_year + 1:04d}-01-01",
    )

    monthly_income = [
        Decimal("0.00") for _ in range(12)
    ]

    monthly_expenses = [
        Decimal("0.00") for _ in range(12)
    ]

    for transaction in transactions:

        month_index = (
            int(transaction["transaction_date"][5:7]) - 1
        )

        amount = Decimal(str(transaction["amount"]))

        if transaction["type"] == "income":

            monthly_income[month_index] += amount

        elif transaction["type"] == "expense":

            monthly_expenses[month_index] += amount

    monthly_balance = [
        monthly_income[i] - monthly_expenses[i]
        for i in range(12)
    ]

    total_income = sum(monthly_income)
    total_expenses = sum(monthly_expenses)
    total_balance = total_income - total_expenses

    return render_template(
        "reports.html",
        years=years,
        selected_year=selected_year,
        total_income=format_brl(total_income),
        total_expenses=format_brl(total_expenses),
        total_balance=format_brl(total_balance),
        monthly_income=[
            float(value) for value in monthly_income
        ],
        monthly_expenses=[
            float(value) for value in monthly_expenses
        ],
        monthly_balance=[
            float(value) for value in monthly_balance
        ],
    )


# ============================================================
# CSV EXPORT
# ============================================================

@app.route("/export")
@login_required
def export_transactions():
    """Export the logged-in user's transactions as CSV."""

    transactions = db.execute(
        """
        SELECT
            transaction_date,
            type,
            category,
            description,
            amount
        FROM transactions
        WHERE user_id = ?
        ORDER BY transaction_date DESC, id DESC
        """,
        session["user_id"],
    )

    output = io.StringIO()

    # UTF-8 BOM helps Excel recognize accented characters.
    output.write("\ufeff")

    writer = csv.writer(
        output,
        delimiter=";",
    )

    writer.writerow([
        "Data",
        "Tipo",
        "Categoria",
        "Descrição",
        "Valor (R$)",
    ])

    def safe_csv_cell(value):
        """Prevent spreadsheet formula execution in text fields."""
        text = str(value)

        if text.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + text

        return text

    for transaction in transactions:

        transaction_type = (
            "Receita"
            if transaction["type"] == "income"
            else "Despesa"
        )

        amount = Decimal(str(transaction["amount"]))

        amount_text = (
            f"{amount:.2f}".replace(".", ",")
        )

        writer.writerow([
            transaction["transaction_date"],
            transaction_type,
            safe_csv_cell(transaction["category"]),
            safe_csv_cell(transaction["description"]),
            amount_text,
        ])

    filename = (
        f"financehub_movimentacoes_"
        f"{today_in_brazil().isoformat()}.csv"
    )

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f"attachment; filename={filename}"
            )
        },
    )
