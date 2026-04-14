from pathlib import Path
import shutil
import sqlite3
import uuid

from fastapi import FastAPI, Form, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="School Supply Wizard")

# ---------- FILES ----------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ---------- DATABASE ----------
DB_PATH = BASE_DIR / "listings.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            price REAL,
            school TEXT,
            seller_name TEXT,
            seller_email TEXT,
            image_path TEXT
        )
        """
    )

    conn.commit()
    conn.close()


init_db()

# ---------- STYLES ----------
def page_wrapper(content: str, title: str = "School Supply Wizard") -> str:
    return f"""
    <html>
    <head>
    <title>{title}</title>
    <style>
    body {{
        font-family: Arial;
        background: #eef3f8;
        margin: 0;
        padding: 10px;
    }}

    .page {{
        max-width: 1200px;
        margin: auto;
    }}

    .grid {{
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 10px;
    }}

    .left-column {{
        display: flex;
        flex-direction: column;
        gap: 10px;
    }}

    .card {{
        background: white;
        padding: 12px;
        border-radius: 12px;
    }}

    h1 {{
        margin: 0;
        color: #2563eb;
    }}

    h2 {{
        color: #2563eb;
    }}

    .subtitle {{
        color: gray;
        font-size: 14px;
    }}

    .button {{
        background: #2563eb;
        color: white;
        padding: 6px 10px;
        border-radius: 6px;
        text-decoration: none;
        display: inline-block;
        margin-top: 5px;
    }}

    /* 🔥 GRID FIX */
    .listings-container {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }}

    .listing {{
        background: white;
        padding: 10px;
        border-radius: 10px;
        border-top: 1px solid #e5e7eb;
    }}

    .listing-title {{
        font-weight: bold;
    }}

    .price {{
        color: #2563eb;
        font-weight: bold;
    }}

    .badge {{
        background: #dbeafe;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 12px;
    }}

    .listing-image {{
        width: 100%;
        max-width: 150px;
        border-radius: 10px;
    }}

    .actions {{
        margin-top: 5px;
    }}

    .button-danger {{
        background: red;
        color: white;
        border: none;
        padding: 4px 8px;
        border-radius: 6px;
    }}

    @media (max-width: 900px) {{
        .grid {{
            grid-template-columns: 1fr;
        }}

        .listings-container {{
            grid-template-columns: 1fr;
        }}
    }}

    </style>
    </head>

    <body>
    <div class="page">
    {content}
    </div>
    </body>
    </html>
    """


# ---------- HOME ----------
@app.get("/", response_class=HTMLResponse)
def home():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM listings ORDER BY id DESC")
    listings = c.fetchall()
    conn.close()

    listings_html = ""

    for listing in listings:
        image_html = (
            f'<img class="listing-image" src="{listing["image_path"]}">'
            if listing["image_path"]
            else ""
        )

        listings_html += f"""
        <div class="listing">
            <div class="listing-title">{listing["title"]}</div>
            <div><span class="badge">{listing["school"]}</span></div>
            <div class="price">${listing["price"]}</div>
            {image_html}
            <p>{listing["description"]}</p>
            <b>Seller:</b> {listing["seller_name"]}<br>
            <b>Contact:</b> {listing["seller_email"]}

            <div class="actions">
                <a class="button" href="/edit/{listing["id"]}">Edit</a>
                <form action="/delete/{listing["id"]}" method="post" style="display:inline;">
                    <button class="button-danger">Delete</button>
                </form>
            </div>
        </div>
        """

    content = f"""
    <div class="grid">
        <div class="left-column">

            <div class="card">
                <h1>School Supply Wizard</h1>
                <div class="subtitle">Buy, sell, or donate supplies</div>
                <a class="button" href="/new">Post a Listing</a>
            </div>

            <div class="card">
                <h2>Available Listings</h2>
                <div class="listings-container">
                    {listings_html}
                </div>
            </div>

        </div>

        <div class="card">
            <h2>Quick Tips</h2>
            <p>Post clear photos and details</p>
        </div>
    </div>
    """

    return page_wrapper(content)


# ---------- CREATE ----------
@app.get("/new", response_class=HTMLResponse)
def new_form():
    return page_wrapper("""
    <div class="card">
        <h1>New Listing</h1>
        <form method="post" enctype="multipart/form-data">
            <input name="title" placeholder="Title"><br>
            <textarea name="description"></textarea><br>
            <input name="price"><br>
            <input name="school"><br>
            <input name="seller_name"><br>
            <input name="seller_email"><br>
            <input type="file" name="image"><br>
            <button>Create</button>
        </form>
    </div>
    """)


@app.post("/new")
async def create(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    school: str = Form(...),
    seller_name: str = Form(...),
    seller_email: str = Form(...),
    image: UploadFile = File(None),
):
    image_path = None

    if image:
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = UPLOADS_DIR / filename
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = f"/uploads/{filename}"

    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO listings VALUES (NULL,?,?,?,?,?,?,?)",
        (title, description, price, school, seller_name, seller_email, image_path),
    )
    conn.commit()
    conn.close()

    return RedirectResponse("/", 303)