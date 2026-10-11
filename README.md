# FinanceHub
#### Video Demo: TODO - Add YouTube video URL

#### Description:

FinanceHub is a personal finance management web application developed as the final project for Harvard University's CS50x 2026.

The application helps users organize their financial activities by recording income and expenses, tracking their balance, reviewing transaction history, and analyzing financial data through interactive charts and annual reports.

FinanceHub was built using Python, Flask, SQLite, HTML, CSS, JavaScript, Bootstrap, and Chart.js.

The main goal of this project is to provide a simple, organized, and intuitive platform for personal financial management while applying the programming concepts learned throughout CS50.

## Features

### User Authentication

FinanceHub provides an authentication system that allows users to:

- Create an account with a username, email, and password.
- Log in securely.
- Log out of their account.
- Access their own financial information.

Passwords are stored using secure password hashes rather than plain text.

### Financial Dashboard

The dashboard provides an overview of the user's financial situation.

It displays:

- Total income.
- Total expenses.
- Financial balance.
- Income and expense comparison chart.
- Expense distribution by category.

Users can filter the dashboard by month and year or view all recorded periods.

### Transaction Management

Authenticated users can:

- Register income.
- Register expenses.
- Select transaction categories.
- Add descriptions.
- Enter monetary amounts.
- Choose transaction dates.
- Edit existing transactions.
- Delete transactions.

Each transaction belongs to a specific user, preventing other users from accessing or modifying it through the application.

### Transaction History

FinanceHub includes a transaction history page with filters for:

- Description.
- Transaction type.
- Category.
- Month.
- Year.

These filters help users find specific financial records.

### Financial Reports

The reports page provides an annual overview of financial activity.

Users can analyze:

- Monthly income.
- Monthly expenses.
- Monthly balances.
- Annual income.
- Annual expenses.
- Annual balance.

The reports use interactive charts to make financial information easier to understand.

### CSV Export

Users can export their transaction records to a CSV file.

This allows financial data to be opened in spreadsheet applications for additional analysis or personal recordkeeping.

## Technologies Used

- **Python:** Backend application logic.
- **Flask:** Web framework and request handling.
- **SQLite:** Relational database.
- **CS50 SQL Library:** Database interaction.
- **HTML:** Web page structure.
- **CSS:** Custom styling.
- **JavaScript:** Interactive frontend functionality.
- **Bootstrap 5:** Responsive interface components.
- **Bootstrap Icons:** Interface icons.
- **Chart.js:** Financial charts and visualizations.
- **Flask-WTF:** CSRF protection.
- **Werkzeug:** Password hashing and verification.

## Project Structure

```text
financehub/
├── app.py
├── financehub.db
├── requirements.txt
├── README.md
├── static/
│   └── styles.css
└── templates/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── transaction.html
    ├── history.html
    ├── edit.html
    └── reports.html
```

The SQLite database is stored locally and is excluded from version control.

## File Descriptions

### app.py

This is the main application file.

It contains Flask configuration, database access, authentication, transaction management, dashboard calculations, history filters, annual reports, and CSV export functionality.

It also implements input validation, password verification, session management, and CSRF protection.

### templates/

This directory contains the HTML templates rendered by Flask.

- `index.html`: Financial dashboard.
- `login.html`: User login page.
- `register.html`: Account registration page.
- `transaction.html`: Transaction creation form.
- `history.html`: Transaction history and filters.
- `edit.html`: Transaction editing form.
- `reports.html`: Annual financial reports.

### static/styles.css

This file contains the application's custom CSS styling.

It defines visual elements used throughout the interface and complements the Bootstrap framework.

### financehub.db

This SQLite database stores user accounts and financial transactions.

The application uses separate tables for users and transactions, with each transaction associated with its owner.

### requirements.txt

This file lists the Python dependencies needed to run the application.

## Database Design

FinanceHub uses two main database tables.

### Users

The users table stores account information, including:

- User ID.
- Username.
- Email.
- Password hash.
- Account creation date.

### Transactions

The transactions table stores financial records, including:

- Transaction ID.
- User ID.
- Transaction type.
- Category.
- Description.
- Amount.
- Transaction date.
- Creation timestamp.

The relationship between users and transactions allows each account to maintain an independent financial history.

## Security

FinanceHub includes several security measures:

- Password hashing.
- Authentication requirements for private routes.
- User-specific database queries.
- CSRF protection for POST forms.
- Server-side input validation.
- Environment-based Flask secret key configuration.
- Parameterized SQL queries.

The SQLite database and environment files are excluded from Git version control.

## How to Run

1. Clone the repository:

```bash
git clone https://github.com/henriquemegre/FinanceHub.git
```

2. Enter the project directory:

```bash
cd FinanceHub
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Configure a secret key:

```bash
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
```

5. Initialize the SQLite database using schema.sql:

    python -m sqlite3 financehub.db ".read schema.sql"


6. Start the Flask application:

```bash
flask run
```

7. Open the local address provided by Flask.

## Design Decisions

One important design decision was to separate financial records by user ID. This allows multiple accounts to use the application without mixing their transaction histories.

Another decision was to store a transaction date separately from the creation timestamp. This allows users to register past financial activities while preserving the date when each record was created.

SQLite was selected because it provides a lightweight relational database suitable for the project's scope.

Flask was selected because its routing and template system made it possible to organize the backend while maintaining a clear separation between application logic and frontend presentation.

Chart.js was used to transform transaction data into visual financial reports.

Bootstrap was used to create a responsive interface, while custom CSS provides the application's visual identity.

## Future Improvements

Possible future improvements include:

- Recurring transactions.
- Monthly budgets.
- Financial goals.
- Password recovery.
- Additional report filters.
- More export formats.
- Automated tests.
- Cloud deployment.

## Author

Developed by Henrique Megre.

Final Project - CS50x 2026.
