import pandas as pd

def load_expenses(csv_file="data/expenses.csv"):
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])
    return df

df = load_expenses()
print(df.head())
