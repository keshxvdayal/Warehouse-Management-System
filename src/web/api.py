import os
from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
from src.data_management.sku_mapper import SkuMapper
import tempfile
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import google.generativeai as genai
import requests
from pydantic import BaseModel
import json
from pathlib import Path

# Initialize FastAPI app
app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# User data model
class UserSignup(BaseModel):
    email: str
    password: str
    full_name: str

# File to store users
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Initialize users from file
USERS = load_users()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if USERS.get(credentials.username) == credentials.password:
        return credentials.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

@app.post("/login/")
def login(credentials: HTTPBasicCredentials = Depends(security)):
    return {"message": "Login successful"}

@app.post("/signup/")
async def signup(user_data: UserSignup):
    # Check if user already exists
    if user_data.email in USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Add new user
    USERS[user_data.email] = user_data.password
    save_users(USERS)
    
    return {"message": "Registration successful"}

BASEROW_API_URL = "https://api.baserow.io/api/database/rows/table/{table_id}/?user_field_names=true"
BASEROW_API_TOKEN = "lQerNXuevv64EPuDnbnrAbPBe3hI16wC"

def push_to_baserow(table_id, records):
    url = BASEROW_API_URL.format(table_id=table_id)
    headers = {"Authorization": f"Token {BASEROW_API_TOKEN}"}
    for record in records:
        requests.post(url, json=record, headers=headers)

# Load mapping file once (can be improved for dynamic mapping uploads)
MAPPING_FILE = os.getenv("MAPPING_FILE", "data/sample_mapping.csv")
sku_mapper = SkuMapper(MAPPING_FILE)

@app.post("/upload_sales_data/")
async def upload_sales_data(file: UploadFile = File(...), user: str = Depends(authenticate)):
    # Save uploaded file to a temp location
    suffix = os.path.splitext(file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        # Load sales data
        if suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(tmp_path)
        elif suffix == ".json":
            df = pd.read_json(tmp_path)
        else:
            df = pd.read_csv(tmp_path)
        # Map SKUs to MSKUs
        cleaned_df = sku_mapper.process_inventory_data(df)
        errors = sku_mapper.get_error_log()
        
        # Push to Baserow
        table_id = 531652  # from your URL
        push_to_baserow(table_id, cleaned_df.to_dict(orient="records"))
        
        # Return cleaned data and errors as JSON
        return JSONResponse({
            "cleaned_data": cleaned_df.to_dict(orient="records"),
            "errors": errors
        })
    finally:
        os.remove(tmp_path)

# Set up Gemini API
genai.configure(api_key="AIzaSyCum2QctzqCOtfEkuavUoFYhdrXAAKfUA0")

@app.post("/ai_query/")
async def ai_query(
    question: str = Body(..., embed=True)
):
    try:
        # Initialize the Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create the prompt
        prompt = f"You are a data analyst. Convert this question to SQL for a PostgreSQL/Baserow database: {question}"
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract the SQL from the response
        sql = response.text.strip()
        
        return {"sql": sql, "result": "Query execution not implemented in this demo."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating SQL: {str(e)}"
        ) 