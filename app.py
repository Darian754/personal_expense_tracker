from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'expenses.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db = SQLAlchemy(app)

# Define Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))

# Create the database tables
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Get form data
        date = request.form["date"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        description = request.form["description"]

        # Save to database
        new_expense = Expense(date=date, category=category, amount=amount, description=description)
        db.session.add(new_expense)
        db.session.commit()

    # Fetch all expenses from database
    expenses = Expense.query.all()
    return render_template("index.html", expenses=expenses)

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    # Find the expense by ID
    expense = Expense.query.get_or_404(expense_id)

    if request.method == "POST":
        # Get updated form data
        expense.date = request.form["date"]
        expense.category = request.form["category"]
        expense.amount = float(request.form["amount"])
        expense.description = request.form["description"]

        # Save changes
        db.session.commit()

        # Redirect back to home
        return redirect("/")

    return render_template("edit.html", expense=expense)


if __name__ == "__main__":
    app.run(debug=True)
