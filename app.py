<<<<<<< HEAD
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, this is your Personal Expense Tracker!"
=======
from flask import Flask, render_template, request

app = Flask(__name__)


expenses = []

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get form data
        date = request.form['date']
        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']

        # (for now, just storing in a list)
        expenses.append({'date': date, 'category': category, 'amount': amount, 'description': description})

    return render_template('index.html', expenses=expenses)
>>>>>>> 90410be48d8e98b531f968ac09aa2c5e0faf73cd

if __name__ == '__main__':
    app.run(debug=True)
