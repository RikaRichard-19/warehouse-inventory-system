from flask import Flask, render_template, request, jsonify
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Google Sheets permissions
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

# Your Google service account JSON file
credentials = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

client = gspread.authorize(credentials)

# Open your Google Sheet
spreadsheet = client.open_by_key("1w6EXx8sY7rVKv4Rn6GkjcSsRZO8cWZa78r6FhuivdT4")

# Open the first sheet
sheet = spreadsheet.sheet1
supplier_sheet = spreadsheet.worksheet("Suppliers")
procurement_sheet = spreadsheet.worksheet("Procurement")
stock_history_sheet = spreadsheet.worksheet("Stock_History")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/suppliers")
def suppliers():
    suppliers = supplier_sheet.get_all_records()
    return render_template("suppliers.html", suppliers=suppliers)
@app.route("/procurement")
def procurement():
    procurement = procurement_sheet.get_all_records()
    return render_template("procurement.html", procurement=procurement)
@app.route("/add_procurement", methods=["POST"])
def add_procurement():
    procurement_id = request.form["procurement_id"]
    supplier_id = request.form["supplier_id"]
    item = request.form["item"]
    quantity = request.form["quantity"]
    order_date = request.form["order_date"]
    status = request.form["status"]

    procurement_sheet.append_row([
        procurement_id,
        supplier_id,
        item,
        quantity,
        order_date,
        status
    ])

    return "Procurement order added successfully. <a href='/procurement'>Go back</a>"
@app.route("/update_procurement_status", methods=["POST"])
def update_procurement_status():
    procurement_id = request.form["procurement_id"]
    new_status = request.form["status"]

    rows = procurement_sheet.get_all_records()

    for index, row in enumerate(rows, start=2):
        if str(row["Procurement ID"]) == procurement_id:

            procurement_sheet.update_cell(
                index,
                6,
                new_status
            )

            return "Status updated successfully. <a href='/procurement'>Go back</a>"

    return "Procurement order not found."
@app.route("/add_supplier", methods=["POST"])
def add_supplier():
    supplier_id = request.form["supplier_id"]
    supplier_name = request.form["supplier_name"]
    contact = request.form["contact"]
    email = request.form["email"]
    items_supplied = request.form["items_supplied"]

    supplier_sheet.append_row([
        supplier_id,
        supplier_name,
        contact,
        email,
        items_supplied
    ])

    return "Supplier added successfully. <a href='/suppliers'>Go back</a>"

@app.route("/stock-forecast")
def stock_forecast():

    # Get inventory and stock history
    inventory = sheet.get_all_records()
    history = stock_history_sheet.get_all_records()

    # --------------------------------
    # OVERALL STOCK MOVEMENT
    # --------------------------------

    total_added = 0
    total_removed = 0

    for row in history:
        total_added += int(row["Stock Added"])
        total_removed += int(row["Stock Removed"])

    total_current_stock = 0

    for row in inventory:
        total_current_stock += int(row["Quantity"])

    # --------------------------------
    # ITEM-WISE FORECAST
    # --------------------------------

    forecast_data = []

    for item in inventory:

        barcode = str(item["Barcode"])
        item_name = item["Item"]
        current_stock = int(item["Quantity"])

        item_removed = 0
        item_history_count = 0

        # Find stock usage for this item
        for record in history:

            if str(record["Barcode"]) == barcode:

                item_removed += int(record["Stock Removed"])
                item_history_count += 1

        # Calculate average daily usage
        if item_history_count > 0:
            daily_usage = item_removed / item_history_count
        else:
            daily_usage = 0

        # Calculate required stock for next 7 days
        required_7_days = round(daily_usage * 7)

        # Calculate additional stock required
        additional_required = max(
            0,
            required_7_days - current_stock
        )

        # Determine status
        if additional_required > 0:
            status = "Reorder Required"
        else:
            status = "Sufficient Stock"

        forecast_data.append({
            "item": item_name,
            "current_stock": current_stock,
            "daily_usage": round(daily_usage, 2),
            "required_7_days": required_7_days,
            "additional_required": additional_required,
            "status": status
        })

    # --------------------------------
    # SORT BY DEMAND
    # Highest usage first
    # --------------------------------

    forecast_data.sort(
        key=lambda x: x["daily_usage"],
        reverse=True
    )

    # Number of items requiring reorder
    reorder_count = 0

    for item in forecast_data:

        if item["additional_required"] > 0:
            reorder_count += 1

    # --------------------------------
    # OVERALL FORECAST
    # --------------------------------

    if history:
        average_daily_usage = total_removed / len(history)
    else:
        average_daily_usage = 0

    forecast_7_days = round(
        average_daily_usage * 7
    )

    # --------------------------------
    # SEND DATA TO HTML
    # --------------------------------

    return render_template(
        "stock_forecast.html",

        history=history,

        forecast_data=forecast_data,

        total_added=total_added,

        total_removed=total_removed,

        total_current_stock=total_current_stock,

        reorder_count=reorder_count,

        average_daily_usage=round(
            average_daily_usage,
            2
        ),

        forecast_7_days=forecast_7_days
    )
    
@app.route("/analytics")
def analytics():

    # Get data from Google Sheets
    inventory = sheet.get_all_records()
    procurement = procurement_sheet.get_all_records()
    history = stock_history_sheet.get_all_records()

    # --------------------------------
    # INVENTORY ANALYTICS
    # --------------------------------

    total_stock = sum(
        int(row["Quantity"])
        for row in inventory
    )

    total_items = len(inventory)

    low_stock_items = sum(
        1 for row in inventory
        if int(row["Quantity"]) < 10
    )

    # --------------------------------
    # STOCK MOVEMENT
    # --------------------------------

    total_added = sum(
        int(row["Stock Added"])
        for row in history
    )

    total_removed = sum(
        int(row["Stock Removed"])
        for row in history
    )

    # --------------------------------
    # PROCUREMENT ANALYTICS
    # --------------------------------

    total_procurement = len(procurement)

    pending_procurement = sum(
        1 for row in procurement
        if row["Status"].strip().lower() == "pending"
    )

    # --------------------------------
    # ITEM-WISE DEMAND
    # --------------------------------

    demand_data = []

    for item in inventory:

        barcode = str(item["Barcode"])
        item_name = item["Item"]
        current_stock = int(item["Quantity"])

        total_item_removed = 0

        for record in history:

            if str(record["Barcode"]) == barcode:

                total_item_removed += int(
                    record["Stock Removed"]
                )

        demand_data.append({
            "item": item_name,
            "current_stock": current_stock,
            "stock_removed": total_item_removed
        })

    # Highest-demand items first
    demand_data.sort(
        key=lambda x: x["stock_removed"],
        reverse=True
    )

    # --------------------------------
    # SEND DATA TO ANALYTICS PAGE
    # --------------------------------

    return render_template(
        "analytics.html",

        total_stock=total_stock,
        total_items=total_items,

        low_stock_items=low_stock_items,

        total_added=total_added,
        total_removed=total_removed,

        total_procurement=total_procurement,
        pending_procurement=pending_procurement,

        demand_data=demand_data
    )
@app.route("/search", methods=["POST"])
def search_item():

    data = request.json
    barcode = str(data.get("barcode", "")).strip()

    # Get all rows from Google Sheet
    rows = sheet.get_all_records()

    for row in rows:

        if str(row["Barcode"]) == barcode:

            return jsonify({
                "success": True,
                "name": row["Item"],
                "quantity": row["Quantity"],
                "location": row["Location"]
            })

    return jsonify({
        "success": False,
        "message": "Item not found"
    })

@app.route("/update", methods=["POST"])
def update_stock():

    data = request.json

    barcode = str(data.get("barcode", "")).strip()
    operation = data.get("operation")
    amount = int(data.get("quantity", 0))

    rows = sheet.get_all_records()

    for index, row in enumerate(rows, start=2):

        if str(row["Barcode"]) == barcode:

            current_quantity = int(row["Quantity"])

            if operation == "ADD":
                new_quantity = current_quantity + amount

            elif operation == "REMOVE":

                if amount > current_quantity:
                    return jsonify({
                        "success": False,
                        "message": "Not enough stock"
                    })

                new_quantity = current_quantity - amount

            else:
                return jsonify({
                    "success": False,
                    "message": "Invalid operation"
                })

            # Update Quantity column
            sheet.update_cell(index, 4, new_quantity)
            stock_history_sheet.append_row([
    datetime.now().strftime("%d-%m-%Y"),
    barcode,
    row["Item"],
    amount if operation == "ADD" else 0,
    amount if operation == "REMOVE" else 0
])
            return jsonify({
                "success": True,
                "message": "Stock updated successfully",
                "quantity": new_quantity
            })

    return jsonify({
        "success": False,
        "message": "Item not found"
    })
if __name__ == "__main__":
    app.run(debug=True, port=5002)
    
