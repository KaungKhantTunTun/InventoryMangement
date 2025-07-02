from flask import Flask, render_template_string, request, redirect, url_for
from datetime import datetime
import csv

app = Flask(__name__)
ITEMS_FILE = "items.txt"
SALES_FILE = "sales.txt"

def load_items():
    items = []
    try:
        with open(ITEMS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                # Support old files without expiry
                if len(parts) == 5:
                    name, stock, original_price, sale_price, expiry = parts
                else:
                    name, stock, original_price, sale_price = parts
                    expiry = ""
                items.append({
                    "name": name,
                    "stock": int(stock),
                    "original_price": float(original_price),
                    "sale_price": float(sale_price),
                    "expiry": expiry
                })
    except FileNotFoundError:
        pass
    return items

def save_items(items):
    with open(ITEMS_FILE, "w") as f:
        for item in items:
            expiry = item.get("expiry", "")
            f.write(
                f"{item['name']},{item['stock']},{item['original_price']},{item['sale_price']},{expiry}\n"
            )

def record_sale(name, quantity, profit):
    now = datetime.now().strftime("%Y-%m-%d")
    with open(SALES_FILE, "a") as f:
        f.write(f"{now},{name},{quantity},{profit}\n")

def load_sales():
    sales = []
    try:
        with open(SALES_FILE, "r") as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line:
                    parts = stripped_line.split(",")
                    if len(parts) == 4:
                        date, name, qty, profit = parts
                        sales.append({
                            "date": date,
                            "name": name,
                            "qty": int(qty),
                            "profit": float(profit)
                        })
    except FileNotFoundError:
        pass
    return sales

def load_all_medicines():
    medicines = []
    try:
        with open("medicines.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) > 1 and row[1].strip():
                    medicines.append(row[1].strip())
    except FileNotFoundError:
        pass
    return medicines

@app.route("/")
def index():
    items = load_items()
    sales = load_sales()
    all_medicines = load_all_medicines()

    today = datetime.now().strftime("%Y-%m-%d")
    today_profit = 0
    sold_count = {}

    # Low stock notification (<10)
    low_stock_items = [item for item in items if item["stock"] < 10]

    for sale in sales:
        if sale["date"] == today:
            today_profit += sale["profit"]
            if sale["name"] not in sold_count:
                sold_count[sale["name"]] = 0
            sold_count[sale["name"]] += sale["qty"]

    return render_template_string("""
    <html>
    <head>
        <title>Simple Inventory System</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { 
                color: white; 
                text-align: center; 
                font-size: 2.5rem; 
                font-weight: 700; 
                margin-bottom: 30px; 
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; }
            .card { 
                background: white; 
                padding: 25px; 
                border-radius: 15px; 
                box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
                border: 1px solid rgba(255,255,255,0.2);
                backdrop-filter: blur(10px);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); }
            .card h2 { 
                color: #2d3748; 
                font-size: 1.4rem; 
                font-weight: 600; 
                margin-bottom: 20px; 
                display: flex; 
                align-items: center; 
                gap: 10px;
            }
            .profit-card { background: linear-gradient(135deg, #8f5be8, #764ba2); color: white; }
            .profit-card h2 { color: white; }
            .profit-amount { font-size: 2.5rem; font-weight: 700; margin: 15px 0; }
            .inventory-item { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                padding: 15px; 
                margin: 10px 0; 
                background: #f7fafc; 
                border-radius: 10px; 
                border-left: 4px solid #4299e1;
            }
            .item-name { font-weight: 600; color: #2d3748; }
            .item-details { font-size: 0.9rem; color: #718096; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #4a5568; }
            input { 
                width: 100%; 
                padding: 12px 15px; 
                border: 2px solid #e2e8f0; 
                border-radius: 8px; 
                font-size: 1rem;
                transition: border-color 0.3s ease, box-shadow 0.3s ease;
                background: white;
            }
            input:focus { 
                outline: none; 
                border-color: #4299e1; 
                box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
            }
            button { 
                background: linear-gradient(135deg, #4299e1, #3182ce); 
                color: white; 
                border: none; 
                padding: 12px 20px; 
                width: 100%; 
                border-radius: 8px; 
                font-size: 1rem; 
                font-weight: 600; 
                cursor: pointer;
                transition: all 0.3s ease;
            }
            button:hover { 
                background: linear-gradient(135deg, #3182ce, #2c5aa0); 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(66, 153, 225, 0.3);
            }
            .sold-item { 
                display: flex; 
                justify-content: space-between; 
                padding: 10px 15px; 
                background: rgba(255,255,255,0.9); 
                border-radius: 8px; 
                margin: 8px 0;
            }
            .icon { font-size: 1.2rem; }
            ul { list-style: none; }
            .no-items { 
                text-align: center; 
                padding: 30px; 
                color: #718096; 
                font-style: italic;
            }
            .edit-btn, .delete-btn {
                width: auto;
                display: inline-block;
                margin-left: 5px;
                margin-top: 5px;
                padding: 6px 12px;
                font-size: 0.9rem;
                border-radius: 6px;
            }
            .edit-btn { background: #ecc94b; color: #2d3748; }
            .edit-btn:hover { background: #f6e05e; }
            .delete-btn { background: #e53e3e; color: white; }
            .delete-btn:hover { background: #c53030; }
            .toggle-btns {
                display: flex;
                gap: 15px;
                margin-bottom: 25px;
                justify-content: center;
            }
            .toggle-btn {
                background: linear-gradient(135deg, #4299e1, #3182ce);
                color: white;
                border: none;
                padding: 12px 28px;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s, transform 0.2s;
            }
            .toggle-btn.active, .toggle-btn:focus {
                background: linear-gradient(135deg, #8f5be8, #764ba2);
                outline: none;
                transform: scale(1.04);
            }
            .toggle-section { display: none; }
            .toggle-section.active { display: block; }
            .tabbar {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100vw;
                background: #fff;
                border-top: 1.5px solid #e2e8f0;
                display: flex;
                justify-content: space-around;
                align-items: center;
                z-index: 100;
                height: 62px;
                box-shadow: 0 -2px 16px rgba(0,0,0,0.07);
            }
            .tabbar-btn {
                flex: 1;
                text-align: center;
                padding: 7px 0 0 0;
                color: #4a5568;
                font-size: 1.1rem;
                background: none;
                border: none;
                outline: none;
                font-family: inherit;
                transition: color 0.2s;
                cursor: pointer;
            }
            .tabbar-btn.active {
                color: #764ba2;
                font-weight: 700;
            }
            .tabbar-btn .icon {
                display: block;
                font-size: 1.5rem;
                margin-bottom: 2px;
            }
            @media (min-width: 769px) {
                .tabbar { display: none; }
            }
            @media (max-width: 768px) {
                body { padding-bottom: 90px !important; }
            }
        </style>
        <script>
            function showSection(id) {
                document.querySelectorAll('.toggle-section').forEach(function(sec) {
                    sec.classList.remove('active');
                });
                document.querySelectorAll('.toggle-btn').forEach(function(btn) {
                    btn.classList.remove('active');
                });
                document.querySelectorAll('.tabbar-btn').forEach(function(btn) {
                    btn.classList.remove('active');
                });
                document.getElementById(id).classList.add('active');
                var btn = document.getElementById('btn-' + id);
                if (btn) btn.classList.add('active');
                var tabBtn = document.getElementById('tab-' + id);
                if (tabBtn) tabBtn.classList.add('active');
            }
            window.onload = function() {
                showSection('inventory');
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Inventory Management 🗂️</h1>
            {% if low_stock_items %}
                <div style="background:#fff3cd;color:#856404;padding:16px;border-radius:8px;margin-bottom:20px;border:1px solid #ffeeba;">
                    <strong>⚠️ Low Stock Alert:</strong>
                    {% for item in low_stock_items %}
                        <span>{{ item.name }} ({{ item.stock }} left)</span>{% if not loop.last %}, {% endif %}
                    {% endfor %}
                </div>
            {% endif %}

            <div class="card profit-card" style="margin-bottom: 30px;">
                <h2><span class="icon">💰</span>Today's Performance</h2>
                <div class="profit-amount">MMK{{ today_profit|int }}</div>
                {% if sold_count %}
                    <h3 style="margin-top: 20px; margin-bottom: 15px; color: black;">Items Sold Today:</h3>
                    {% for name, qty in sold_count.items() %}
                        <div class="sold-item" style="color: black;">
                            <span>{{ name }}</span>
                            <span><strong>{{ qty }} sold</strong></span>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="no-items">No sales recorded today</div>
                {% endif %}
            </div>

            <div id="inventory" class="card toggle-section">
                <h2><span class="icon">📦</span>Current Inventory</h2>
                <input type="text" id="inventory-search" placeholder="Search item..." style="margin-bottom:15px;width:100%;padding:10px;border-radius:6px;border:1.5px solid #e2e8f0;">
                <div id="inventory-table-wrapper">
                {% if items %}
                    <table id="inventory-table" style="width:100%;border-collapse:collapse;">
                        <thead>
                            <tr style="background:#f1f5f9;">
                                <th style="text-align:left;padding:8px;">Name</th>
                                <th style="text-align:right;padding:8px;">Stock</th>
                                <th style="text-align:right;padding:8px;">Buy (MMK)</th>
                                <th style="text-align:right;padding:8px;">Sell (MMK)</th>
                                <th style="text-align:center;padding:8px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                        {% for item in items %}
                            <tr>
                                <td>{{ item.name }}</td>
                                <td style="text-align:right;">{{ item.stock }}</td>
                                <td style="text-align:right;">MMK{{ item.original_price|int }}</td>
                                <td style="text-align:right;">MMK{{ item.sale_price|int }}</td>
                                <td style="text-align:center;">
                                    <form action="/delete/{{ item.name }}" method="post" style="display:inline;">
                                        <button type="submit" class="delete-btn">Delete</button>
                                    </form>
                                    <a href="/edit/{{ item.name }}"><button type="button" class="edit-btn">Edit</button></a>
                                </td>
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                {% else %}
                    <div class="no-items">No items in inventory</div>
                {% endif %}
                </div>
            </div>
            <script>
            document.getElementById('inventory-search').addEventListener('input', function() {
                var filter = this.value.toLowerCase();
                document.querySelectorAll('#inventory-table tbody tr').forEach(function(row) {
                    row.style.display = row.children[0].textContent.toLowerCase().includes(filter) ? '' : 'none';
                });
            });
            </script>

            <div id="add" class="card toggle-section">
                <h2><span class="icon">➕</span>Add New Item</h2>
                <form action="/add" method="post">
                    <div class="form-group">
                        <label for="name">Item Name</label>
                        <select id="name-select" name="name_select" onchange="onMedicineSelect()" style="width:100%;padding:12px 15px;border:2px solid #e2e8f0;border-radius:8px;font-size:1rem;">
                            <option value="">-- Select Medicine --</option>
                            {% for med in all_medicines %}
                                <option value="{{ med }}">{{ med }}</option>
                            {% endfor %}
                            <option value="__custom__">Other (Type manually)</option>
                        </select>
                        <input id="name" name="name" placeholder="Enter item name" style="margin-top:8px;" required>
                    </div>
                    <div class="form-group">
                        <label for="stock">Initial Stock</label>
                        <input id="stock" name="stock" placeholder="Enter quantity" type="number" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="buy">Purchase Price (MMK)</label>
                        <input id="buy" name="buy" placeholder="0.00" type="number" step="0.01" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="sell">Selling Price (MMK)</label>
                        <input id="sell" name="sell" placeholder="0.00" type="number" step="0.01" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="expiry">Expiry Date (optional)</label>
                        <input id="expiry" name="expiry" type="date">
                    </div>
                    <button type="submit">Add to Inventory</button>
                </form>
                <script>
                function onMedicineSelect() {
                    var sel = document.getElementById('name-select');
                    var input = document.getElementById('name');
                    if(sel.value && sel.value !== "__custom__") {
                        input.value = sel.value;
                        input.readOnly = true;
                    } else if(sel.value === "__custom__") {
                        input.value = "";
                        input.readOnly = false;
                        input.focus();
                    } else {
                        input.value = "";
                        input.readOnly = false;
                    }
                }
                </script>
            </div>

            <div id="sale" class="card toggle-section">
                <h2><span class="icon">🛒</span>Process Sale</h2>
                <form action="/sell" method="post">
                    <div class="form-group">
                        <label for="sell-name">Item Name</label>
                        <select id="sell-name" name="name" required style="width:100%;padding:12px 15px;border:2px solid #e2e8f0;border-radius:8px;font-size:1rem;">
                            <option value="">-- Select Item --</option>
                            {% for item in items %}
                                <option value="{{ item.name }}" data-price="{{ item.sale_price }}">{{ item.name }} (Stock: {{ item.stock }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="qty">Quantity to Sell</label>
                        <input id="qty" name="qty" placeholder="Enter quantity" type="number" min="1" required>
                    </div>
                    <div class="form-group">
                        <label>Total Price (MMK)</label>
                        <div id="total-price" style="font-weight:700;font-size:1.2rem;">MMK0</div>
                    </div>
                    <button type="submit">Complete Sale</button>
                </form>
                <script>
                function updateTotalPrice() {
                    var select = document.getElementById('sell-name');
                    var qtyInput = document.getElementById('qty');
                    var totalDiv = document.getElementById('total-price');
                    if (!select || !qtyInput || !totalDiv) return;
                    var qty = parseInt(qtyInput.value) || 0;
                    var price = 0;
                    if (select.value) {
                        var selectedOption = select.options[select.selectedIndex];
                        price = parseFloat(selectedOption.getAttribute('data-price')) || 0;
                    }
                    var total = qty * price;
                    totalDiv.innerText = 'MMK' + total;
                }
                document.getElementById('sell-name').addEventListener('change', updateTotalPrice);
                document.getElementById('qty').addEventListener('input', updateTotalPrice);
                document.getElementById('qty').addEventListener('change', updateTotalPrice);
                updateTotalPrice();
                </script>
            </div>
        </div>
        <!-- Bottom Tab Bar -->
        <nav class="tabbar">
            <button class="tabbar-btn" id="tab-inventory" onclick="showSection('inventory')">
                <span class="icon">📦</span>
                <span style="font-size:0.98rem;">Inventory</span>
            </button>
            <button class="tabbar-btn" id="tab-add" onclick="showSection('add')">
                <span class="icon">➕</span>
                <span style="font-size:0.98rem;">Add</span>
            </button>
            <button class="tabbar-btn" id="tab-sale" onclick="showSection('sale')">
                <span class="icon">🛒</span>
                <span style="font-size:0.98rem;">Sale</span>
            </button>
        </nav>
        <script>
    function updateTotalPrice() {
        var select = document.getElementById('sell-name');
        var qtyInput = document.getElementById('qty');
        var totalDiv = document.getElementById('total-price');
        if (!select || !qtyInput || !totalDiv) return;
        var qty = parseInt(qtyInput.value) || 0;
        var price = 0;
        if (select.value) {
            var selectedOption = select.options[select.selectedIndex];
            price = parseFloat(selectedOption.getAttribute('data-price')) || 0;
        }
        var total = qty * price;
        totalDiv.innerText = 'MMK' + total;
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Tab bar activation
        document.querySelectorAll('.tabbar-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.tabbar-btn').forEach(function(b) {
                    b.classList.remove('active');
                });
                btn.classList.add('active');
            });
        });
        // Always update price on load and on input
        var select = document.getElementById('sell-name');
        var qtyInput = document.getElementById('qty');
        if (select) select.addEventListener('change', updateTotalPrice);
        if (qtyInput) qtyInput.addEventListener('input', updateTotalPrice);
        updateTotalPrice();
    });
</script>
<script>
    // Request notification permission on page load
    document.addEventListener('DOMContentLoaded', function() {
        if ("Notification" in window && Notification.permission !== "granted") {
            Notification.requestPermission();
        }
        // If there are low stock items, show a notification
        {% if low_stock_items %}
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification("Low Stock Alert", {
                body: "{% for item in low_stock_items %}{{ item.name }} ({{ item.stock }} left){% if not loop.last %}, {% endif %}{% endfor %}"
            });
        }
        {% endif %}
    });
</script>
    </body>
    </html>
    """,
        items=items,
        today_profit=today_profit,
        sold_count=sold_count,
        low_stock_items=low_stock_items,
        all_medicines=all_medicines
    )

@app.route("/add", methods=["POST"])
def add():
    items = load_items()
    items.append({
        "name": request.form["name"],
        "stock": int(request.form["stock"]),
        "original_price": float(request.form["buy"]),
        "sale_price": float(request.form["sell"]),
        "expiry": request.form.get("expiry", "")
    })
    save_items(items)
    return redirect("/")

@app.route("/edit/<name>", methods=["GET", "POST"])
def edit(name):
    items = load_items()
    item = next((i for i in items if i["name"].lower() == name.lower()), None)
    if not item:
        return redirect("/")
    if request.method == "POST":
        item["name"] = request.form["name"]
        item["stock"] = int(request.form["stock"])
        item["original_price"] = float(request.form["buy"])
        item["sale_price"] = float(request.form["sell"])
        item["expiry"] = request.form.get("expiry", "")
        save_items(items)
        return redirect("/")
    return render_template_string("""
        <html>
        <head>
            <title>Edit Item</title>
            <style>
                body { font-family: 'Inter', sans-serif; background: #f7fafc; padding: 40px; }
                .edit-form { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);}
                .form-group { margin-bottom: 18px; }
                label { display: block; margin-bottom: 6px; font-weight: 500; color: #4a5568; }
                input { width: 100%; padding: 10px 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 1rem; }
                button { background: #4299e1; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }
                button:hover { background: #3182ce; }
            </style>
        </head>
        <body>
            <form class="edit-form" method="post">
                <h2>Edit Item</h2>
                <div class="form-group">
                    <label for="name">Item Name</label>
                    <input id="name" name="name" value="{{item.name}}" required>
                </div>
                <div class="form-group">
                    <label for="stock">Stock</label>
                    <input id="stock" name="stock" type="number" value="{{item.stock}}" required>
                </div>
                <div class="form-group">
                    <label for="buy">Purchase Price (MMK)</label>
                    <input id="buy" name="buy" type="number" step="0.01" value="{{item.original_price}}" required>
                </div>
                <div class="form-group">
                    <label for="sell">Selling Price (MMK)</label>
                    <input id="sell" name="sell" type="number" step="0.01" value="{{item.sale_price}}" required>
                </div>
                <div class="form-group">
                    <label for="expiry">Expiry Date (optional)</label>
                    <input id="expiry" name="expiry" type="date" value="{{item.expiry}}">
                </div>
                <button type="submit">Save</button>
            </form>
        </body>
        </html>
    """, item=item)

@app.route("/delete/<name>", methods=["POST"])
def delete(name):
    # Confirm deletion via POST parameter
    if request.form.get("confirm") == "yes":
        items = load_items()
        items = [i for i in items if i["name"].lower() != name.lower()]
        save_items(items)
        return redirect("/")
    else:
        # Show confirmation page
        return render_template_string("""
        <html>
        <head>
            <title>Confirm Delete</title>
            <style>
                body { font-family: 'Inter', sans-serif; background: #f7fafc; padding: 40px; }
                .confirm-box { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); text-align: center;}
                button { background: #e53e3e; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; margin: 10px;}
                button.cancel { background: #a0aec0; }
            </style>
        </head>
        <body>
            <div class="confirm-box">
                <h2>Confirm Delete</h2>
                <p>Are you sure you want to delete <strong>{{ name }}</strong> from stock?</p>
                <form method="post">
                    <input type="hidden" name="confirm" value="yes">
                    <button type="submit">Yes, Delete</button>
                    <a href="/"><button type="button" class="cancel">Cancel</button></a>
                </form>
            </div>
        </body>
        </html>
        """, name=name)

@app.route("/sell", methods=["POST"])
def sell():
    name = request.form["name"]
    qty = int(request.form["qty"])
    items = load_items()

    for item in items:
        if item["name"].lower() == name.lower():
            if item["stock"] >= qty:
                item["stock"] -= qty
                profit = (item["sale_price"] - item["original_price"]) * qty
                record_sale(item["name"], qty, profit)
                save_items(items)
                break
    return redirect("/")

@app.route("/profit")
def profit():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    sales = load_sales()
    profit = sum(s["profit"] for s in sales if s["date"] == date)
    return f"Profit for {date}: MMK{int(profit)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
