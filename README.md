# Product Catalogue Manager

This project generates printable PDF catalogues from a master inventory spreadsheet.

## Features
- Add products from the Streamlit interface
- Maintain inventory in `master_inventory.xlsx`
- Group products by category
- Generate a PDF catalogue per category
- Download generated files directly from the app
- Share catalogues via WhatsApp or email

## Run locally

1. Create a virtual environment
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app:
   ```bash
   streamlit run app.py
   ```

## File structure
- `app.py` – Streamlit app entrypoint
- `master_inventory.xlsx` – inventory data file created automatically if missing
- `catalogues/` – generated PDFs
- `images/` – uploaded product images

## Notes
- The app creates `master_inventory.xlsx` automatically the first time it runs.
- Product images can be uploaded directly in the sidebar form or referenced via a local file path if needed.
