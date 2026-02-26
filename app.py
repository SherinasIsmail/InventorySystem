import sqlite3
import csv
import io
import os
import json
from flask import Flask, render_template, request, session, redirect, url_for, Response, jsonify
from datetime import datetime, date, timedelta
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)
app.secret_key = 'small_business_ims_2026'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_COOKIE_NAME'] = 'ims_session'

# --- DATABASE SETUP ---
def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

def log_activity(conn, user, action, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute('INSERT INTO logs (user, action, details, timestamp) VALUES (?, ?, ?, ?)',
                 (user, action, details, timestamp))

def init_db():
    if not os.path.exists('inventory.db'):
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, role TEXT, assigned_category TEXT, contact TEXT, address TEXT, status TEXT, created_at TEXT,company_name TEXT, city TEXT, country TEXT, website TEXT, tax_id TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, category TEXT, price REAL, stock INTEGER, supplier TEXT, min_stock INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, user TEXT, action TEXT, details TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS deliveries (id INTEGER PRIMARY KEY, product_name TEXT, sku TEXT, quantity INTEGER, request_date TEXT, status TEXT, supplier TEXT)''')
        
        # --- SEED USERS ---
        users = [
            # Admin and Staff (Empty strings at the end for the new company details)
            ('Sherinas Ismail', 'sheri@sys.com', 'sheri123', 'Admin', 'All', '', '', 'Active', '2024-01-15', '', '', '', '', ''),
            ('Rahul Mohandas', 'rahul@sys.com', 'rahul123', 'Staff', 'Electronics', '', '', 'Active', '2024-02-20', '', '', '', '', ''),
            ('Alenteena Joseph', 'alenteena@sys.com', 'teena123', 'Staff', 'Accessories', '', '', 'Active', '2024-03-10', '', '', '', '', ''),
            ('Lisa Therese', 'lisa@sys.com', 'lisa123', 'Staff', 'Office Supplies', '', '', 'Active', '2024-04-05', '', '', '', '', ''),
            ('Shalbin Shyju', 'shal@sys.com', 'shal123', 'Staff', 'Furniture', '', '', 'Active', '2024-05-12', '', '', '', '', ''),
            
            # Suppliers
            ('Tech Vendor', 'tech@vendor.com', 'techpass', 'Supplier', 'Electronics', '+91 8546971236', '123 Tech Park', 'Active', '2024-01-10', 'Tech Vendor Inc.', 'Bangalore', 'India', 'www.techvendor.com', '12ABCDE1234F1Z5'),
            
            # FIXED: Cable Guy now has "Cable Solutions Pvt Ltd" perfectly in the 10th slot
            ('Cable Guy', 'cable@vendor.com', 'cablepass', 'Supplier', 'Accessories', '+91 9876543210', '45 Wire Lane', 'Active', '2024-01-12', 'Cable Solutions Pvt Ltd', 'Mumbai', 'India', 'www.cablesolutions.com', '22ABCDE1234F1Z5'),
            
            # FIXED: Office Depot now has the correct website
            ('Office Depot', 'office@vendor.com', 'officepass', 'Supplier', 'Office Supplies', '+91 7778889990', '78 Stationery Street', 'Active', '2024-02-01', 'Office Supply Co', 'Delhi', 'India', 'www.officedepot.com', '07LMNOP3456D1Z2'),
            
            ('Wood Works', 'wood@vendor.com', 'woodpass', 'Supplier', 'Furniture', '+91 6665554443', '99 Timber Road', 'Active', '2024-02-15', 'Wood Works Ltd', 'Chennai', 'India', 'www.woodworks.com', '33PQRSX7890E1Z4')
        ]
        
        c.executemany('INSERT INTO users (name, email, password, role, assigned_category, contact, address, status, created_at, company_name, city, country, website, tax_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', users)
        
        # --- SEED PRODUCTS (10+ PER CATEGORY) ---
        products = [
            # 1. Electronics (Tech Vendor)
            ('Laptop Dell XPS 15', 'ELEC-001', 'Electronics', 129999, 15, 'Tech Vendor', 10),
            ('Monitor 27" 4K', 'ELEC-002', 'Electronics', 32000, 5, 'Tech Vendor', 8),
            ('Webcam HD', 'ELEC-003', 'Electronics', 3500, 2, 'Tech Vendor', 5),
            ('Projector Sony', 'ELEC-004', 'Electronics', 45000, 4, 'Tech Vendor', 2),
            ('Samsung Tablet S9', 'ELEC-005', 'Electronics', 65000, 20, 'Tech Vendor', 10),
            ('HP LaserJet Printer', 'ELEC-006', 'Electronics', 18000, 8, 'Tech Vendor', 5),
            ('WiFi Router Asus', 'ELEC-007', 'Electronics', 4500, 30, 'Tech Vendor', 10),
            ('External HDD 2TB', 'ELEC-008', 'Electronics', 6000, 45, 'Tech Vendor', 15),
            ('Smart Speaker', 'ELEC-009', 'Electronics', 8000, 12, 'Tech Vendor', 5),
            ('Power Bank 20k', 'ELEC-010', 'Electronics', 2500, 60, 'Tech Vendor', 20),
            ('Graphics Card RTX', 'ELEC-011', 'Electronics', 45000, 3, 'Tech Vendor', 5),

            # 2. Accessories (Cable Guy)
            ('Wireless Mouse', 'ACC-101', 'Accessories', 850, 120, 'Cable Guy', 50),
            ('Mechanical Keyboard', 'ACC-102', 'Accessories', 3500, 25, 'Cable Guy', 10),
            ('HDMI Cable 2m', 'ACC-103', 'Accessories', 450, 200, 'Cable Guy', 30),
            ('USB-C Hub', 'ACC-104', 'Accessories', 1200, 40, 'Cable Guy', 15),
            ('Laptop Stand', 'ACC-105', 'Accessories', 1500, 15, 'Cable Guy', 5),
            ('Mousepad XL', 'ACC-106', 'Accessories', 350, 80, 'Cable Guy', 20),
            ('Screen Cleaner Kit', 'ACC-107', 'Accessories', 250, 100, 'Cable Guy', 30),
            ('Laptop Sleeve 15"', 'ACC-108', 'Accessories', 900, 35, 'Cable Guy', 10),
            ('Cable Organizer', 'ACC-109', 'Accessories', 150, 150, 'Cable Guy', 40),
            ('Webcam Cover', 'ACC-110', 'Accessories', 100, 300, 'Cable Guy', 50),
            ('Bluetooth Dongle', 'ACC-111', 'Accessories', 500, 60, 'Cable Guy', 15),

            # 3. Office Supplies (Office Depot)
            ('A4 Paper Bundle', 'OFF-101', 'Office Supplies', 250, 500, 'Office Depot', 100),
            ('Whiteboard Markers', 'OFF-102', 'Office Supplies', 150, 45, 'Office Depot', 20),
            ('Stapler Heavy Duty', 'OFF-103', 'Office Supplies', 450, 30, 'Office Depot', 10),
            ('Sticky Notes Pack', 'OFF-104', 'Office Supplies', 80, 200, 'Office Depot', 50),
            ('Ballpoint Pens Box', 'OFF-105', 'Office Supplies', 120, 150, 'Office Depot', 40),
            ('File Folders (Set)', 'OFF-106', 'Office Supplies', 300, 80, 'Office Depot', 20),
            ('Scotch Tape Dispenser', 'OFF-107', 'Office Supplies', 200, 60, 'Office Depot', 15),
            ('Paper Shredder', 'OFF-108', 'Office Supplies', 4500, 5, 'Office Depot', 2),
            ('Desk Organizer', 'OFF-109', 'Office Supplies', 550, 25, 'Office Depot', 5),
            ('Calculator Scientific', 'OFF-110', 'Office Supplies', 850, 40, 'Office Depot', 10),
            ('Scissors Professional', 'OFF-111', 'Office Supplies', 180, 70, 'Office Depot', 15),

            # 4. Furniture (Wood Works)
            ('Ergonomic Chair', 'FUR-001', 'Furniture', 15000, 12, 'Wood Works', 5),
            ('Office Desk Wooden', 'FUR-002', 'Furniture', 22000, 4, 'Wood Works', 3), # Low Stock
            ('Filing Cabinet', 'FUR-003', 'Furniture', 8000, 10, 'Wood Works', 3),
            ('Bookshelf 5-Tier', 'FUR-004', 'Furniture', 6500, 8, 'Wood Works', 2),
            ('Conference Table', 'FUR-005', 'Furniture', 45000, 2, 'Wood Works', 1),
            ('Whiteboard 6x4', 'FUR-006', 'Furniture', 3500, 15, 'Wood Works', 5),
            ('Desk Lamp LED', 'FUR-007', 'Furniture', 1200, 30, 'Wood Works', 10),
            ('Visitor Chair', 'FUR-008', 'Furniture', 4500, 20, 'Wood Works', 5),
            ('Sofa 3-Seater', 'FUR-009', 'Furniture', 35000, 2, 'Wood Works', 1),
            ('Monitor Arm Dual', 'FUR-010', 'Furniture', 4000, 15, 'Wood Works', 5),
            ('Footrest Adjustable', 'FUR-011', 'Furniture', 1800, 25, 'Wood Works', 8)
        ]
        c.executemany('INSERT INTO products (name, sku, category, price, stock, supplier, min_stock) VALUES (?,?,?,?,?,?,?)', products)
        
        # --- SEED DELIVERIES ---
        deliveries = [
            ('Laptop Dell XPS 15', 'ELEC-001', 5, '2024-11-20', 'Delivered', 'Tech Vendor'),
            ('Monitor 27" 4K', 'ELEC-002', 4, '2024-11-21', 'Pending', 'Tech Vendor'),
            ('Ergonomic Chair', 'FUR-001', 6, '2024-11-24', 'Pending', 'Wood Works'),
            ('A4 Paper Bundle', 'OFF-101', 100, '2024-11-25', 'Shipped', 'Office Depot')
        ]
        c.executemany('INSERT INTO deliveries (product_name, sku, quantity, request_date, status, supplier) VALUES (?,?,?,?,?,?)', deliveries)

        # --- SEED LOGS ---
        logs = [
            ('Admin', 'USER_ADD', 'Added new user: Lisa Staff', '2024-04-05 10:00'),
            ('Rahul', 'SALE', 'Sold Laptop Dell XPS 15', '2024-11-24 14:30'),
            ('Alenteena', 'STOCK_ADJUST', 'Restocked Wireless Mouse', '2024-11-24 09:15'),
            ('Tech Vendor', 'SUPPLY_DELIVERED', 'Supplied 25 Laptop Dell XPS 15', '2024-11-22 11:20')
        ]
        c.executemany('INSERT INTO logs (user, action, details, timestamp) VALUES (?,?,?,?)', logs)

        conn.commit()
        conn.close()

init_db()

# --- ROUTES ---
@app.route('/')
def home():
    if 'user' in session:
        role = session.get('role')
        if role == 'Admin': return redirect('/admin')
        if role == 'Staff': return redirect('/staff')
        if role == 'Supplier': return redirect('/supplier')
    return render_template('login.html', title="Login")

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    if user and user['password'] == password:
        if user['status'] == 'Inactive':
            return render_template('login.html', error="Access Denied: Your account is currently Inactive. Please contact the Admin.")
        session['user'] = user['name']
        session['role'] = user['role']
        session['assigned_category'] = user['assigned_category']
        if user['role'] == 'Admin': return redirect('/admin')
        if user['role'] == 'Staff': return redirect('/staff')
        if user['role'] == 'Supplier': return redirect('/supplier')
    return render_template('login.html', error="Invalid credentials. Please try again.")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- ADMIN ROUTES ---
@app.route('/admin')
def admin_dash():
    print(f"DEBUG: Current Session User: {session.get('user')}, Role: {session.get('role')}")
    if 'user' not in session or session.get('role') != 'Admin': 
        return redirect('/')
    
    conn = get_db_connection()
    
    # 1. Fetch base data
    products = conn.execute('SELECT * FROM products ORDER BY category ASC, name ASC').fetchall()
    users = conn.execute('SELECT * FROM users').fetchall()
    logs = conn.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 10').fetchall()
    transactions = conn.execute('''
        SELECT * FROM logs 
        WHERE (action = 'SALE' OR action LIKE '%RESTOCK%' OR action LIKE '%SUPPLY%')
        AND details NOT LIKE '%Deleted%' 
        AND details NOT LIKE '%Removed%'
        ORDER BY timestamp DESC LIMIT 5
    ''').fetchall()
    
    # 2. Dynamic Sales Calculations
    total_sales_count = conn.execute("SELECT count(*) FROM logs WHERE action='SALE'").fetchone()[0]
    revenue_query = '''
        SELECT SUM(p.price) 
        FROM logs l 
        JOIN products p ON l.details LIKE '%' || p.name || '%' 
        WHERE l.action = 'SALE'
    '''
    total_revenue = conn.execute(revenue_query).fetchone()[0] or 0
    
    # 3. Dynamic Category Data for Stock Chart
    category_data = conn.execute('''
        SELECT category, COUNT(*) as count 
        FROM products 
        GROUP BY category
    ''').fetchall()
    cat_labels = [row['category'] for row in category_data]
    cat_values = [row['count'] for row in category_data]

    # 4. Standard Dashboard Stats
    low_stock = sum(1 for p in products if p['stock'] < p['min_stock'])
    total_value = sum(p['price'] * p['stock'] for p in products)

    # 5. Dynamic Data (Indestructible Python-Side Filtering)
    from datetime import datetime, timedelta
    
    req_day = request.args.get('day')
    req_month = request.args.get('month')
    req_year = request.args.get('year')

    if req_year and req_month and req_day:
        try:
            anchor_date = datetime(int(req_year), int(req_month), int(req_day))
        except ValueError:
            anchor_date = datetime.now()
    else:
        anchor_date = datetime.now()

    # Grab ALL sales first, completely bypassing SQLite's broken date formatting
    all_sales = conn.execute('''
        SELECT l.timestamp, p.price, l.id, p.name
        FROM logs l 
        JOIN products p ON l.details LIKE '%' || p.name || '%' 
        WHERE l.action = 'SALE'
    ''').fetchall()
    print(f"DEBUG: Found {len(all_sales)} total sales in the database.")
    for s in all_sales:
        print(f"DEBUG SALE: Time: {s['timestamp']} | Price: {s['price']} | Product: {s['name']}")

    revenue_history = []
    sales_history = []
    days_labels = []

    for i in range(6, -1, -1):
        target_obj = anchor_date - timedelta(days=i)
        days_labels.append(target_obj.strftime('%a'))
        
        # Create all possible string formats your database might be hiding
        f1 = target_obj.strftime('%Y-%m-%d') # e.g. 2024-11-24
        f2 = target_obj.strftime('%d-%m-%Y') # e.g. 24-11-2024
        f3 = target_obj.strftime('%d/%m/%Y') # e.g. 24/11/2024
        
        daily_rev = 0
        daily_count = 0
        
        # Let Python do the searching instead of the database
        for sale in all_sales:
            ts = str(sale['timestamp'])
            if f1 in ts or f2 in ts or f3 in ts:
                daily_rev += (sale['price'] or 0)
                daily_count += 1
                
        revenue_history.append(daily_rev)
        sales_history.append(daily_count)
        
    stats = {
        'total': len(products),
        'low': low_stock,
        'value': total_value,
        'revenue': total_revenue,
        'sales_count': total_sales_count,
        'revenue_data': revenue_history, 
        'sales_vol': sales_history,      
        'days': days_labels,
        'cat_labels': cat_labels,
        'cat_values': cat_values
    }
    cat_query = '''
        SELECT DISTINCT category FROM products WHERE category != "" AND category IS NOT NULL
        UNION
        SELECT DISTINCT assigned_category as category FROM users WHERE assigned_category != "" AND assigned_category IS NOT NULL
        ORDER BY category ASC
    '''
    existing_cats = conn.execute(cat_query).fetchall()
    dynamic_categories = [row['category'] for row in existing_cats]
    
    conn.close()
    
    # 6. Single return to send all data to the template
    return render_template('admin_dashboard.html', 
                           products=products, 
                           users=users, 
                           logs=logs, 
                           transactions=transactions,
                           stats=stats,
                           dynamic_categories=dynamic_categories)

@app.route('/add_user', methods=['POST'])
def add_user():
    conn = get_db_connection()
    conn.execute('INSERT INTO users (name, email, password, role, assigned_category, contact, address, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)',
                 (request.form['name'], request.form['email'], request.form['password'], request.form['role'], request.form['assigned_category'], '','', 'Active', date.today().strftime("%Y-%m-%d")))
    log_activity(conn, session.get('user'), 'USER_ADD', f"Added user: {request.form['name']}")
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/edit_user', methods=['POST'])
def edit_user():
    user_id = request.form.get('user_id')
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    category = request.form.get('assigned_category')

    conn = get_db_connection()
    # This query updates all fields, allowing the Admin to change their own password live
    conn.execute('''UPDATE users 
                    SET name=?, email=?, password=?, role=?, assigned_category=? 
                    WHERE id=?''', 
                 (name, email, password, role, category, user_id))
    if session.get('user_id_internal') == user_id or session.get('user') == name:
        session['user'] = name
        session['role'] = role
        session.permanent = True
    
    log_activity(conn, session.get('user'), 'USER_EDIT', f"Updated user: {name}")
    conn.commit()
    conn.close()
    return redirect('/admin')
@app.route('/delete_user/<int:id>')
def delete_user(id):
    conn = get_db_connection()
    user = conn.execute('SELECT name FROM users WHERE id=?', (id,)).fetchone()
    if user:
        conn.execute('DELETE FROM users WHERE id = ?', (id,))
        log_activity(conn, session.get('user'), 'USER_DELETE', f"Deleted user: {user['name']}")
    conn.commit()
    conn.close()
    return redirect('/admin')
@app.route('/add_product', methods=['POST'])
def add_product():
    conn = get_db_connection()
    # Now we read the REAL supplier typed in the form
    conn.execute('INSERT INTO products (name, sku, category, price, stock, supplier, min_stock) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                 (request.form['name'], request.form['sku'], request.form['category'], request.form['price'], request.form['stock'], request.form['supplier'], 10))
    log_activity(conn, session.get('user'), 'PROD_ADD', f"Added product: {request.form['name']}")
    conn.commit()
    conn.close()
    return redirect('/admin')
@app.route('/edit_product', methods=['POST'])
def edit_product():
    conn = get_db_connection()
    conn.execute('UPDATE products SET name=?, sku=?, category=?, price=?, stock=? WHERE id=?', (request.form['name'], request.form['sku'], request.form['category'], request.form['price'], request.form['stock'], request.form['product_id']))
    log_activity(conn, session.get('user'), 'PROD_EDIT', f"Updated product: {request.form['name']}")
    conn.commit()
    conn.close()
    return redirect('/admin')
@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn = get_db_connection()
    prod = conn.execute('SELECT name FROM products WHERE id=?', (id,)).fetchone()
    if prod:
        conn.execute('DELETE FROM products WHERE id = ?', (id,))
        log_activity(conn, session.get('user'), 'PROD_DELETE', f"Deleted product: {prod['name']}")
    conn.commit()
    conn.close()
    return redirect('/admin')
@app.route('/adjust_stock_admin', methods=['POST'])
def adjust_stock_admin():
    conn = get_db_connection()
    conn.execute('UPDATE products SET stock=? WHERE sku=?', (request.form['new_stock'], request.form['sku']))
    log_activity(conn, session.get('user'), 'STOCK_ADJUST', f"Adjusted {request.form['sku']} to {request.form['new_stock']}")
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/export_report/<report_type>')
def export_report(report_type):
    conn = get_db_connection()
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'sales':
        # 1. Catch the specific dates from the export form
        req_day = request.args.get('day')
        req_month = request.args.get('month')
        req_year = request.args.get('year')

        # 2. exact base query, ready for filtering
        base_query = '''
            SELECT logs.user, logs.details, logs.timestamp, users.assigned_category 
            FROM logs 
            LEFT JOIN users ON logs.user = users.name 
            WHERE logs.action = 'SALE'
        '''

        # 3. Apply the filters dynamically
        if req_year and req_month and req_day:
            search_pattern = f"{req_year}-{req_month}-{req_day}%"
            query = base_query + " AND logs.timestamp LIKE ?"
            data = conn.execute(query, (search_pattern,)).fetchall()
            
        elif req_year and req_month:
            search_pattern = f"{req_year}-{req_month}-%"
            query = base_query + " AND logs.timestamp LIKE ?"
            data = conn.execute(query, (search_pattern,)).fetchall()
            
        elif req_year:
            search_pattern = f"{req_year}-%"
            query = base_query + " AND logs.timestamp LIKE ?"
            data = conn.execute(query, (search_pattern,)).fetchall()
            
        else:
            data = conn.execute(base_query).fetchall()

        writer.writerow(['Staff Name', 'Product Details', 'Timestamp', 'Staff Category'])
        for row in data:
            writer.writerow([row['user'], row['details'], row['timestamp'], row['assigned_category']])
        filename = "sales_report.csv"
        
    else:
        # Fetch products sorted by category first, and then alphabetically by name
        products = conn.execute('SELECT * FROM products ORDER BY category ASC, name ASC').fetchall()
        
        writer.writerow(['Sl. No.', 'Name', 'SKU', 'Category', 'Price', 'Stock', 'Supplier', 'Status'])
        
        for index, p in enumerate(products, start=1):
            
            # 1. Calculate the status dynamically based on the stock amount
            stock_level = p['stock']
            if stock_level == 0:
                status = 'Out of Stock'
            elif stock_level <= (p['min_stock']):  # Use min_stock if set, otherwise default to 5
                status = 'Low Stock'
            else:
                status = 'In Stock'
                
            writer.writerow([
                index, 
                p['name'], 
                p['sku'], 
                p['category'], 
                p['price'], 
                p['stock'], 
                p['supplier'],
                status
            ])
            
        filename = "stock_report.csv"

    conn.close()
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": f"attachment; filename={filename}"})

@app.route('/api/performance_data')
def get_performance_data():
    if session.get('role') != 'Admin': return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    
    # 1. Dynamic Turnover (Real Sales Count from Logs)
    sales_count = conn.execute("SELECT count(*) FROM logs WHERE action='SALE'").fetchone()[0]
    
    # 2. Dynamic Fulfillment Rate (Delivered vs Total Orders)
    total_orders = conn.execute("SELECT count(*) FROM deliveries").fetchone()[0]
    delivered_orders = conn.execute("SELECT count(*) FROM deliveries WHERE status='Delivered'").fetchone()[0]
    fulfillment = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
    
    # 3. Dynamic Response Time (Estimated by activity frequency)
    # Checks logs from the current date to see how "active" the system is
    today_str = date.today().strftime("%Y-%m-%d")
    recent_activity = conn.execute("SELECT count(*) FROM logs WHERE timestamp LIKE ?", (f'{today_str}%',)).fetchone()[0]
    # More activity = faster "simulated" response time
    res_time = round(3.0 / (recent_activity if recent_activity > 0 else 1), 1)

    conn.close()
    
    return jsonify({
        'fulfillment': f"{int(fulfillment)}%", 
        'response_time': f"{res_time} hrs", 
        'turnover': f"{sales_count} items"
    })

@app.route('/all_activities')
def all_activities():
    # Security check to ensure only the Admin enters
    if 'user' not in session or session.get('role') != 'Admin': 
        return redirect('/')
    
    conn = get_db_connection()
    # Fetch all logs from the database, newest first
    all_logs = conn.execute('SELECT * FROM logs ORDER BY timestamp DESC').fetchall()
    conn.close()
    
    return render_template('all_activities.html', logs=all_logs)

@app.route('/export_activities')
def export_activities():
    if 'user' not in session or session.get('role') != 'Admin':
        return redirect('/')
    
    # 1. Catch the search word sent by JavaScript button!
    search_word = request.args.get('search', '').strip()
    
    conn = get_db_connection()
    
    # 2. If a search word exists, filter the database. If not, get everything.
    if search_word:
        search_pattern = f"%{search_word}%"
        # The LIKE command finds the text anywhere in the user name or details
        query = '''
            SELECT timestamp, user, action, details 
            FROM logs 
            WHERE user LIKE ? OR details LIKE ? 
            ORDER BY timestamp DESC
        '''
        logs = conn.execute(query, (search_pattern, search_pattern)).fetchall()
    else:
        # Fallback: Just get all logs if the search box was empty
        logs = conn.execute('SELECT timestamp, user, action, details FROM logs ORDER BY timestamp DESC').fetchall()
        
    conn.close()

    # 3. Build and download the CSV
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Timestamp', 'User', 'Action', 'Details']) # Column Headers
    cw.writerows(logs)

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=activity_audit.csv"}
    )

@app.route('/get_sales_data/<period>')
def get_sales_data(period):
    if 'user' not in session or session.get('role') != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_connection()
    
    # 1. Catch the custom dates if the JavaScript sends them
    req_day = request.args.get('day')
    req_month = request.args.get('month')
    req_year = request.args.get('year')

    # 2. Determine anchor date (Handles Year only, Year+Month, or Full Date)
    if req_year:
        import calendar
        y = int(req_year)
        
        # If year is 2026 (current year), anchor to today
        if y == datetime.now().year:
            anchor_date = datetime.now()
        else:
            # If month is missing, look for the last month with a sale in that year
            m = int(req_month) if req_month else 11 # Defaulting to Nov for your 2024 data
            
            if req_day:
                d = int(req_day)
            else:
                d = calendar.monthrange(y, m)[1]
            
            try:
                anchor_date = datetime(y, m, d)
            except ValueError:
                anchor_date = datetime.now()
    else:
        # Fallback to the newest sale if no filter is used
        latest_sale = conn.execute("SELECT MAX(DATE(timestamp)) as max_date FROM logs WHERE action = 'SALE'").fetchone()
        if latest_sale and latest_sale['max_date']:
            anchor_date = datetime.strptime(latest_sale['max_date'], '%Y-%m-%d')
        else:
            anchor_date = datetime.now()
            
    days = 7 if period == 'week' else 30 if period == 'month' else 365
    
    labels = []
    revenue = []
    sales = []

    for i in range(days - 1, -1, -1):
        date_obj = anchor_date - timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d') # Matches '2024-11-24' format
        
        label = date_obj.strftime('%a') if period == 'week' else date_obj.strftime('%d %b')
        
        # Use LIKE to ignore the "14:30" part of database timestamp
        res = conn.execute('''
            SELECT SUM(p.price), COUNT(l.id)
            FROM logs l 
            JOIN products p ON l.details LIKE '%' || p.name || '%' 
            WHERE l.action = 'SALE' AND l.timestamp LIKE ? || '%'
        ''', (date_str,)).fetchone()
        
        labels.append(label)
        revenue.append(res[0] or 0)
        sales.append(res[1] or 0)
        
    total_revenue = sum(revenue)
    total_sales = sum(sales)
    avg_order = round(total_revenue / max(total_sales, 1))

    # Calculate past period for the percentage change text
    past_revenue = []
    past_sales = [] # NEW: Tracking past sales
    
    for i in range(days * 2 - 1, days - 1, -1):
        target_date = (anchor_date - timedelta(days=i)).strftime('%Y-%m-%d')
        # NEW: Added COUNT(l.id) to the query
        res = conn.execute('''
            SELECT SUM(p.price), COUNT(l.id) FROM logs l 
            JOIN products p ON l.details LIKE '%' || p.name || '%' 
            WHERE l.action = 'SALE' AND l.timestamp LIKE ? || '%'
        ''', (target_date,)).fetchone()
        
        past_revenue.append(res[0] or 0)
        past_sales.append(res[1] or 0)

    # Calculate the totals for the past period
    past_total_rev = sum(past_revenue)
    past_total_sales = sum(past_sales)
    past_avg = round(past_total_rev / max(past_total_sales, 1))

    # Helper function to safely calculate percentage change
    def get_change(current, past):
        if past > 0:
            return round(((current - past) / past) * 100, 1)
        return 100.0 if current > 0 else 0.0

    # Calculate all three percentage changes
    rev_change = get_change(total_revenue, past_total_rev)
    sales_change = get_change(total_sales, past_total_sales)
    avg_change = get_change(avg_order, past_avg)
        
    conn.close()
    
    # Send all three variables to the frontend
    return jsonify({
        'labels': labels, 
        'revenue': revenue, 
        'sales': sales,
        'total_revenue': total_revenue,
        'total_sales': total_sales,
        'avg_value': avg_order,
        'revenue_change': rev_change,
        'sales_change': sales_change,  
        'avg_change': avg_change       
    })
    
@app.route('/update_status/<int:id>/<status>')
def update_status(id, status):
    # 1. Security check: Only let valid statuses through
    if status not in ['Active', 'Inactive']:
        return jsonify({'success': False, 'error': 'Invalid status provided'}), 400

    try:
        # 2. Connect to the database and update the user
        conn = get_db_connection()
        conn.execute('UPDATE users SET status = ? WHERE id = ?', (status, id))
        conn.commit()
        conn.close()
        
        # 3. Send a success message back to JavaScript
        return jsonify({'success': True, 'message': f'User {id} status changed to {status}'})
        
    except Exception as e:
        # If the database crashes, let the frontend know safely
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stock_by_category')
def stock_by_category():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_connection()
    try:
        # COALESCE ensures products without a category are grouped as 'Other'
        query = '''
            SELECT 
                COALESCE(category, 'Other') as cat,
                SUM(CASE WHEN stock >= COALESCE(min_stock, 5) THEN 1 ELSE 0 END) as in_stock,
                SUM(CASE WHEN stock < COALESCE(min_stock, 5) AND stock > 0 THEN 1 ELSE 0 END) as low_stock,
                SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END) as out_of_stock
            FROM products
            GROUP BY COALESCE(category, 'Other')
            ORDER BY category ASC
        '''
        results = conn.execute(query).fetchall()
        
        return jsonify({
            'labels': [r['cat'] for r in results],
            'inStock': [r['in_stock'] for r in results],
            'lowStock': [r['low_stock'] for r in results],
            'outOfStock': [r['out_of_stock'] for r in results]
        })
    except Exception as e:
        print(f"Chart Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
    
# --- STAFF ROUTES ---
@app.route('/staff')
def staff_dash():
    if session.get('role') != 'Staff': return redirect('/')
    user_name = session.get('user')
    user_category = session.get('assigned_category')
    conn = get_db_connection()
    if user_category and user_category != 'All':
        products = conn.execute('SELECT * FROM products WHERE category = ?', (user_category,)).fetchall()
    else:
        products = conn.execute('SELECT * FROM products').fetchall()
    logs = conn.execute('SELECT * FROM logs WHERE user = ? ORDER BY id DESC LIMIT 5', (user_name,)).fetchall()
    today = date.today().strftime("%Y-%m-%d")
    sales_today = conn.execute("SELECT count(*) FROM logs WHERE action='SALE' AND timestamp LIKE ?", (f'{today}%',)).fetchone()[0]
    updates_today = conn.execute("SELECT count(*) FROM logs WHERE action='STOCK_ADJUST' AND timestamp LIKE ?", (f'{today}%',)).fetchone()[0]
    conn.close()
    return render_template('staff_dashboard.html', products=products, logs=logs, user_category=user_category, stats={'products': len(products), 'updates': updates_today, 'transactions': sales_today})

@app.route('/staff_update_stock', methods=['POST'])
def staff_update_stock():
    if session.get('role') != 'Staff': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    try:
        sku = request.form['sku']
        qty = int(request.form['quantity'])
        conn.execute('UPDATE products SET stock = stock + ? WHERE sku = ?', (qty, sku))
        log_msg = f"Added {qty} units to {sku}" if qty >= 0 else f"Removed {abs(qty)} units from {sku}"
        log_activity(conn, session.get('user'), 'STOCK_ADJUST', log_msg)
        conn.commit()
        return jsonify({'status': 'success', 'message': log_msg})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

@app.route('/staff_add_product', methods=['POST'])
def staff_add_product():
    if session.get('role') != 'Staff': return redirect('/')
    conn = get_db_connection()
    try:
        user_cat = session.get('assigned_category')
        category = user_cat if user_cat and user_cat != 'All' else request.form.get('category', 'General')
        conn.execute('INSERT INTO products (name, sku, category, price, stock, supplier, min_stock) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (request.form['name'], request.form['sku'], category, float(request.form['price']), int(request.form['stock']), request.form['supplier'], int(request.form['min_stock'])))
        log_activity(conn, session.get('user'), 'PROD_ADD', f"Staff created: {request.form['name']}")
        conn.commit()
    except: pass
    finally: conn.close()
    return redirect('/staff')

@app.route('/staff_checkout', methods=['POST'])
def staff_checkout():
    if session.get('role') != 'Staff': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    conn = get_db_connection()
    try:
        for item in data['items']:
            curr = conn.execute('SELECT stock FROM products WHERE sku = ?', (item['sku'],)).fetchone()
            if curr and curr['stock'] > 0:
                conn.execute('UPDATE products SET stock = stock - 1 WHERE sku = ?', (item['sku'],))
                log_activity(conn, session.get('user'), 'SALE', f"Sold {item['name']}")
            else:
                return jsonify({'status': 'error', 'message': f"Out of stock: {item['name']}"}), 400
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()
        
# --- SUPPLIER ROUTES ---
@app.route('/supplier')
def supplier_dash():
    if session.get('role') != 'Supplier': return redirect('/')
    supplier_name = session.get('user')
    conn = get_db_connection()
    user_info = conn.execute('SELECT * FROM users WHERE name = ?', (supplier_name,)).fetchone()
    my_products = conn.execute('SELECT * FROM products WHERE supplier = ?', (supplier_name,)).fetchall()
    orders = conn.execute('SELECT * FROM deliveries WHERE supplier = ? ORDER BY id DESC', (supplier_name,)).fetchall()
    active_deliveries = sum(1 for o in orders if o['status'] == 'In Progress' or o['status'] == 'Shipped')
    pending_reqs = sum(1 for o in orders if o['status'] == 'Pending')
    conn.close()
    return render_template('supplier_dashboard.html', user=user_info, products=my_products, orders=orders, stats={'active': active_deliveries, 'pending': pending_reqs, 'total_products': len(my_products)})

@app.route('/supplier_update_status', methods=['POST'])
def supplier_update_status():
    if session.get('role') != 'Supplier': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    try:
        order_id = request.form['order_id']
        new_status = request.form['status']
        if new_status == 'Delivered':
            order = conn.execute('SELECT * FROM deliveries WHERE id=?', (order_id,)).fetchone()
            if order:
                conn.execute('UPDATE products SET stock = stock + ? WHERE sku = ?', (order['quantity'], order['sku']))
                log_activity(conn, session.get('user'), 'SUPPLY_DELIVERED', f"Supplied {order['quantity']} {order['product_name']}")
        conn.execute('UPDATE deliveries SET status = ? WHERE id = ?', (new_status, order_id))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

@app.route('/supplier_acknowledge_alert', methods=['POST'])
def supplier_acknowledge_alert():
    if session.get('role') != 'Supplier': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    try:
        sku = request.form['sku']
        qty = request.form.get('quantity', type=int, default=1)
        product = conn.execute('SELECT * FROM products WHERE sku=?', (sku,)).fetchone()
        if product:
            today = date.today().strftime("%Y-%m-%d")
            conn.execute('INSERT INTO deliveries (product_name, sku, quantity, request_date, status, supplier) VALUES (?,?,?,?,?,?)',
                         (product['name'], sku, qty, today, 'Pending', session.get('user')))
            conn.commit()
            return jsonify({'status': 'success', 'message': f"Restock initiated: {qty} units of {product['name']}"})
        else:
            return jsonify({'status': 'error', 'message': 'Product not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

@app.route('/supplier_update_profile', methods=['POST'])
def supplier_update_profile():
    if session.get('role') != 'Supplier': 
        return redirect('/')
    
    company_name = request.form.get('company_name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    city = request.form.get('city')
    country = request.form.get('country')
    website = request.form.get('website')
    tax_id = request.form.get('tax_id')
    
    conn = get_db_connection()
    
    # Update the database with all the new fields
    conn.execute('''
        UPDATE users 
        SET company_name=?, contact=?, address=?, city=?, country=?, website=?, tax_id=? 
        WHERE name=?
    ''', (company_name, phone, address, city, country, website, tax_id, session.get('user')))
    
    conn.commit()
    conn.close()
    
    return redirect('/supplier')
if __name__ == '__main__':
    app.run(debug=True, port=5000)
