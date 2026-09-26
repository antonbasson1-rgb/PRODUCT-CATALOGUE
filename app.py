import os
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

os.makedirs("catalogues", exist_ok=True)
os.makedirs("images", exist_ok=True)

EXCEL_FILE = Path("master_inventory.xlsx")
CATALOGUES_DIR = Path("catalogues")
IMAGES_DIR = Path("images")

REQUIRED_COLUMNS = ["Code", "Description", "Barcode", "Category", "Price", "Image_Path"]


st.set_page_config(page_title="Product Catalogue Manager", layout="wide", page_icon="📋")


def ensure_template_inventory() -> pd.DataFrame:
    if not EXCEL_FILE.exists():
        empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        empty_df.to_excel(EXCEL_FILE, index=False)
    return pd.read_excel(EXCEL_FILE)


def save_uploaded_image(uploaded_file, product_code: str) -> str:
    if uploaded_file is None:
        return ""

    extension = Path(uploaded_file.name).suffix.lower() or ".png"
    safe_name = f"{product_code.strip().replace(' ', '_')}{extension}"
    target_path = IMAGES_DIR / safe_name
    target_path.write_bytes(uploaded_file.getvalue())
    return str(target_path)


def slugify(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def generate_pdf(category_name: str, df_filtered: pd.DataFrame) -> str:
    category_slug = slugify(category_name)
    pdf_path = CATALOGUES_DIR / f"{category_slug}_catalogue.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, title=f"{category_name} Catalogue")
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CatalogTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=15,
    )
    cell_text_style = ParagraphStyle("CellText", parent=styles["Normal"], fontSize=9, leading=12)
    cell_header_style = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontSize=10,
        bold=True,
        textColor=colors.white,
    )

    story.append(Paragraph(f"PRODUCT CATALOGUE: {category_name.upper()}", title_style))
    story.append(Spacer(1, 10))

    table_data = [[
        Paragraph("Image", cell_header_style),
        Paragraph("Product Details", cell_header_style),
        Paragraph("Price (ZAR)", cell_header_style),
    ]]

    for _, row in df_filtered.iterrows():
        image_value = row.get("Image_Path")
        if pd.notna(image_value) and str(image_value).strip():
            image_path = str(image_value)
            if os.path.exists(image_path):
                prod_img = Image(image_path, width=60, height=60)
            else:
                prod_img = Paragraph("<b>[ No Image ]</b>", cell_text_style)
        else:
            prod_img = Paragraph("<b>[ No Image ]</b>", cell_text_style)

        details = (
            f"<b>Code:</b> {row.get('Code', '')}<br/>"
            f"<b>Description:</b> {row.get('Description', '')}<br/>"
            f"<b>Barcode:</b> {row.get('Barcode', '')}"
        )
        price = float(row.get("Price", 0) or 0)
        price_text = f"<b>R {price:.2f}</b>"

        table_data.append([
            prod_img,
            Paragraph(details, cell_text_style),
            Paragraph(price_text, cell_text_style),
        ])

    product_table = Table(table_data, colWidths=[80, 320, 100])
    product_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))

    story.append(product_table)
    doc.build(story)
    return str(pdf_path)


st.title("🇿🇦 Product Catalogue & PDF Generator")

# Load data
inventory = ensure_template_inventory()
if inventory.empty:
    inventory = pd.DataFrame(columns=REQUIRED_COLUMNS)

# Sidebar: add a product
st.sidebar.header("📦 Add New Product")
with st.sidebar.form("product_form", clear_on_submit=True):
    new_code = st.text_input("Product Code")
    new_desc = st.text_input("Description")
    new_barcode = st.text_input("Barcode / SKU")
    new_cat = st.text_input("Category")
    new_price = st.number_input("Selling Price (ZAR)", min_value=0.0, step=0.50)
    uploaded_image = st.file_uploader("Product Image", type=["png", "jpg", "jpeg", "webp"])
    submitted = st.form_submit_button("Save Product to Database")

    if submitted and new_code and new_cat:
        image_path = save_uploaded_image(uploaded_image, new_code) if uploaded_image is not None else ""
        new_row = pd.DataFrame([{
            "Code": new_code,
            "Description": new_desc,
            "Barcode": new_barcode,
            "Category": new_cat,
            "Price": new_price,
            "Image_Path": image_path,
        }])
        inventory = pd.concat([inventory, new_row], ignore_index=True)
        inventory.to_excel(EXCEL_FILE, index=False)
        st.sidebar.success(f"Product {new_code} added successfully!")
        st.rerun()

# Main layout
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("📋 Current Inventory Records")
    if inventory.empty:
        st.info("Your inventory database is currently empty. Use the sidebar to populate products.")
    else:
        st.dataframe(inventory, use_container_width=True, hide_index=True)

with right_col:
    st.subheader("⚡ Export & Share Catalogues")
    if inventory.empty:
        st.info("Add at least one product before generating a PDF catalogue.")
    else:
        categories = inventory["Category"].dropna().astype(str).unique()
        selected_category = st.selectbox("Select a category to generate", options=sorted(categories))

        if selected_category:
            filtered_df = inventory[inventory["Category"].astype(str) == selected_category]
            st.metric("Total items in category", value=len(filtered_df))

            if st.button(f"Build {selected_category} PDF File"):
                with st.spinner("Compiling PDF catalogue..."):
                    pdf_path = generate_pdf(selected_category, filtered_df)
                st.success(f"Success! Generated: `{pdf_path}`")

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=f,
                        file_name=Path(pdf_path).name,
                        mime="application/pdf",
                    )

                # Shared links
                message = (
                    f"Hi! Please find attached our latest {selected_category} catalog updates. "
                    f"You can preview file: {Path(pdf_path).name}"
                )
                whatsapp_url = f"https://wa.me/?text={quote(message)}"
                email_subject = quote(f"{selected_category} Product Catalogue")
                email_body = quote(message)
                email_url = f"mailto:?subject={email_subject}&body={email_body}"

                st.write("---")
                st.markdown("#### 🔗 Share Catalogue")
                st.markdown(f"[💬 Share via WhatsApp]({whatsapp_url})")
                st.markdown(f"[✉️ Draft email]({email_url})")

st.caption("Built for managing inventory and generating printable PDF catalogues.")
