import os
import uuid
from functools import wraps
from dotenv import load_dotenv
from supabase import create_client, Client
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)

load_dotenv()

# ============================================================
# CONFIG — hardcoded
# ============================================================
SUPABASE_URL   = "https://soeenrjxrspfsexdiuip.supabase.co"
SUPABASE_KEY   = "sb_publishable_mYvFcs9_OSA0PTIbcj4djg_NHGB8DXC"
SECRET_KEY     = "advance-tools-secret-2026-change-me"
ADMIN_PASSWORD = "advance2026"

app = Flask(__name__)
app.secret_key = SECRET_KEY

print("BOOT SUPABASE_URL =", repr(SUPABASE_URL), "KEY_LEN =", len(SUPABASE_KEY))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

PER_PAGE = 8


@app.template_filter("goldmark")
def goldmark(text):
    if not text:
        return ""
    return text.replace("{gold}", '<span class="gold">').replace("{/gold}", "</span>")


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


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def fetch_tools():
    try:
        res = supabase.table("tools").select("*").order("id").execute()
        return res.data or []
    except Exception as e:
        print("fetch_tools error:", e)
        return []


def fetch_services():
    try:
        res = supabase.table("services").select("*").order("sort_order").execute()
        return res.data or []
    except Exception as e:
        print("fetch_services error:", e)
        return []


def fetch_comments():
    try:
        res = supabase.table("comments").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        print("fetch_comments error:", e)
        return []


def fetch_site():
    try:
        res = supabase.table("site_content").select("*").execute()
        return {row["key"]: row["value"] for row in (res.data or [])}
    except Exception as e:
        print("fetch_site error:", e)
        return {}


def upload_image_to_supabase(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "gif", "webp"}:
        return None
    filename = f"{uuid.uuid4().hex}.{ext}"
    try:
        supabase.storage.from_("tool-images").upload(
            path=filename,
            file=file_storage.read(),
            file_options={"content-type": file_storage.mimetype or "image/jpeg"},
        )
        return supabase.storage.from_("tool-images").get_public_url(filename)
    except Exception as e:
        print("upload error:", e)
        return None


def get_uploaded_image():
    return (
        upload_image_to_supabase(request.files.get("image_file"))
        or upload_image_to_supabase(request.files.get("image_file_camera"))
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name    = (request.form.get("name") or "").strip()
        comment = (request.form.get("comment") or "").strip()
        if name and comment:
            try:
                supabase.table("comments").insert({"name": name, "text": comment}).execute()
            except Exception as e:
                print("comment insert error:", e)
        return redirect(url_for("index") + "#testimonials")

    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    all_products = fetch_tools()
    total        = len(all_products)
    total_pages  = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    if page > total_pages:
        page = total_pages

    start         = (page - 1) * PER_PAGE
    products_page = all_products[start:start + PER_PAGE]

    return render_template(
        "index.html",
        site=fetch_site(),
        services=fetch_services(),
        products=products_page,
        page=page,
        total_pages=total_pages,
        total_tools=total,
        visitor_comments=fetch_comments(),
        fixed_reviews=FIXED_REVIEWS,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if pwd == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Wrong password", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template(
        "admin/dashboard.html",
        product_count=len(fetch_tools()),
        comment_count=len(fetch_comments()),
        service_count=len(fetch_services()),
    )


@app.route("/admin/tools")
@login_required
def admin_tools():
    return render_template("admin/tools.html", products=fetch_tools())


@app.route("/admin/tools/new", methods=["GET", "POST"])
@login_required
def admin_tool_new():
    if request.method == "POST":
        uploaded = get_uploaded_image()
        image    = uploaded or request.form.get("image", "").strip()
        try:
            supabase.table("tools").insert({
                "name":     request.form.get("name", "").strip(),
                "location": request.form.get("location", "").strip(),
                "price":    float(request.form.get("price", 0) or 0),
                "specs":    request.form.get("specs", "").strip(),
                "image":    image,
            }).execute()
            flash("Tool added successfully", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_tools"))
    return render_template("admin/tool_form.html", tool=None)


@app.route("/admin/tools/edit/<int:tool_id>", methods=["GET", "POST"])
@login_required
def admin_tool_edit(tool_id):
    try:
        res = supabase.table("tools").select("*").eq("id", tool_id).single().execute()
        tool = res.data
    except Exception:
        tool = None
    if not tool:
        abort(404)
    if request.method == "POST":
        uploaded = get_uploaded_image()
        url_val  = request.form.get("image", "").strip()
        update_data = {
            "name":     request.form.get("name", "").strip(),
            "location": request.form.get("location", "").strip(),
            "price":    float(request.form.get("price", 0) or 0),
            "specs":    request.form.get("specs", "").strip(),
        }
        if uploaded:
            update_data["image"] = uploaded
        elif url_val:
            update_data["image"] = url_val
        try:
            supabase.table("tools").update(update_data).eq("id", tool_id).execute()
            flash("Tool updated", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_tools"))
    return render_template("admin/tool_form.html", tool=tool)


@app.route("/admin/tools/delete/<int:tool_id>", methods=["POST"])
@login_required
def admin_tool_delete(tool_id):
    try:
        supabase.table("tools").delete().eq("id", tool_id).execute()
        flash("Tool deleted", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_tools"))


@app.route("/admin/site", methods=["GET", "POST"])
@login_required
def admin_site():
    if request.method == "POST":
        fields = [
            "hero_kicker", "hero_title_line1", "hero_title_line2", "hero_sub",
            "services_heading", "products_heading",
            "info_location", "info_phone", "info_whatsapp", "info_slogan",
            "footer_blurb", "footer_dev",
        ]
        try:
            for f in fields:
                supabase.table("site_content").upsert({
                    "key":   f,
                    "value": request.form.get(f, "").strip(),
                }).execute()
            flash("Site content updated", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_site"))
    return render_template("admin/site.html", site=fetch_site())


@app.route("/admin/services", methods=["GET", "POST"])
@login_required
def admin_services():
    if request.method == "POST":
        icons  = request.form.getlist("icon")
        titles = request.form.getlist("title")
        try:
            supabase.table("services").delete().neq("id", 0).execute()
            for i, (ic, ti) in enumerate(zip(icons, titles)):
                if ti.strip():
                    supabase.table("services").insert({
                        "icon":       ic.strip(),
                        "title":      ti.strip(),
                        "sort_order": i,
                    }).execute()
            flash("Services updated", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_services"))
    return render_template("admin/services.html", services=fetch_services())


@app.route("/admin/comments")
@login_required
def admin_comments():
    return render_template("admin/comments.html", comments=fetch_comments())


@app.route("/admin/comments/delete/<int:comment_id>", methods=["POST"])
@login_required
def admin_comment_delete(comment_id):
    try:
        supabase.table("comments").delete().eq("id", comment_id).execute()
        flash("Comment deleted", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_comments"))


@app.route("/admin/password", methods=["POST"])
@login_required
def admin_password():
    flash("Password is set in app.py (ADMIN_PASSWORD constant).", "error")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
