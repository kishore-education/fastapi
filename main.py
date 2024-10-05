from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlitecloud
import logging

app = FastAPI()
DATABASE_URL = "sqlitecloud://ce3yvllesk.sqlite.cloud:8860/gass?apikey=kOt8yvfwRbBFka2FXT1Q1ybJKaDEtzTya3SWEGzFbvE"

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class User(BaseModel):
    username: str
    name: str
    mobile_number: str
    address: str
    gas_name: str
    alternate_mobile_number: str

class UserSignIn(BaseModel):
    mobile_number: str
    gas_name: str

class Booking(BaseModel):
    username: str
    name: str
    mobile_number: str
    address: str
    gas_name: str
    alternate_mobile_number: str
    GasTheySelected: str

def create_tables():
    conn = sqlitecloud.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        name TEXT,
        mobile_number TEXT,
        address TEXT,
        gas_name TEXT,
        alternate_mobile_number TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Bookings (
        id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        mobile_number TEXT,
        address TEXT,
        gas_name TEXT,
        alternate_mobile_number TEXT,
        GasTheySelected TEXT,
        status TEXT DEFAULT 'progress'
    )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.post("/signup")
async def create_user(user: User):
    conn = sqlitecloud.connect(DATABASE_URL)
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO users (username, name, mobile_number, address, gas_name, alternate_mobile_number)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.username, user.name, user.mobile_number, user.address, user.gas_name, user.alternate_mobile_number))
        conn.commit()
    except sqlitecloud.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already registered")
    finally:
        conn.close()
    return {"message": "User created successfully"}

@app.post("/signin")
async def sign_in(user: UserSignIn):
    conn = sqlitecloud.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE mobile_number = ? AND gas_name = ?', (user.mobile_number, user.gas_name))
    result = cursor.fetchone()
    id,un,n,mn,a,gn,amn=result
    conn.close()
    if not result:
        raise HTTPException(status_code=400, detail="Invalid mobile number or gas name")
    print(result)
    
    user_data = {
        "username": un,
        "name": n,
        "mobile_number": mn,
        "address": a,
        "gas_name": gn,
        "alternate_mobile_number": amn
    }
    return {"message": "Sign in successful", "user_data": user_data}

@app.post("/book")
async def create_booking(booking: Booking, request: Request):
    conn = sqlitecloud.connect(DATABASE_URL)
    cursor = conn.cursor()
    try:
        body = await request.json()
        print("Request body:", body)  # Log the request body
        print("Booking data received:", booking)  # Log the booking data
        cursor.execute('''
        INSERT INTO Bookings (username, name, mobile_number, address, gas_name, alternate_mobile_number, GasTheySelected, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'progress')
        ''', (booking.username, booking.name, booking.mobile_number, booking.address, booking.gas_name, booking.alternate_mobile_number, booking.GasTheySelected))
        conn.commit()
    except sqlitecloud.IntegrityError:
        raise HTTPException(status_code=400, detail="Booking could not be created")
    finally:
        conn.close()
    return {"message": "Booking created successfully"}

@app.get("/products")
async def fetch_products():
    conn = sqlitecloud.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT id, image, name, price FROM products')
    products = cursor.fetchall()
    conn.close()
    product_list = []
    for product in products:
        id, image, name, price = product
        product_list.append({"id": id, "image": image, "name": name, "price": price})
    return product_list

# Silence passlib warnings
logging.getLogger('passlib').setLevel(logging.ERROR)
