import pandas as pd
from io import StringIO

def generate_html_report(financial_records):
    data = []
    for record in financial_records:
        data.append([record.username, record.user_message, record.product, record.price,
                     record.quantity, record.status, record.amount, record.timestamp])

    df = pd.DataFrame(data, columns=["Username", "User message", "Product", "Price",
                                     "Quantity", "Status", "Amount", "Timestamp"])

    html_content = df.to_html()

    return html_content
