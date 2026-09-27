import json
import os
import uuid
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"


@app.template_filter("goldmark")
def goldmark(text):
    """Convert {gold}...{/gold} markers into a gold-coloured span."""
    if not text:
        return ""
    return text.replace("{gold}", '<span class="gold">').replace("{/gold}", "</span>")

DATA_FILE   = os.path.join(os.path.dirname(__file__), "data.json")
UPLOAD_DIR  = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

PER_PAGE = 8


# ============================================================
# FIXED TESTIMONIALS — always shown, cannot be deleted in admin
# ============================================================
FIXED_REVIEWS = [
    {"name": "Joseph Appiah",    "location": "Accra",      "text": "Very genuine tools. I bought a cordless drill and it works perfectly. Highly recommended!"},
    {"name": "Frederick Ansah",  "location": "Kumasi",     "text": "Fast delivery! I ordered in the morning and received my tools the same day. Impressive service."},
    {"name": "Sosu Christopher", "location": "Takoradi",   "text": "Their prices are very cheap compared to other shops in town. I will definitely buy again."},
    {"name": "Appiah Adjei",     "location": "Kasoa",      "text": "Excellent customer service. They helped me choose the right spare parts for my machine."},
    {"name": "Badago Victor",    "location": "Tema",       "text": "100% original products. I was skeptical at first but the tools are very genuine."},
    {"name": "Ama Serwaa",       "location": "Accra",      "text": "Their fabrication work is top-notch. Very professional and affordable."},
    {"name": "Kwame Boateng",    "location": "Kumasi",     "text": "I ordered a welding machine and it arrived in perfect condition. Very reliable shop."},
    {"name": "Akosua Mensah",    "location": "Cape Coast", "text": "Friendly staff, quality tools and fast response on WhatsApp. 5 stars!"},
    {"name": "Yaw Owusu",        "location": "Sunyani",    "text": "Best place to buy tools in Ghana. Genuine parts and honest prices."},
]


# ============================================================
# HELPERS
# ============================================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "site": {},
            "services": [],
            "products": [],
            "comments": [],
            "admin_password": "admin",
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_uploaded_image(file_storage):
    """Save an uploaded image; return its public URL path (/static/uploads/...)."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None

    ext  = file_storage.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    file_storage.save(path)
    return f"/static/uploads/{name}"


def get_uploaded_image():
    """
    Return the first image found across both upload inputs:
      - image_file         → From Gallery
      - image_file_camera  → Take Photo
    """
    return (
        save_uploaded_image(request.files.get("image_file"))
        or save_uploaded_image(request.files.get("image_file_camera"))
    )


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# PUBLIC — HOME
# ============================================================
@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()

    # Visitor comment submitted
    if request.method == "POST":
        name    = (request.form.get("name") or "").strip()
        comment = (request.form.get("comment") or "").strip()
        if name and comment:
            data["comments"].insert(0, {"name": name, "text": comment})
            save_data(data)
        return redirect(url_for("index") + "#testimonials")

    # Pagination
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    products    = data.get("products", [])
    total       = len(products)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    if page > total_pages:
        page = total_pages

    start         = (page - 1) * PER_PAGE
    products_page = products[start:start + PER_PAGE]

    return render_template(
        "index.html",
        site=data.get("site", {}),
        services=data.get("services", []),
        products=products_page,
        page=page,
        total_pages=total_pages,
        total_tools=total,
        visitor_comments=data.get("comments", []),
        fixed_reviews=FIXED_REVIEWS,
    )


# ============================================================
# ADMIN — AUTH
# ============================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        data = load_data()
        pwd  = request.form.get("password", "")
        if pwd == data.get("admin_password", "admin"):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Wrong password", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


# ============================================================
# ADMIN — DASHBOARD
# ============================================================
@app.route("/admin")
@login_required
def admin_dashboard():
    data = load_data()
    return render_template(
        "admin/dashboard.html",
        product_count=len(data.get("products", [])),
        comment_count=len(data.get("comments", [])),
        service_count=len(data.get("services", [])),
    )


# ============================================================
# ADMIN — TOOLS
# ============================================================
@app.route("/admin/tools")
@login_required
def admin_tools():
    data = load_data()
    return render_template("admin/tools.html", products=data.get("products", []))


@app.route("/admin/tools/new", methods=["GET", "POST"])
@login_required
def admin_tool_new():
    if request.method == "POST":
        data = load_data()

        # Image priority: gallery upload → camera upload → URL
        uploaded = get_uploaded_image()
        image    = uploaded or request.form.get("image", "").strip()

        new_id = max([p["id"] for p in data["products"]], default=0) + 1
        data["products"].append({
            "id":       new_id,
            "name":     request.form.get("name", "").strip(),
            "location": request.form.get("location", "").strip(),
            "price":    float(request.form.get("price", 0) or 0),
            "specs":    request.form.get("specs", "").strip(),
            "image":    image,
        })
        save_data(data)
        flash("Tool added successfully", "success")
        return redirect(url_for("admin_tools"))

    return render_template("admin/tool_form.html", tool=None)


@app.route("/admin/tools/edit/<int:tool_id>", methods=["GET", "POST"])
@login_required
def admin_tool_edit(tool_id):
    data = load_data()
    tool = next((p for p in data["products"] if p["id"] == tool_id), None)
    if not tool:
        abort(404)

    if request.method == "POST":
        uploaded = get_uploaded_image()
        url_val  = request.form.get("image", "").strip()

        if uploaded:
            tool["image"] = uploaded
        elif url_val:
            tool["image"] = url_val
        # else: keep existing image

        tool["name"]     = request.form.get("name", "").strip()
        tool["location"] = request.form.get("location", "").strip()
        tool["price"]    = float(request.form.get("price", 0) or 0)
        tool["specs"]    = request.form.get("specs", "").strip()

        save_data(data)
        flash("Tool updated", "success")
        return redirect(url_for("admin_tools"))

    return render_template("admin/tool_form.html", tool=tool)


@app.route("/admin/tools/delete/<int:tool_id>", methods=["POST"])
@login_required
def admin_tool_delete(tool_id):
    data = load_data()
    data["products"] = [p for p in data["products"] if p["id"] != tool_id]
    save_data(data)
    flash("Tool deleted", "success")
    return redirect(url_for("admin_tools"))


# ============================================================
# ADMIN — SITE
# ============================================================
@app.route("/admin/site", methods=["GET", "POST"])
@login_required
def admin_site():
    data = load_data()
    if request.method == "POST":
        data["site"].update({
            "hero_kicker":       request.form.get("hero_kicker", "").strip(),
            "hero_title_line1":  request.form.get("hero_title_line1", "").strip(),
            "hero_title_line2":  request.form.get("hero_title_line2", "").strip(),
            "hero_sub":          request.form.get("hero_sub", "").strip(),
            "services_heading":  request.form.get("services_heading", "").strip(),
            "products_heading":  request.form.get("products_heading", "").strip(),
            "info_location":     request.form.get("info_location", "").strip(),
            "info_phone":        request.form.get("info_phone", "").strip(),
            "info_whatsapp":     request.form.get("info_whatsapp", "").strip(),
            "info_slogan":       request.form.get("info_slogan", "").strip(),
            "footer_blurb":      request.form.get("footer_blurb", "").strip(),
            "footer_dev":        request.form.get("footer_dev", "").strip(),
        })
        save_data(data)
        flash("Site content updated", "success")
        return redirect(url_for("admin_site"))
    return render_template("admin/site.html", site=data["site"])


# ============================================================
# ADMIN — SERVICES
# ============================================================
@app.route("/admin/services", methods=["GET", "POST"])
@login_required
def admin_services():
    data = load_data()
    if request.method == "POST":
        icons  = request.form.getlist("icon")
        titles = request.form.getlist("title")
        data["services"] = [
            {"icon": i.strip(), "title": t.strip()}
            for i, t in zip(icons, titles) if t.strip()
        ]
        save_data(data)
        flash("Services updated", "success")
        return redirect(url_for("admin_services"))
    return render_template("admin/services.html", services=data["services"])


# ============================================================
# ADMIN — COMMENTS
# ============================================================
@app.route("/admin/comments")
@login_required
def admin_comments():
    data = load_data()
    return render_template("admin/comments.html", comments=data.get("comments", []))


@app.route("/admin/comments/delete/<int:idx>", methods=["POST"])
@login_required
def admin_comment_delete(idx):
    data = load_data()
    if 0 <= idx < len(data["comments"]):
        del data["comments"][idx]
        save_data(data)
        flash("Comment deleted", "success")
    return redirect(url_for("admin_comments"))


# ============================================================
# ADMIN — PASSWORD
# ============================================================
@app.route("/admin/password", methods=["POST"])
@login_required
def admin_password():
    data = load_data()
    new_pwd = request.form.get("new_password", "").strip()
    if new_pwd:
        data["admin_password"] = new_pwd
        save_data(data)
        flash("Password changed", "success")
    return redirect(url_for("admin_dashboard"))


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)