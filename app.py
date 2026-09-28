import os
import uuid
import random
from functools import wraps
from dotenv import load_dotenv
from supabase import create_client, Client
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort, jsonify
)

load_dotenv()

# ============================================================
# CONFIG — hardcoded fallbacks
# ============================================================
SUPABASE_URL     = os.environ.get("SUPABASE_URL",  "https://soeenrjxrspfsexdiuip.supabase.co")
SUPABASE_KEY     = os.environ.get("SUPABASE_KEY",  "sb_publishable_mYvFcs9_OSA0PTIbcj4djg_NHGB8DXC")
SECRET_KEY       = os.environ.get("SECRET_KEY",    "advance-tools-secret-2026-change-me")
ADMIN_PASSWORD   = os.environ.get("ADMIN_PASSWORD","advance2026")
DEFAULT_WHATSAPP = "233593652536"
DEFAULT_PHONE    = "0593652536"

app = Flask(__name__)
app.secret_key = SECRET_KEY

print("BOOT SUPABASE_URL =", repr(SUPABASE_URL), "KEY_LEN =", len(SUPABASE_KEY))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

PER_PAGE = 8


# ============================================================
# GOLD MARKER FILTER
# ============================================================
@app.template_filter("goldmark")
def goldmark(text):
    if not text:
        return ""
    return text.replace("{gold}", '<span class="gold">').replace("{/gold}", "</span>")


# ============================================================
# FIXED REVIEWS
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
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def fetch_tools(category_id=None):
    try:
        q = supabase.table("tools").select("*").order("id")
        if category_id:
            q = q.eq("category_id", category_id)
        res = q.execute()
        return res.data or []
    except Exception as e:
        print("fetch_tools error:", e)
        return []


def fetch_featured_tools():
    try:
        res = supabase.table("tools").select("*").eq("featured", True).order("id").execute()
        return res.data or []
    except Exception as e:
        print("fetch_featured_tools error:", e)
        return []


def fetch_regular_tools(category_id=None):
    try:
        res = supabase.table("tools").select("*").order("id").execute()
        all_tools = res.data or []
        regular = [t for t in all_tools if not t.get("featured")]
        if category_id:
            regular = [t for t in regular if t.get("category_id") == category_id]
        return regular
    except Exception as e:
        print("fetch_regular_tools error:", e)
        return []


def fetch_categories():
    try:
        res = supabase.table("categories").select("*").order("sort_order").execute()
        return res.data or []
    except Exception as e:
        print("fetch_categories error:", e)
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


def build_random_grid():
    featured = fetch_featured_tools()
    regular  = fetch_regular_tools()

    random.shuffle(featured)
    random.shuffle(regular)

    picks = []
    picks.extend(featured[:2])
    picks.extend(regular[:2])

    if len(featured) < 2:
        picks.extend(regular[2:2 + (2 - len(featured))])
    if len(regular) < 2:
        picks.extend(featured[2:2 + (2 - len(regular))])

    seen, unique = set(), []
    for p in picks:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    random.shuffle(unique)
    return unique[:4]


def build_card_payload(tool):
    return {
        "id":       tool["id"],
        "name":     tool.get("name", ""),
        "location": tool.get("location", ""),
        "price":    tool.get("price", 0),
        "specs":    tool.get("specs", ""),
        "image":    tool.get("image", ""),
        "featured": bool(tool.get("featured")),
        "phone":    tool.get("phone") or DEFAULT_WHATSAPP,
    }


def upload_image_to_supabase(file_storage):
    """Upload image to Supabase Storage and return public URL."""
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


# ============================================================
# PUBLIC — HOME
# ============================================================
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

    category_slug = request.args.get("category")
    active_category = None
    if category_slug:
        cats = fetch_categories()
        active_category = next((c for c in cats if c.get("slug") == category_slug), None)

    if active_category:
        all_products = fetch_tools(category_id=active_category["id"])
    else:
        all_products = fetch_tools()

    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    total       = len(all_products)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    if page > total_pages:
        page = total_pages
    start         = (page - 1) * PER_PAGE
    products_page = all_products[start:start + PER_PAGE]

    random_grid = build_random_grid() if not active_category else []

    return render_template(
        "index.html",
        site=fetch_site(),
        categories=fetch_categories(),
        services=fetch_services(),
        products=products_page,
        random_grid=random_grid,
        total_tools=total,
        page=page,
        total_pages=total_pages,
        active_category=active_category,
        visitor_comments=fetch_comments(),
        fixed_reviews=FIXED_REVIEWS,
    )


# ============================================================
# SHOP
# ============================================================
@app.route("/shop")
def shop_page():
    all_tools = fetch_tools()
    featured  = [t for t in all_tools if t.get("featured")]
    regular   = [t for t in all_tools if not t.get("featured")]

    return render_template(
        "shop.html",
        site=fetch_site(),
        categories=fetch_categories(),
        all_tools=all_tools,
        featured_tools=featured,
        regular_tools=regular,
        total_tools=len(all_tools),
        active_category=None,
    )


# ============================================================
# FEATURED PAGE
# ============================================================
@app.route("/featured")
def featured_page():
    featured = fetch_featured_tools()
    return render_template(
        "featured.html",
        site=fetch_site(),
        categories=fetch_categories(),
        featured_tools=featured,
        total_tools=len(featured),
        active_category=None,
    )


# ============================================================
# API — random cards
# ============================================================
@app.route("/api/random-cards")
def api_random_cards():
    grid = build_random_grid()
    return jsonify([build_card_payload(t) for t in grid])


# ============================================================
# API — search
# ============================================================
@app.route("/api/search")
def api_search():
    q = (request.args.get("q") or "").strip().lower()
    if not q:
        return jsonify([])

    results = []

    for t in fetch_tools():
        haystack = " ".join([t.get("name", ""), t.get("specs", ""), t.get("location", "")]).lower()
        if q in haystack:
            results.append({
                "type":  "tool",
                "id":    t["id"],
                "name":  t.get("name", ""),
                "specs": t.get("specs", ""),
                "price": t.get("price", 0),
                "image": t.get("image", ""),
                "phone": t.get("phone") or DEFAULT_WHATSAPP,
                "url":   url_for("index"),
            })

    for c in fetch_categories():
        if q in c.get("name", "").lower():
            results.append({
                "type":  "category",
                "id":    c["id"],
                "name":  c.get("name", ""),
                "image": c.get("image", ""),
                "url":   url_for("index", category=c["slug"]),
            })

    return jsonify(results[:20])


# ============================================================
# ADMIN — AUTH
# ============================================================
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


# ============================================================
# ADMIN — DASHBOARD
# ============================================================
@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template(
        "admin/dashboard.html",
        product_count=len(fetch_tools()),
        featured_count=len(fetch_featured_tools()),
        category_count=len(fetch_categories()),
        comment_count=len(fetch_comments()),
        service_count=len(fetch_services()),
    )


# ============================================================
# ADMIN — TOOLS
# ============================================================
@app.route("/admin/tools")
@login_required
def admin_tools():
    return render_template("admin/tools.html", products=fetch_tools(), categories=fetch_categories())


@app.route("/admin/tools/new", methods=["GET", "POST"])
@login_required
def admin_tool_new():
    if request.method == "POST":
        uploaded = get_uploaded_image()
        image    = uploaded or request.form.get("image", "").strip()

        category_id = request.form.get("category_id") or None
        if category_id:
            try:
                category_id = int(category_id)
            except:
                category_id = None

        featured = True if request.form.get("featured") == "on" else False
        phone    = request.form.get("phone", "").strip() or None

        try:
            supabase.table("tools").insert({
                "name":        request.form.get("name", "").strip(),
                "location":    request.form.get("location", "").strip(),
                "price":       float(request.form.get("price", 0) or 0),
                "specs":       request.form.get("specs", "").strip(),
                "image":       image,
                "category_id": category_id,
                "featured":    featured,
                "phone":       phone,
            }).execute()
            flash("Tool added successfully", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")

        return redirect(url_for("admin_tools"))

    return render_template("admin/tool_form.html", tool=None, categories=fetch_categories())


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

        category_id = request.form.get("category_id") or None
        if category_id:
            try:
                category_id = int(category_id)
            except:
                category_id = None

        featured = True if request.form.get("featured") == "on" else False
        phone    = request.form.get("phone", "").strip() or None

        update_data = {
            "name":        request.form.get("name", "").strip(),
            "location":    request.form.get("location", "").strip(),
            "price":       float(request.form.get("price", 0) or 0),
            "specs":       request.form.get("specs", "").strip(),
            "category_id": category_id,
            "featured":    featured,
            "phone":       phone,
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

    return render_template("admin/tool_form.html", tool=tool, categories=fetch_categories())


@app.route("/admin/tools/delete/<int:tool_id>", methods=["POST"])
@login_required
def admin_tool_delete(tool_id):
    try:
        supabase.table("tools").delete().eq("id", tool_id).execute()
        flash("Tool deleted", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_tools"))


# ============================================================
# ADMIN — CATEGORIES
# ============================================================
@app.route("/admin/categories")
@login_required
def admin_categories():
    return render_template("admin/categories.html", categories=fetch_categories())


@app.route("/admin/categories/new", methods=["POST"])
@login_required
def admin_category_new():
    name  = request.form.get("name", "").strip()
    slug  = request.form.get("slug", "").strip().lower().replace(" ", "-")

    uploaded = get_uploaded_image()
    image    = uploaded or request.form.get("image", "").strip()

    if name and slug:
        try:
            supabase.table("categories").insert({
                "name":       name,
                "slug":       slug,
                "image":      image,
                "sort_order": len(fetch_categories()) + 1,
            }).execute()
            flash("Category added", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")

    return redirect(url_for("admin_categories"))


@app.route("/admin/categories/edit/<int:cat_id>", methods=["POST"])
@login_required
def admin_category_edit(cat_id):
    uploaded = get_uploaded_image()
    url_val  = request.form.get("image", "").strip()

    try:
        res = supabase.table("categories").select("*").eq("id", cat_id).single().execute()
        row = res.data
    except Exception:
        row = None

    if not row:
        abort(404)

    image = row.get("image") or ""
    if uploaded:
        image = uploaded
    elif url_val:
        image = url_val

    try:
        supabase.table("categories").update({
            "name":  request.form.get("name", "").strip(),
            "slug":  request.form.get("slug", "").strip().lower().replace(" ", "-"),
            "image": image,
        }).eq("id", cat_id).execute()
        flash("Category updated", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for("admin_categories"))


@app.route("/admin/categories/delete/<int:cat_id>", methods=["POST"])
@login_required
def admin_category_delete(cat_id):
    try:
        supabase.table("categories").delete().eq("id", cat_id).execute()
        flash("Category deleted", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_categories"))


# ============================================================
# ADMIN — FEATURED
# ============================================================
@app.route("/admin/featured")
@login_required
def admin_featured():
    return render_template(
        "admin/featured.html",
        featured_tools=fetch_featured_tools(),
        categories=fetch_categories(),
    )


# ============================================================
# ADMIN — SITE CONTENT
# ============================================================
@app.route("/admin/site", methods=["GET", "POST"])
@login_required
def admin_site():
    if request.method == "POST":
        uploaded_logo = (
            upload_image_to_supabase(request.files.get("base_logo_file"))
            or upload_image_to_supabase(request.files.get("base_logo_camera"))
        )

        fields = [
            "page_title", "brand_name",
            "hero_kicker", "hero_title_line1", "hero_title_line2", "hero_sub",
            "services_heading", "products_heading",
            "info_phone", "info_whatsapp",
            "info_location", "info_slogan",
            "footer_blurb", "footer_dev",
        ]

        try:
            for f in fields:
                supabase.table("site_content").upsert({
                    "key":   f,
                    "value": request.form.get(f, "").strip(),
                }).execute()

            # Base logo: uploaded wins, else URL
            url_logo = request.form.get("base_logo", "").strip()
            if uploaded_logo:
                supabase.table("site_content").upsert({
                    "key": "base_logo", "value": uploaded_logo,
                }).execute()
            elif url_logo:
                supabase.table("site_content").upsert({
                    "key": "base_logo", "value": url_logo,
                }).execute()

            flash("Site content updated", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")

        return redirect(url_for("admin_site"))

    return render_template("admin/site.html", site=fetch_site())


# ============================================================
# ADMIN — SERVICES
# ============================================================
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


# ============================================================
# ADMIN — COMMENTS
# ============================================================
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


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)