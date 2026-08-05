import csv
import os

class DataLoader:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.orders = {}           # order_id -> dict
        self.customers = {}        # customer_id -> dict
        self.customer_orders = {}  # customer_unique_id -> list of order_ids
        self.order_items = {}      # order_id -> list of dicts
        self.order_payments = {}   # order_id -> list of dicts
        self.products = {}         # product_id -> dict
        self.category_translation = {} # category_pt -> category_en

    def load_all(self):
        print("Loading Olist datasets...")
        self._load_translations()
        self._load_products()
        self._load_customers()
        self._load_orders()
        self._load_order_items()
        self._load_order_payments()
        print(f"Data loading complete: {len(self.orders)} orders, {len(self.customers)} customers indexed.")

    def _load_translations(self):
        filepath = os.path.join(self.data_dir, "product_category_name_translation.csv")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pt = row.get("product_category_name", "").strip()
                en = row.get("product_category_name_english", "").strip()
                if pt and en:
                    self.category_translation[pt] = en

    def _load_products(self):
        filepath = os.path.join(self.data_dir, "olist_products_dataset.csv")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("product_id", "").strip()
                cat_pt = row.get("product_category_name", "").strip()
                # Use exact product_category_name as present in olist_products_dataset.csv
                row["category_name"] = cat_pt
                self.products[pid] = row

    def _load_customers(self):
        filepath = os.path.join(self.data_dir, "olist_customers_dataset.csv")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get("customer_id", "").strip()
                self.customers[cid] = row

    def _load_orders(self):
        filepath = os.path.join(self.data_dir, "olist_orders_dataset.csv")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                oid = row.get("order_id", "").strip()
                cid = row.get("customer_id", "").strip()
                self.orders[oid] = row
                
                # Index customer history
                cust_info = self.customers.get(cid, {})
                c_unique_id = cust_info.get("customer_unique_id", "")
                if c_unique_id:
                    if c_unique_id not in self.customer_orders:
                        self.customer_orders[c_unique_id] = []
                    self.customer_orders[c_unique_id].append(oid)

    def _load_order_items(self):
        filepath = os.path.join(self.data_dir, "olist_order_items_dataset.csv")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                oid = row.get("order_id", "").strip()
                if oid not in self.order_items:
                    self.order_items[oid] = []
                self.order_items[oid].append(row)

    def _load_order_payments(self):
        filepath = os.path.join(self.data_dir, "olist_order_payments_dataset.csv")
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                oid = row.get("order_id", "").strip()
                if oid not in self.order_payments:
                    self.order_payments[oid] = []
                self.order_payments[oid].append(row)

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def get_customer_by_id(self, customer_id):
        return self.customers.get(customer_id)

    def get_customer_orders(self, customer_unique_id):
        return self.customer_orders.get(customer_unique_id, [])

    def get_items(self, order_id):
        return self.order_items.get(order_id, [])

    def get_payments(self, order_id):
        return self.order_payments.get(order_id, [])

    def get_product(self, product_id):
        return self.products.get(product_id)
