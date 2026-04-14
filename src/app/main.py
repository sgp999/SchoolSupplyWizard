from fastapi import FastAPI
from fastapi import Form

from fastapi.responses import HTMLResponse

app = FastAPI(title="School Supply Wizard")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <html>
        <head>
            <title>School Supply Wizard</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: #eef3f8;
                    margin: 0;
                    padding: 32px;
                    color: #1f2937;
                }
                .page {
                    max-width: 1100px;
                    margin: 0 auto;
                }
                .card {
                    background: white;
                    border-radius: 18px;
                    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
                    padding: 28px;
                }
                h1 {
                    margin: 0 0 10px 0;
                    font-size: 48px;
                    color: #2450d3;
                }
                p {
                    color: #6b7280;
                    font-size: 18px;
                    line-height: 1.5;
                }
                .button {
                    display: inline-block;
                    background: #2563eb;
                    color: white;
                    text-decoration: none;
                    padding: 14px 18px;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 700;
                    margin-top: 12px;
                }
                .button:hover {
                    background: #1d4ed8;
                }
            </style>
        </head>
        <body>
            <div class="page">
                <div class="card">
                    <h1>School Supply Wizard</h1>
                    <p>
                        Buy, sell, or donate school supplies, books, and uniforms within your district.
                    </p>
                    <a class="button" href="/new-listing">Post a Listing</a>
                </div>
            </div>
        </body>
    </html>
    """


@app.get("/new-listing", response_class=HTMLResponse)
def new_listing_form() -> str:
    return """
    <html>
        <head>
            <title>Post Listing</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: #eef3f8;
                    padding: 32px;
                }
                .card {
                    max-width: 700px;
                    margin: 0 auto;
                    background: white;
                    padding: 24px;
                    border-radius: 12px;
                }
                input, textarea {
                    width: 100%;
                    padding: 12px;
                    margin-bottom: 12px;
                    border-radius: 8px;
                    border: 1px solid #ccc;
                }
                button {
                    background: #2563eb;
                    color: white;
                    padding: 12px;
                    border: none;
                    border-radius: 8px;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Post a Listing</h1>
                <form action="/new-listing" method="post">
                    <input name="title" placeholder="Item Title" required>
                    <textarea name="description" placeholder="Description" required></textarea>
                    <input name="price" type="number" step="0.01" placeholder="Price">
                    <input name="school" placeholder="School" required>
                    <input name="seller_name" placeholder="Your Name" required>
                    <input name="seller_email" type="email" placeholder="Email" required>
                    <button type="submit">Create Listing</button>
                </form>
            </div>
        </body>
    </html>
    """
@app.post("/new-listing", response_class=HTMLResponse)
def create_listing(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(0),
    school: str = Form(...),
    seller_name: str = Form(...),
    seller_email: str = Form(...),
):
    return f"""
    <html>
        <body style="font-family: Arial; padding: 40px;">
            <h1>Listing Created</h1>
            <p><b>{title}</b></p>
            <p>{description}</p>
            <p>Price: ${price}</p>
            <p>School: {school}</p>
            <p>Seller: {seller_name}</p>
            <p>Contact: {seller_email}</p>
            <a href="/">Back Home</a>
        </body>
    </html>
    """