from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from datetime import datetime
from flask import send_file
from io import BytesIO
import csv

from flask import Flask

from flask_scss import Scss





app = Flask(__name__)
Scss(app, static_dir='static/css', asset_dir='static/scss')
app = Flask(__name__, static_folder="static")
app = Flask(__name__, static_folder="static")




app.secret_key = 'your_secret_key'  # Required for session management

# Database Configuration (Replace with your Render PostgreSQL credentials)
DB_CONFIG = {
    'dbname': 'db2_96ym',  # Database name
    'user': 'db2_96ym_user',  # Username
    'password': 'vpVGNjgmuXYB9EwmGBgWtCyUBdoC74p9',  # Password
    'host': 'dpg-cumutu9u0jms73b8o8hg-a.oregon-postgres.render.com',  # Hostname
    'port': '5432'  # Default PostgreSQL port
}

# Menu Data
drinks = [
    {"id": 31, "name": "Fresh Orange Juice", "category": "Fresh Juice", "price": 2000},
    {"id": 32, "name": "Watermelon Juice", "category": "Fresh Juice", "price": 2200},
    {"id": 33, "name": "Chapman", "category": "Mocktail", "price": 2500},
]

foods = [
    {"id": 1, "name": "Peppered Snail", "category": "Starter", "price": 4500},
    {"id": 2, "name": "Meat Pie", "category": "Starter", "price": 1200},
    {"id": 3, "name": "Spring Rolls", "category": "Starter", "price": 1500},
]

# Helper function to connect to the database
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                table_number VARCHAR(10),
                item VARCHAR(255),
                quantity INTEGER,
                price FLOAT,
                confirmed BOOLEAN,
                timestamp TIMESTAMP
            )
        ''')
        # Create served_orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS served_orders (
                id SERIAL PRIMARY KEY,
                table_number VARCHAR(10),
                item VARCHAR(255),
                quantity INTEGER,
                price FLOAT,
                closing_time TIMESTAMP
            )
        ''')
        # Create table_status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_status (
                table_number VARCHAR(10) PRIMARY KEY,
                glow_status BOOLEAN DEFAULT FALSE
            )
        ''')
        # Initialize table_status for tables 1-10
        for table_number in range(1, 11):
            cursor.execute('''
                INSERT INTO table_status (table_number, glow_status)
                VALUES (%s, FALSE)
                ON CONFLICT (table_number) DO NOTHING
            ''', (str(table_number),))
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

initialize_database()

# Helper function to read orders from the database
def read_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT table_number, item, quantity, price, confirmed, timestamp FROM orders')
        rows = cursor.fetchall()
        orders = []
        for row in rows:
            orders.append({
                'Table Number': row[0],
                'Item': row[1],
                'Quantity': row[2],
                'Price': row[3],
                'Confirmed': row[4],
                'Timestamp': row[5]
            })
        return orders
    except Exception as e:
        print(f"Error reading orders: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Helper function to write an order to the database
def write_order(table_number, item, quantity, price, confirmed):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO orders (table_number, item, quantity, price, confirmed, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (table_number, item, quantity, price, confirmed, timestamp))
        conn.commit()
    except Exception as e:
        print(f"Error writing order: {e}")
    finally:
        cursor.close()
        conn.close()

# Helper function to remove an order by index
def remove_order(index):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM orders WHERE id = %s', (index,))
        conn.commit()
    except Exception as e:
        print(f"Error removing order: {e}")
    finally:
        cursor.close()
        conn.close()


# Helper function to remove an order by index
def remove_order(index):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ensure the index is valid before executing the query
        if not isinstance(index, int):
            raise ValueError("Invalid index type. Expected an integer.")

        # Execute the DELETE query
        cursor.execute('DELETE FROM orders WHERE id = %s', (index,))

        # Check if any rows were affected
        if cursor.rowcount == 0:
            print(f"No order found with id {index}.")
        else:
            print(f"Order with id {index} removed successfully.")

        # Commit the transaction
        conn.commit()

    except ValueError as ve:
        # Handle invalid index type errors
        print(f"ValueError: {ve}")
    except Exception as e:
        # Handle other exceptions
        print(f"Error removing order: {e}")
    finally:
        # Ensure resources are properly closed
        cursor.close()
        conn.close()
# Helper function to move all orders for a table to served_orders
def move_table_to_served_orders(table_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Find all orders for the specified table
        cursor.execute('SELECT id, table_number, item, quantity, price FROM orders WHERE table_number = %s', (table_number,))
        rows = cursor.fetchall()
        served_orders = []
        for row in rows:
            served_orders.append({
                'table_number': row[1],
                'item': row[2],
                'quantity': row[3],
                'price': row[4],
                'closing_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        # Insert into served_orders table
        for order in served_orders:
            cursor.execute('''
                INSERT INTO served_orders (table_number, item, quantity, price, closing_time)
                VALUES (%s, %s, %s, %s, %s)
            ''', (order['table_number'], order['item'], order['quantity'], order['price'], order['closing_time']))
        # Delete from orders table
        cursor.execute('DELETE FROM orders WHERE table_number = %s', (table_number,))
        conn.commit()
    except Exception as e:
        print(f"Error moving orders to served_orders: {e}")
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/tables')
def tables():
    return render_template('tables.html')

@app.route('/bill/<int:table_number>')
def bill(table_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM orders WHERE table_number = %s AND confirmed = FALSE', (str(table_number),))
        rows = cursor.fetchall()
        unconfirmed_orders = []
        for row in rows:
            unconfirmed_orders.append({
                'Table Number': row[1],
                'Item': row[2],
                'Quantity': row[3],
                'Price': row[4],
                'Confirmed': row[5],
                'Timestamp': row[6]
            })
        total_items = sum(order['Quantity'] for order in unconfirmed_orders)
        total_bill = sum(order['Price'] * order['Quantity'] for order in unconfirmed_orders)
        return render_template(
            'bill.html',
            table_number=table_number,
            total_items=total_items,
            total_bill=total_bill,
            unconfirmed_orders=unconfirmed_orders
        )
    except Exception as e:
        print(f"Error fetching bill: {e}")
        return render_template('bill.html', table_number=table_number, total_items=0, total_bill=0, unconfirmed_orders=[])
    finally:
        cursor.close()
        conn.close()

@app.route('/close_table/<int:table_number>', methods=['POST'])
def close_table(table_number):
    move_table_to_served_orders(str(table_number))
    return redirect(url_for('waiter'))

@app.route('/menu/<int:table_number>', methods=['GET', 'POST'])
def menu(table_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch all orders for the specified table
        cursor.execute('SELECT * FROM orders WHERE table_number = %s', (str(table_number),))
        rows = cursor.fetchall()
        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'Table Number': row[1],
                'Item': row[2],
                'Quantity': row[3],
                'Price': row[4],
                'Confirmed': row[5],
                'Timestamp': row[6]
            })

        if request.method == 'POST':
            action = request.form.get('action')

            # Prevent duplicate submissions on page refresh
            if 'submitted' in session and session['submitted']:
                return redirect(url_for('menu', table_number=table_number))
            session['submitted'] = True

            if action == 'add':
                # Add a new item to the order
                item = request.form['item']
                quantity = int(request.form['quantity'])
                price = float(request.form['price'])
                write_order(str(table_number), item, quantity, price, False)

            elif action == 'remove':
                # Remove an item from the unconfirmed orders
                index = int(request.form['index'])
                remove_order(index)

            elif action == 'send':
                # Mark all unconfirmed orders as sent (confirmed)
                cursor.execute(
                    'UPDATE orders SET confirmed = TRUE WHERE table_number = %s AND confirmed = FALSE',
                    (str(table_number),)
                )
                conn.commit()

            return redirect(url_for('menu', table_number=table_number))

        # Reset submission flag after GET request
        session.pop('submitted', None)

        # Separate confirmed and unconfirmed orders
        confirmed_orders = [order for order in orders if order['Confirmed']]
        unconfirmed_orders = [order for order in orders if not order['Confirmed']]

        # Calculate total bill for unconfirmed orders
        total_bill = sum(order['Price'] * order['Quantity'] for order in unconfirmed_orders)

        # Pass enumerated orders to the template
        enumerated_confirmed_orders = list(enumerate(confirmed_orders))
        enumerated_unconfirmed_orders = list(enumerate(unconfirmed_orders))

        return render_template(
            'menu.html',
            enumerated_confirmed_orders=enumerated_confirmed_orders,
            enumerated_unconfirmed_orders=enumerated_unconfirmed_orders,
            table_number=table_number,
            total_bill=total_bill,
            drinks=drinks,
            foods=foods,
            has_unconfirmed_orders=len(unconfirmed_orders) > 0
        )

    except Exception as e:
        print(f"Error handling menu: {e}")
        return redirect(url_for('menu', table_number=table_number))

    finally:
        cursor.close()
        conn.close()

@app.route('/waiter')
def waiter():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch confirmed orders
        cursor.execute('SELECT * FROM orders WHERE confirmed = TRUE')
        rows = cursor.fetchall()
        grouped_tables = {}
        for row in rows:
            table_number = row[1]
            if table_number not in grouped_tables:
                grouped_tables[table_number] = []
            grouped_tables[table_number].append({
                'Item': row[2],
                'Quantity': row[3],
                'Price': row[4],
                'Timestamp': row[6]
            })

        # Fetch glowing status for all tables
        cursor.execute('SELECT table_number, glow_status FROM table_status')
        glow_status_rows = cursor.fetchall()
        glow_status = {row[0]: row[1] for row in glow_status_rows}

        return render_template('waiter.html', grouped_tables=grouped_tables, glow_status=glow_status)
    except Exception as e:
        print(f"Error fetching waiter data: {e}")
        return render_template('waiter.html', grouped_tables={}, glow_status={})
    finally:
        cursor.close()
        conn.close()

@app.route('/confirm_order/<int:table_number>', methods=['POST'])
def confirm_order_route(table_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Mark all unconfirmed orders for the table as confirmed
        cursor.execute('UPDATE orders SET confirmed = TRUE WHERE table_number = %s AND confirmed = FALSE', (str(table_number),))
        conn.commit()
    except Exception as e:
        print(f"Error confirming order: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('waiter'))





from flask import send_file
from io import BytesIO
from openpyxl import Workbook

# Password for downloading served orders
DOWNLOAD_PASSWORD = "admin123"

@app.route('/download_served_orders', methods=['GET', 'POST'])
def download_served_orders():
    if request.method == 'POST':
        # Check if the password is correct
        password = request.form.get('password')
        if password == DOWNLOAD_PASSWORD:
            # Fetch served orders from the database
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT table_number, item, quantity, price, closing_time FROM served_orders')
                rows = cursor.fetchall()
                served_orders = []
                for row in rows:
                    served_orders.append({
                        'Table Number': row[0],
                        'Item': row[1],
                        'Quantity': row[2],
                        'Price': row[3],
                        'Closing Time': row[4]
                    })

                # Create an Excel workbook and worksheet
                wb = Workbook()
                ws = wb.active
                ws.title = "Served Orders"

                # Write headers
                headers = ['Table Number', 'Item', 'Quantity', 'Price', 'Closing Time']
                ws.append(headers)

                # Write data rows
                for order in served_orders:
                    ws.append([
                        order['Table Number'],
                        order['Item'],
                        order['Quantity'],
                        order['Price'],
                        order['Closing Time']
                    ])

                # Save the workbook to a BytesIO object
                output = BytesIO()
                wb.save(output)
                output.seek(0)

                # Send the Excel file as a download
                return send_file(
                    output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name='served_orders.xlsx'
                )
            except Exception as e:
                print(f"Error fetching served orders: {e}")
                return render_template('download.html', error="An error occurred while fetching served orders.")
            finally:
                cursor.close()
                conn.close()
        else:
            return render_template('download.html', error="Incorrect password. Please try again.")

    # Render the download page with a password form
    return render_template('download.html', error=None)



@app.route('/call_waiter/<int:table_number>', methods=['POST'])
def call_waiter(table_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE table_status SET glow_status = TRUE WHERE table_number = %s', (str(table_number),))
        conn.commit()
    except Exception as e:
        print(f"Error updating glow status: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('menu', table_number=table_number))

@app.route('/acknowledge_call/<int:table_number>', methods=['POST'])
def acknowledge_call(table_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Update the glow status for the table
        cursor.execute('UPDATE table_status SET glow_status = FALSE WHERE table_number = %s', (str(table_number),))
        conn.commit()
    except Exception as e:
        print(f"Error acknowledging call: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('waiter'))



if __name__ == '__main__':
    app.run(debug=True)