# Inventory Management & Analytics Platform

## 🚀 Overview
A full-stack, AI-powered inventory management and analytics solution for SKU mapping, sales data cleaning, dashboarding, and natural language analytics.

UX Designs = [https://docs.google.com/document/d/1hGk2jaycw0RMSKKuB3XmUnB2JegFYZrqz1e8c6UdtXM/edit?usp=sharing](https://docs.google.com/document/d/1hGk2jaycw0RMSKKuB3XmUnB2JegFYZrqz1e8c6UdtXM/edit?usp=sharing)
---
## 🛠️ Tech Stack
- **Frontend:** React (with drag-and-drop uploader, authentication, AI chat widget)
- **Backend:** FastAPI (Python 3.9+)
- **SKU Mapping:** Custom Python class with regex validation, combo support, and rotating log file
- **Database:** Baserow (no-code, Airtable alternative)
- **AI Layer:** Gemini AI API (`gemini-2.0-flash` model) for text-to-SQL
- **Authentication:** HTTP Basic Auth (demo)
- **Logging:** Rotating log file for mapping steps

---

## ⚡ Features
- Upload sales data (CSV, Excel, JSON) and map SKUs to MSKUs
- Handles combo products and validates SKU format (regex)
- Logs all mapping steps with log rotation
- Pushes cleaned data to Baserow (no-code DB)
- Live dashboard (Baserow public view)
- AI-powered chat: Ask questions in plain English, get SQL and (optionally) results
- Simple login for secure access

---

## 📝 Setup Steps

### 1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. **Backend Setup**
- Create a virtual environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Set up your Gemini API key in `src/web/api.py`:
  ```python
  genai.configure(api_key="YOUR_GEMINI_API_KEY")
  ```
- Make sure you have a mapping file at `data/sample_mapping.csv`.
- Run the backend:
  ```bash
  python -m src.web.main
  ```

### 3. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```
- The app will open at [http://localhost:3000](http://localhost:3000)

### 4. **Baserow Setup**
- Sign up at [https://baserow.io/](https://baserow.io/) or self-host
- Create tables: Products, Orders, Returns
- Set up your dashboard view and make it public
- Copy the public dashboard link for the frontend

---

## 👤 User Guide

### **Login**
- Use the login form (default: `admin@example.com` / `password123`)

### **Upload & Clean Data**
- Drag and drop or select your sales data file
- Click "Upload & Clean Data"
- See cleaned data preview and mapping errors

### **Live Dashboard**
- Click "Open Live Dashboard" to view your Baserow dashboard

### **AI Chat (Natural Language Analytics)**
- Type questions like "Show me total sales by MSKU in January"
- The AI will generate SQL and (optionally) results

---

## 🧩 Customization & Extensibility
- Update SKU mapping logic in `src/data_management/sku_mapper.py`
- Change authentication in `src/web/api.py`
- Extend AI query execution to run SQL on your actual DB
- Add more chart types or analytics in the frontend

---

## 🧪 Testing
- Unit tests for core mapping logic are in `tests/`
- To run tests:
  ```bash
  pytest
  ```

---

## 📦 Deployment
- Dockerfile and cloud deployment instructions coming soon!

---

## 📚 References
- [Baserow Docs](https://baserow.io/docs/)
- [Gemini AI API](https://ai.google.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/) 
