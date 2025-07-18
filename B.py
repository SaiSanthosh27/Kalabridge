import streamlit as st
import sqlite3
import os

# ---------------- DATABASE SETUP ----------------
DB_PATH = "telangana.db"

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS districts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        district_id INTEGER,
        category_name TEXT,
        FOREIGN KEY(district_id) REFERENCES districts(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        product_name TEXT,
        description TEXT,
        image_data BLOB,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )""")
    conn.commit()
    conn.close()

create_tables()

# ---------------- FUNCTIONS ----------------
def add_district(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO districts(name) VALUES(?)", (name,))
    conn.commit()
    conn.close()

def add_category(district_name, category_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM districts WHERE name=?", (district_name,))
    district_id = cursor.fetchone()
    if district_id:
        cursor.execute("INSERT INTO categories(district_id, category_name) VALUES(?, ?)", (district_id[0], category_name))
        conn.commit()
    conn.close()

def add_product(category_id, product_name, description, image_bytes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products(category_id, product_name, description, image_data)
        VALUES(?, ?, ?, ?)""", (category_id, product_name, description, image_bytes))
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT d.name, c.category_name, p.product_name
    FROM districts d
    JOIN categories c ON d.id = c.district_id
    JOIN products p ON c.id = p.category_id
    """)
    data = cursor.fetchall()
    conn.close()
    return data

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="Telangana Products Explorer", page_icon="🌾", layout="wide")
menu = st.sidebar.radio("Navigation", ["Home", "Add Data", "View by District"])

# ---------------- HOME PAGE ----------------
if menu == "Home":
    st.title("🌾 Telangana Famous Products")
    st.subheader("Explore Products by District")

    data = get_all_data()
    if data:
        grouped = {}
        for district, category, product in data:
            grouped.setdefault(district, {}).setdefault(category, []).append(product)

        for district, categories in grouped.items():
            with st.expander(f"📍 {district}"):
                for category, products in categories.items():
                    # CORRECTED LINE BELOW:
                    st.write(f"**{category}**: {', '.join(products)}")
    else:
        st.info("No data available. Please add data in 'Add Data' section.")

# ---------------- ADD DATA PAGE ----------------
elif menu == "Add Data":
    st.header("Add New Data")

    # Add District
    with st.form("add_district_form"):
        district_name = st.text_input("District Name")
        submitted = st.form_submit_button("Add District")
        if submitted and district_name:
            add_district(district_name)
            st.success(f"✅ District '{district_name}' added!")

    st.write("---")

    # Add Category
    with st.form("add_category_form"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM districts")
        district_list = [row[0] for row in cursor.fetchall()]
        conn.close()

        if district_list:
            selected_district = st.selectbox("Select District", district_list)
            category_name = st.text_input("Category Name")
            cat_submitted = st.form_submit_button("Add Category")
            if cat_submitted and selected_district and category_name:
                add_category(selected_district, category_name)
                st.success(f"✅ Category '{category_name}' added to {selected_district}")
        else:
            st.warning("Please add districts first.")

    st.write("---")

    # Add Product
    with st.form("add_product_form"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.id, c.category_name, d.name 
        FROM categories c 
        JOIN districts d ON c.district_id = d.id
        """)
        category_list = [(row[0], f"{row[2]} - {row[1]}") for row in cursor.fetchall()]
        conn.close()

        if category_list:
            category_dict = {label: cat_id for cat_id, label in category_list}
            selected_category_label = st.selectbox("Select Category", list(category_dict.keys()))
            product_name = st.text_input("Product Name")
            product_description = st.text_area("Product Description")
            product_image = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"])

            prod_submitted = st.form_submit_button("Add Product")
            if prod_submitted and selected_category_label and product_name:
                image_bytes = product_image.getvalue() if product_image else None
                add_product(
                    category_dict[selected_category_label],
                    product_name,
                    product_description,
                    image_bytes
                )
                st.success(f"✅ Product '{product_name}' added!")
        else:
            st.warning("Please add categories first.")

# ---------------- VIEW BY DISTRICT ----------------
elif menu == "View by District":
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM districts")
    districts = [row[0] for row in cursor.fetchall()]
    conn.close()

    if districts:
        selected_district = st.selectbox("Select District", districts)
        if selected_district:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.category_name, p.product_name, p.description, p.image_data
            FROM districts d
            JOIN categories c ON d.id = c.district_id
            JOIN products p ON c.id = p.category_id
            WHERE d.name = ?
            """, (selected_district,))
            rows = cursor.fetchall()
            conn.close()

            if rows:
                st.write(f"### 📍 {selected_district}")
                category_dict = {}
                for category, product, description, image in rows:
                    category_dict.setdefault(category, []).append((product, description, image))

                for category, products in category_dict.items():
                    st.markdown(f"#### 🏷 {category}")
                    for product_name, description, image_data in products:
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if image_data:
                                st.image(image_data, use_column_width=True)
                        with col2:
                            st.write(f"**{product_name}**") # Bolding product name for consistency
                            st.caption(description)
                    st.write("---")
            else:
                st.info("No products available for this district.")
    else:
        st.warning("Please add districts first.")