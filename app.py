from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from math import ceil
import matplotlib.pyplot as plt
import io
import base64


app = Flask(__name__)

app.secret_key = "os.urandom(24)"  # Replace with a strong key


# Configure SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'expenses.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db = SQLAlchemy(app)

#user login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect users to login if not authenticated

# Define Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # ✅ Link to User table



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()



def generate_charts(selected_month=None, selected_year=None):
    # Get all expenses from the database
    query = Expense.query.filter_by(user_id=current_user.id)


    # Filter by month and year if selected
    if selected_month:
        query = query.filter(db.extract("month", Expense.date) == selected_month)
    if selected_year:
        query = query.filter(db.extract("year", Expense.date) == selected_year)

    expenses = query.all()

    # Organize data by category
    category_totals = {}
    for expense in expenses:
        category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount

    if not category_totals:
        return None, None  # No data available

    # Create Bar Chart
    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    plt.figure(figsize=(6, 4))
    plt.bar(categories, amounts, color='skyblue')
    plt.xlabel("Category")
    plt.ylabel("Amount ($)")
    plt.title(f"Expenses for {selected_month}/{selected_year}" if selected_month and selected_year else "Expenses by Category")

    # Convert Bar Chart to Image
    bar_img = io.BytesIO()
    plt.savefig(bar_img, format="png")
    bar_img.seek(0)
    bar_url = base64.b64encode(bar_img.getvalue()).decode()

    # Create Pie Chart
    plt.figure(figsize=(6, 4))
    plt.pie(amounts, labels=categories, autopct="%1.1f%%", colors=['lightcoral', 'gold', 'lightblue', 'lightgreen', 'orange'])
    plt.title(f"Spending Breakdown for {selected_month}/{selected_year}" if selected_month and selected_year else "Spending Breakdown")

    # Convert Pie Chart to Image
    pie_img = io.BytesIO()
    plt.savefig(pie_img, format="png")
    pie_img.seek(0)
    pie_url = base64.b64encode(pie_img.getvalue()).decode()

    return bar_url, pie_url



@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        date = request.form["date"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        description = request.form["description"]

        new_expense = Expense(date=date, category=category, amount=amount, description=description, user_id=current_user.id)
        db.session.add(new_expense)
        db.session.commit()

        flash("Expense added successfully!", "success") 

        return redirect("/")

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category")
    sort_by = request.args.get("sort_by", "date")
    page = request.args.get("page", 1, type=int)
    per_page = 5

    # Get selected month and year from dropdown
    selected_month = request.args.get("month", type=int)
    selected_year = request.args.get("year", type=int)

    query = Expense.query.filter_by(user_id=current_user.id)

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category and category != "":
        query = query.filter(Expense.category == category)

    if selected_month:
        query = query.filter(db.extract("month", Expense.date) == selected_month)
    if selected_year:
        query = query.filter(db.extract("year", Expense.date) == selected_year)

    if sort_by == "date":
        query = query.order_by(Expense.date)
    elif sort_by == "category":
        query = query.order_by(Expense.category)
    elif sort_by == "amount":
        query = query.order_by(Expense.amount)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    expenses = pagination.items

    # Get available years dynamically
    available_years = db.session.query(db.func.extract("year", Expense.date)).distinct().all()
    available_years = sorted([int(year[0]) for year in available_years])

    # Generate charts with filters
    bar_chart, pie_chart = generate_charts(selected_month, selected_year)

    

    return render_template("index.html", expenses=expenses, pagination=pagination,
                           bar_chart=bar_chart, pie_chart=pie_chart, 
                           selected_month=selected_month, selected_year=selected_year,
                           available_years=available_years, current_user=current_user)





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

        flash("Expense updated successfully!", "info") #info - Blue message

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

    flash("Expense deleted successfully!", "danger") #Danger - Red message

    # Redirect back to home
    return redirect("/")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        # Hash password and store user
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)

    

