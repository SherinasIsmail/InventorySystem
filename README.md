📦 Inventory Management System
Inventory Management System is a high-performance, three-tier management application designed to bridge the gap between warehouse logistics and retail efficiency. It features a unique Silent Traceability engine that automatically assigns serial and batch numbers during checkout, ensuring every unit sold is 100% trackable.

🚀 Project Overview
Developed as a full-stack solution, this system manages the entire product lifecycle—from supplier restocking to point-of-sale scanning. It eliminates manual data entry errors by integrating smartphone hardware as a wireless barcode scanner.

🔑 Key Modules
Admin Console: High-level oversight of users, master inventory, and sales analytics with CSV export capabilities.
Staff Dashboard: A fast-paced billing interface with live product search and automated item serialization.
Supplier Portal: A dedicated vendor view for tracking low-stock alerts and managing incoming deliveries.

✨ Core Features
Hardware Integration: Uses a Mobile-to-PC bridge to turn any smartphone into a professional barcode wand.
Automated Traceability: Custom JavaScript engine that "invents" unique Serial Numbers (SN) and Batch Numbers (BN) the millisecond an item is scanned.
Real-Time Alerts: Automated visual cues for suppliers when stock levels drop below the defined min_stock threshold.
Dynamic Billing: A "no-refresh" cart system built with Vanilla JS and Flask for a smooth user experience.

🛠️ Tech Stack
Backend: Python 3.x, Flask
Frontend: HTML5, Tailwind CSS, JavaScript (ES6+)
Database: SQLite3
Tools: Git, VS Code, Barcode to PC API

📂 Project Structure
Plaintext
├── app.py              # Main Flask application & API routes
├── inventory.db        # SQLite database (Auto-generated)
├── static/
│   ├── css/            # Tailwind styles
│   └── js/             # Billing & Scanner logic
└── templates/
    ├── base.html              # Shared layout (Navigation & Footers)
    ├── login.html             # Secure multi-user authentication page
    ├── admin_dashboard.html   # Management & Sales Reporting interface
    ├── staff_dashboard.html   # Real-time Billing & Barcode Scanner interface
    ├── supplier_dashboard.html  # Low-stock Alerts & Vendor portal
    └── all_activities.html    # Master audit log for system events
    
⚙️ Setup & Installation
Clone the Repository:
Bash
git clone https://github.com/NavriReddy/QuickScan-Inventory.git

Install Flask:
Bash
pip install flask

Run the Application:
Bash
python app.py

Hardware Sync:
Open the Barcode to PC server on your laptop.
Pair your mobile device via the QR code.
Scan items directly into the Billing tab!

📝 License
Distributed under the MIT License. Created by Sherinas Ismail.
