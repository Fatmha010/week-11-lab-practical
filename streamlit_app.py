import streamlit as st
from app.database import SessionLocal
from app.models import Product, Category

# Initialize database session
@st.cache_resource
def get_db():
    return SessionLocal()

db = get_db()

# Ensure we always fetch fresh data from the database
products = db.query(Product).all()
categories = db.query(Category).all()
category_names = [c.name for c in categories]
category_map = {c.name: c.id for c in categories}
reverse_category_map = {c.id: c.name for c in categories}

st.title("🛍️ Fashion Store Management System")

# -------------------------
# ADD PRODUCT
# -------------------------
st.header("➕ Add Product")

with st.form("add_product_form"):
    name = st.text_input("Product Name")
    
    # Use categories from DB or fallback
    if category_names:
        category = st.selectbox("Category", category_names)
    else:
        category = st.selectbox("Category", ["Men", "Women", "Kids"])
        
    price = st.number_input("Price", min_value=0.0, step=1.0)
    brand = st.text_input("Brand")
    stock = st.number_input("Stock", min_value=0, step=1)
    
    submitted = st.form_submit_button("Add Product")

    if submitted:
        if name and category:
            cat_id = category_map.get(category)
            if not cat_id:
                # Create category if it doesn't exist
                new_cat = Category(name=category)
                db.add(new_cat)
                db.commit()
                cat_id = new_cat.id

            new_product = Product(
                name=name,
                category_id=cat_id,
                price=price,
                brand=brand,
                stock_quantity=stock
            )
            db.add(new_product)
            db.commit()
            st.success("Product Added Successfully!")
            st.rerun()
        else:
            st.error("Please enter a product name and category")

# -------------------------
# EDIT PRODUCT
# -------------------------
if "edit_id" in st.session_state:
    st.header("✏️ Edit Product")

    prod_id = st.session_state.edit_id
    product = db.query(Product).filter(Product.id == prod_id).first()

    if product:
        with st.form("edit_product_form"):
            new_name = st.text_input("New Name", product.name)
            
            # Find index of current category
            current_cat_name = reverse_category_map.get(product.category_id, "Men")
            try:
                cat_index = category_names.index(current_cat_name) if category_names else 0
            except ValueError:
                cat_index = 0
                
            new_category = st.selectbox("New Category", category_names if category_names else ["Men", "Women", "Kids"], index=cat_index)
            new_price = st.number_input("New Price", value=float(product.price), step=1.0)
            new_brand = st.text_input("New Brand", product.brand if product.brand else "")
            new_stock = st.number_input("New Stock", value=int(product.stock_quantity), step=1)

            col1, col2 = st.columns(2)
            with col1:
                updated = st.form_submit_button("Update Product")
            with col2:
                canceled = st.form_submit_button("Cancel")

            if updated:
                product.name = new_name
                product.price = new_price
                product.brand = new_brand
                product.stock_quantity = new_stock
                
                cat_id = category_map.get(new_category)
                if cat_id:
                    product.category_id = cat_id
                    
                db.commit()
                del st.session_state.edit_id
                st.success("Updated Successfully!")
                st.rerun()
            elif canceled:
                del st.session_state.edit_id
                st.rerun()

# -------------------------
# VIEW PRODUCTS
# -------------------------
st.header("📦 Product List")

if products:
    for product in products:
        cat_name = reverse_category_map.get(product.category_id, "Unknown")
        brand_str = f" | Brand: {product.brand}" if product.brand else ""
        st.write(f"**{product.name}** | {cat_name} | ${product.price:.2f} | Stock: {product.stock_quantity}{brand_str}")

        col1, col2 = st.columns(2)

        # DELETE
        if col1.button("Delete", key=f"del_{product.id}"):
            db.delete(product)
            db.commit()
            if "edit_id" in st.session_state and st.session_state.edit_id == product.id:
                del st.session_state.edit_id
            st.rerun()

        # EDIT
        if col2.button("Edit", key=f"edit_{product.id}"):
            st.session_state.edit_id = product.id
            st.rerun()
        
        st.divider()
else:
    st.info("No products found. Add some above!")
