from pathlib import Path
import shutil
import sqlite3
import uuid

from fastapi import FastAPI, Form, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="School Supply Wizard")


# ---------- FILES / STATIC ----------
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
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            school TEXT NOT NULL,
            seller_name TEXT NOT NULL,
            seller_email TEXT NOT NULL,
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
                    font-family: Arial, sans-serif;
                    background: #eef3f8;
                    margin: 0;
                    padding: 8px 16px 8px 16px;
                    color: #1f2937;
                }}
                .page {{
                    max-width: 1280px;
                    margin: 0 auto;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 8px;
                    align-items: start;
                    margin-bottom: 0;
                }}
                .left-column {{
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }}
                .card {{
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
                    padding: 12px;
                    margin-bottom: 0;
                }}
                h1 {{
                    margin: 0 0 2px 0;
                    font-size: 46px;
                    color: #2450d3;
                    letter-spacing: -1px;
                }}
                h2, h3 {{
                    color: #2450d3;
                    margin-top: 0;
                }}
                .subtitle {{
                    color: #6b7280;
                    margin-bottom: 4px;
                    font-size: 16px;
                    line-height: 1.4;
                }}
                label {{
                    display: block;
                    font-weight: 700;
                    margin-bottom: 8px;
                    font-size: 18px;
                }}
                input, textarea, select {{
                    width: 100%;
                    padding: 14px 16px;
                    border: 1px solid #d1d5db;
                    border-radius: 12px;
                    box-sizing: border-box;
                    margin-bottom: 10px;
                    font-size: 16px;
                    background: #fff;
                }}
                input:focus, textarea:focus, select:focus {{
                    outline: none;
                    border-color: #2450d3;
                    box-shadow: 0 0 0 3px rgba(36, 80, 211, 0.12);
                }}
                textarea {{
                    min-height: 120px;
                    resize: vertical;
                }}
                .row {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                }}
                .button, button {{
                    background: #2563eb;
                    color: white;
                    border: none;
                    padding: 12px 16px;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: 700;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin-bottom: 0;
                }}
                .button:hover, button:hover {{
                    background: #1d4ed8;
                }}
                .button-secondary {{
                    background: #e5e7eb;
                    color: #111827;
                }}
                .button-secondary:hover {{
                    background: #d1d5db;
                }}
                .button-danger {{
                    background: #dc2626;
                }}
                .button-danger:hover {{
                    background: #b91c1c;
                }}
                .muted {{
                    color: #6b7280;
                }}
                .listing {{
                    border-top: 1px solid #e5e7eb;
                    padding-top: 12px;
                    margin-top: 12px;
                }}
                .listing:first-child {{
                    border-top: none;
                    padding-top: 0;
                    margin-top: 0;
                }}
                .listing-title {{
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    color: #111827;
                }}
                .listing-meta {{
                    color: #4b5563;
                    margin-bottom: 10px;
                }}
                .price {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #2563eb;
                    margin-bottom: 10px;
                }}
                .badge {{
                    display: inline-block;
                    background: #dbeafe;
                    color: #1d4ed8;
                    border-radius: 999px;
                    padding: 6px 10px;
                    font-size: 13px;
                    font-weight: 700;
                    margin-right: 8px;
                    margin-bottom: 10px;
                }}
                .actions {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                    margin-top: 8px;
                }}
                .listing-image {{
                    width: 100%;
                    max-width: 320px;
                    border-radius: 14px;
                    border: 1px solid #e5e7eb;
                    margin: 8px 0;
                }}
                .sidebar-section {{
                    margin-top: 16px;
                    padding-top: 12px;
                    border-top: 1px solid #e5e7eb;
                }}
                .empty {{
                    color: #6b7280;
                    font-size: 18px;
                }}
                form.inline {{
                    display: inline;
                    margin: 0;
                }}
                @media (max-width: 900px) {{
                    .grid, .row {{
                        grid-template-columns: 1fr;
                    }}
                    h1 {{
                        font-size: 40px;
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


# ---------- HELPERS ----------
def save_uploaded_image(image: UploadFile | None) -> str | None:
    if not image or not image.filename:
        return None

    suffix = Path(image.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    filename = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOADS_DIR / filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return f"/uploads/{filename}"


def delete_image_file(image_path: str | None) -> None:
    if not image_path:
        return

    filename = image_path.replace("/uploads/", "").strip()
    file_path = UPLOADS_DIR / filename
    if file_path.exists():
        file_path.unlink()


# ---------- ROUTES ----------
@app.get("/", response_class=HTMLResponse)
def home() -> str:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM listings ORDER BY id DESC")
    listings = c.fetchall()
    conn.close()

    if listings:
        listings_html = ""
        for listing in listings:
            image_html = (
                f'<img class="listing-image" src="{listing["image_path"]}" alt="{listing["title"]}">'
                if listing["image_path"]
                else ""
            )

            price_text = "Free" if float(listing["price"]) == 0 else f'${float(listing["price"]):,.2f}'

            listings_html += f"""
            <div class="listing">
                <div class="listing-title">{listing["title"]}</div>
                <div>
                    <span class="badge">{listing["school"]}</span>
                </div>
                <div class="price">{price_text}</div>
                {image_html}
                <p>{listing["description"]}</p>
                <div class="listing-meta">
                    <b>Seller:</b> {listing["seller_name"]}<br>
                    <b>Contact:</b> {listing["seller_email"]}
                </div>
                <div class="actions">
                    <a class="button" href="/edit-listing/{listing["id"]}">Edit</a>
                    <form class="inline" action="/delete-listing/{listing["id"]}" method="post">
                        <button type="submit" class="button-danger">Delete</button>
                    </form>
                </div>
            </div>
            """
    else:
        listings_html = '<p class="empty">No listings yet.</p>'

    content = f"""
    <div class="grid">
        <div class="left-column">
            <div class="card">
                <h1>School Supply Wizard</h1>
                <div class="subtitle">Buy, sell, or donate used books, uniforms, and supplies within your district.</div>
                <a class="button" href="/new-listing">Post a Listing</a>
            </div>

            <div class="card" style="margin-top:0;">
                <h2>Available Listings</h2>
                {listings_html}
            </div>
        </div>

        <div class="card">
            <h2>Quick Tips</h2>
            <p class="muted" style="margin-bottom: 0;">Post clear photos, include condition, and list the school to help families find what they need faster.</p>

            <div class="sidebar-section">
                <h3>Categories</h3>
                <p class="muted" style="margin-bottom: 0;">Uniforms, books, calculators, backpacks, lunch boxes, sports gear, and more.</p>
            </div>
        </div>
    </div>
    """
    return page_wrapper(content)


@app.get("/new-listing", response_class=HTMLResponse)
def new_listing_form() -> str:
    content = """
    <div class="card">
        <h1>Post a Listing</h1>
        <div class="subtitle">Add an item families in your district can buy or claim.</div>

        <form action="/new-listing" method="post" enctype="multipart/form-data">
            <label>Item Title</label>
            <input name="title" required>

            <label>Description</label>
            <textarea name="description" required></textarea>

            <div class="row">
                <div>
                    <label>Price</label>
                    <input name="price" type="number" step="0.01" value="0">
                </div>
                <div>
                    <label>School</label>
                    <input name="school" required>
                </div>
            </div>

            <div class="row">
                <div>
                    <label>Seller Name</label>
                    <input name="seller_name" required>
                </div>
                <div>
                    <label>Seller Email</label>
                    <input name="seller_email" type="email" required>
                </div>
            </div>

            <label>Image</label>
            <input name="image" type="file" accept=".jpg,.jpeg,.png,.webp,.gif">

            <div class="actions">
                <button type="submit">Create Listing</button>
                <a class="button button-secondary" href="/">Back Home</a>
            </div>
        </form>
    </div>
    """
    return page_wrapper(content, "Post a Listing")


@app.post("/new-listing", response_class=HTMLResponse)
async def create_listing(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(0),
    school: str = Form(...),
    seller_name: str = Form(...),
    seller_email: str = Form(...),
    image: UploadFile | None = File(None),
) -> HTMLResponse:
    image_path = save_uploaded_image(image)

    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO listings (title, description, price, school, seller_name, seller_email, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, price, school, seller_name, seller_email, image_path),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/", status_code=303)


@app.get("/edit-listing/{listing_id}", response_class=HTMLResponse)
def edit_listing_form(listing_id: int) -> str:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
    listing = c.fetchone()
    conn.close()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    image_html = (
        f'<img class="listing-image" src="{listing["image_path"]}" alt="{listing["title"]}">'
        if listing["image_path"]
        else "<p class='muted'>No image uploaded.</p>"
    )

    content = f"""
    <div class="card">
        <h1>Edit Listing</h1>
        <div class="subtitle">Update the item details below.</div>

        {image_html}

        <form action="/edit-listing/{listing_id}" method="post" enctype="multipart/form-data">
            <label>Item Title</label>
            <input name="title" value="{listing["title"]}" required>

            <label>Description</label>
            <textarea name="description" required>{listing["description"]}</textarea>

            <div class="row">
                <div>
                    <label>Price</label>
                    <input name="price" type="number" step="0.01" value="{listing["price"]}">
                </div>
                <div>
                    <label>School</label>
                    <input name="school" value="{listing["school"]}" required>
                </div>
            </div>

            <div class="row">
                <div>
                    <label>Seller Name</label>
                    <input name="seller_name" value="{listing["seller_name"]}" required>
                </div>
                <div>
                    <label>Seller Email</label>
                    <input name="seller_email" type="email" value="{listing["seller_email"]}" required>
                </div>
            </div>

            <label>Replace Image</label>
            <input name="image" type="file" accept=".jpg,.jpeg,.png,.webp,.gif">

            <div class="actions">
                <button type="submit">Save Changes</button>
                <a class="button button-secondary" href="/">Cancel</a>
            </div>
        </form>
    </div>
    """
    return page_wrapper(content, "Edit Listing")


@app.post("/edit-listing/{listing_id}", response_class=HTMLResponse)
async def edit_listing(
    listing_id: int,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(0),
    school: str = Form(...),
    seller_name: str = Form(...),
    seller_email: str = Form(...),
    image: UploadFile | None = File(None),
) -> HTMLResponse:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
    listing = c.fetchone()

    if not listing:
        conn.close()
        raise HTTPException(status_code=404, detail="Listing not found")

    image_path = listing["image_path"]
    if image and image.filename:
        delete_image_file(image_path)
        image_path = save_uploaded_image(image)

    c.execute(
        """
        UPDATE listings
        SET title = ?, description = ?, price = ?, school = ?, seller_name = ?, seller_email = ?, image_path = ?
        WHERE id = ?
        """,
        (title, description, price, school, seller_name, seller_email, image_path, listing_id),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/", status_code=303)


@app.post("/delete-listing/{listing_id}", response_class=HTMLResponse)
def delete_listing(listing_id: int) -> HTMLResponse:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT image_path FROM listings WHERE id = ?", (listing_id,))
    listing = c.fetchone()

    if listing:
        delete_image_file(listing["image_path"])
        c.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
        conn.commit()

    conn.close()
    return RedirectResponse(url="/", status_code=303)