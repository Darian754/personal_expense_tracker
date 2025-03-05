from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from math import ceil

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
        date = request.form["date"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        description = request.form["description"]

        new_expense = Expense(date=date, category=category, amount=amount, description=description)
        db.session.add(new_expense)
        db.session.commit()

        return redirect("/")

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category")
    sort_by = request.args.get("sort_by", "date")

    page = request.args.get("page", 1, type=int)
    per_page = 5  # Show 5 expenses per page

    query = Expense.query

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category and category != "":
        query = query.filter(Expense.category == category)

    if sort_by == "date":
        query = query.order_by(Expense.date)
    elif sort_by == "category":
        query = query.order_by(Expense.category)
    elif sort_by == "amount":
        query = query.order_by(Expense.amount)

   # total_expenses = query.count()
   # total_pages = ceil(total_expenses / per_page)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    expenses = pagination.items


    return render_template("index.html", expenses=expenses, pagination=pagination)



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

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    # Find the expense by ID
    expense = Expense.query.get_or_404(expense_id)

    # Delete from database
    db.session.delete(expense)
    db.session.commit()

    # Redirect back to home
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)
