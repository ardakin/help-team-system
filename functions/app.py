import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required, logout_user, current_user
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import text, func, or_
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# -------------------------------
# Ortam değişkenleri
# -------------------------------
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DATABASE_URL = os.getenv("DATABASE_URL")
INIT_TOKEN = os.getenv("INIT_TOKEN", "help-team-system-123")

# Postgres URL fix + SSL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
if DATABASE_URL.startswith("postgresql+psycopg2://") and "sslmode=" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

# -------------------------------
# Flask ve DB
# -------------------------------
app = Flask(__name__)
app.url_map.strict_slashes = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-dev-key")
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_PATH"] = "/"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# -------------------------------
# Fakülte -> Bölümler (select için)
# -------------------------------
FACULTY_DEPARTMENTS = {
    "Tıp Fakültesi": ["TIP"],
    "Diş Hekimliği Fakültesi": ["DİŞ HEKİMLİĞİ"],
    "İktisadi, İdari ve Sosyal Bilimler Fakültesi": [
        "EKONOMİ",
        "EKONOMİ VE FİNANS",
        "FİNANS VE BANKACILIK",
        "HALKLA İLİŞKİLER VE REKLAMCILIK",
        "HAVACILIK YÖNETİMİ (TÜRKÇE-İNGİLİZCE)",
        "İNGİLİZ DİLİ VE EDEBİYATI (İNGİLİZCE)",
        "İNGİLİZCE MÜTERCİM TERCÜMANLIK",
        "İŞLETME (TÜRKÇE - İNGİLİZCE)",
        "PSİKOLOJİ (TÜRKÇE-İNGİLİZCE)",
        "SİYASET BİLİMİ VE KAMU YÖNETİMİ",
        "MUHASEBE VE FİNANS YÖNETİMİ",
        "SERMAYE PİYASASI",
        "SOSYAL HİZMET",
        "SOSYOLOJİ",
        "TURİZM İŞLETMECİLİĞİ",
        "ULUSLARARASI İLİŞKİLER",
        "ULUSLARARASI TİCARET VE LOJİSTİK",
        "YENİ MEDYA VE İLETİŞİM",
        "YÖNETİM BİLİŞİM SİSTEMLERİ (TÜRKÇE-İNGİLİZCE)",
    ],
    "Mühendislik Mimarlık Fakültesi": [
        "BİLGİSAYAR MÜHENDİSLİĞİ (Türkçe)",
        "ELEKTRİK - ELEKTRONİK MÜHENDİSLİĞİ (İngilizce)",
        "ENDÜSTRİ MÜHENDİSLİĞİ",
        "İNŞAAT MÜHENDİSLİĞİ",
        "MEKATRONİK MÜHENDİSLİĞİ",
        "MİMARLIK",
        "YAZILIM MÜHENDİSLİĞİ (İngilizce)",
        "MAKİNE MÜHENDİSLİĞİ (İNGİLİZCE)",
    ],
    "Sanat ve Tasarım Fakültesi": [
        "DİJİTAL OYUN TASARIMI",
        "ENDÜSTRİYEL TASARIM",
        "GASTRONOMİ VE MUTFAK SANATLARI (TÜRKÇE - İNGİLİZCE)",
        "GRAFİK TASARIMI",
        "İLETİŞİM VE TASARIMI",
        "RADYO, TELEVİZYON VE SİNEMA",
        "Tekstil ve Moda Tasarımı",
        "İÇ MİMARLIK (TÜRKÇE-İNGİLİZCE)",
    ],
    "Konservatuvar": ["MÜZİK", "SAHNE SANATLARI"],
    "Beden Eğitimi ve Spor Yüksekokulu": [
        "ANTRENÖRLÜK EĞİTİMİ",
        "EGZERSİZ VE SPOR BİLİMLERİ",
        "REKREASYON",
        "SPOR YÖNETİCİLİĞİ",
    ],
    "Sivil Havacılık Yüksekokulu": [
        "HAVA TRAFİK KONTROLÜ",
        "HAVACILIK ELEKTRİK VE ELEKTRONİĞİ",
        "PİLOTAJ (İNGİLİZCE)",
        "UÇAK BAKIM VE ONARIM",
    ],
    "Uygulamalı Bilimler Yüksekokulu": [
        "BİLİŞİM SİSTEMLERİ VE TEKNOLOJİLERİ",
        "TURİZM REHBERLİĞİ",
        "ULUSLARARASI TİCARET VE İŞLETMECİLİK",
        "VERİ BİLİMİ VE ANALİTİĞİ",
        "YAZILIM GELİŞTİRME",
    ],
    "Sağlık Bilimleri Fakültesi": [
        "BESLENME VE DİYETETİK",
        "DİL VE KONUŞMA TERAPİSİ",
        "FİZYOTERAPİ VE REHABİLİTASYON",
        "HEMŞİRELİK",
        "EBELİK",
    ],
    "Meslek Yüksekokulu": [
        "AŞÇILIK",
        "BANKACILIK VE SİGORTACILIK",
        "BİLGİSAYAR PROGRAMCILIĞI",
        "DENİZ ULAŞTIRMA VE İŞLETME",
        "DIŞ TİCARET",
        "ELEKTRİK",
        "FOTOĞRAFÇILIK VE KAMERAMANLIK",
        "GRAFİK TASARIMI",
        "HALKLA İLİŞKİLER VE TANITIM",
        "İÇ MEKAN TASARIMI",
        "İNŞAAT TEKNOLOJİSİ",
        "İŞLETME YÖNETİMİ",
        "LOJİSTİK PROGRAMI",
        "MAKİNE",
        "MEKATRONİK",
        "Mobil Teknolojileri",
        "MİMARİ RESTORASYON",
        "MODA TASARIMI",
        "MUHASEBE VE VERGİ UYGULAMALARI",
        "Otomotiv Teknolojisi",
        "RADYO VE TELEVİZYON PROGRAMCILIĞI",
        "SİVİL HAVA ULAŞTIRMA İŞLETMECİLİĞİ",
        "SİVİL HAVACILIK KABİN HİZMETLERİ",
        "SPOR YÖNETİMİ",
        "TURİST REHBERLİĞİ",
        "TURİZM VE OTEL İŞLETMECİLİĞİ",
        "Uçak Teknolojisi",
        "ELEKTRONİK TEKNOLOJİSİ",
        "İNSANSIZ ARAÇ TEKNİKERLİĞİ",
        "MARINA VE YAT İŞLETMECİLİĞİ",
        "WEB TASARIMI VE KODLAMA",
        "YEŞİL VE EKOLOJİK BİNA TEKNİKERLİĞİ",
        "MAHKEME BÜRO HİZMETLERİ",
        "İNTERNET VE AĞ TEKNOLOJİLERİ",
    ],
    "Sağlık Hizmetleri Meslek Yüksekokulu": [
        "AĞIZ VE DİŞ SAĞLIĞI",
        "AMELİYATHANE HİZMETLERİ",
        "ANESTEZİ",
        "ÇOCUK GELİŞİMİ",
        "DİŞ PROTEZ TEKNOLOJİSİ",
        "DİYALİZ",
        "ECZANE HİZMETLERİ",
        "ELEKTRONÖROFİZYOLOJİ",
        "FİZYOTERAPİ",
        "İLK VE ACİL YARDIM",
        "İŞ SAĞLIĞI VE GÜVENLİĞİ",
        "ODYOMETRİ",
        "OPTİSYENLİK",
        "ORTOPEDİK PROTEZ VE ORTEZ",
        "PATOLOJİ LABORATUVAR TEKNİKLERİ",
        "RADYOTERAPİ",
        "SOSYAL HİZMETLER",
        "TIBBİ DOKÜMANTASYON VE SEKRETERLİK",
        "TIBBİ GÖRÜNTÜLEME TEKNİKLERİ",
        "TIBBİ LABORATUVAR TEKNİKLERİ",
        "TIBBİ VERİ İŞLEME TEKNİKERLİĞİ",
        "DİJİTAL SAĞLIK SİSTEMLERİ TEKNİKERLİĞİ",
        "BİYOMEDİKAL CİHAZ TEKNOLOJİLERİ",
    ],
}

# -------------------------------
# Modeller
# -------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Parola TEXT -> uzun hash'lerde patlamasın
    password = db.Column(db.Text, nullable=False)

class Student(db.Model):
    __tablename__ = "student"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    phone      = db.Column(db.String(30))
    school_no  = db.Column(db.String(30))
    added_by   = db.Column(db.String(80))
    status     = db.Column(db.String(20), default="cozulmedi")  # 'cozuldu'|'cozulmedi'
    department = db.Column(db.String(200))
    faculty    = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentNote(db.Model):
    __tablename__ = "student_note"
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    text       = db.Column(db.Text, nullable=False)
    author     = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------------
# Login Manager
# -------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------
# Formlar
# -------------------------------
class LoginForm(FlaskForm):
    # İlk aşamada CSRF'yi kapattım; form hatası akışı engellemesin
    class Meta:
        csrf = False
    username = StringField("Kullanıcı Adı", validators=[DataRequired()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit   = SubmitField("Giriş Yap")

# -------------------------------
# Routes
# -------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Kullanıcı bulunamadı!", "danger")
            return redirect(url_for("login"))

        if not check_password_hash(user.password, password):
            flash("Şifre yanlış!", "danger")
            return redirect(url_for("login"))

        # LOGIN OK
        login_user(user)

        print("LOGIN SUCCESS — SESSION:", dict(request.cookies))

        # REDIRECT’I SABİTLİYORUZ
        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/health")
def health():
    return "OK", 200

@app.route("/whoami")
@login_required
def whoami():
    return f"✅ {current_user.username}", 200

@app.route("/dashboard")
@login_required
def dashboard():

    # --- Güvenli DEBUG ---
    try:
        uname = getattr(current_user, "username", None)
        print("DEBUG — CURRENT_USER:", uname)
    except Exception as e:
        print("DEBUG — current_user ERROR:", e)

    try:
        print("DEBUG — REQUEST COOKIES:", dict(request.cookies))
    except Exception:
        pass
    # -----------------------

    q          = request.args.get("q", "").strip()
    status     = request.args.get("status", "").strip()
    department = request.args.get("department", "").strip()
    faculty    = request.args.get("faculty", "").strip()
    added_by   = request.args.get("added_by", "").strip()

    query = Student.query

    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Student.name.ilike(like),
            Student.phone.ilike(like),
            Student.school_no.ilike(like),
        ))
    if status in ("cozuldu", "cozulmedi"):
        query = query.filter(Student.status == status)
    if department:
        query = query.filter(Student.department.ilike(f"%{department}%"))
    if faculty:
        query = query.filter(Student.faculty.ilike(f"%{faculty}%"))
    if added_by:
        query = query.filter(Student.added_by == added_by)

    students = query.order_by(Student.id.desc()).all()

    added_by_options = [
        row[0] for row in db.session.query(Student.added_by)
        .distinct().order_by(Student.added_by.asc()).all()
        if row[0]
    ]

    return render_template(
        "dashboard.html",
        students=students,
        q=q, status=status, department=department, faculty=faculty,
        added_by=added_by, added_by_options=added_by_options,
        faculties=FACULTY_DEPARTMENTS
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name       = (request.form.get("name") or "").strip()
        phone      = (request.form.get("phone") or "").strip()
        school_no  = (request.form.get("school_no") or "").strip()
        department = (request.form.get("department") or "").strip()
        faculty    = (request.form.get("faculty") or "").strip()
        status     = request.form.get("status", "cozulmedi")

        if not name:
            flash("İsim zorunlu.", "danger")
            return render_template("add_student.html", faculties=FACULTY_DEPARTMENTS)

        s = Student(
            name=name,
            phone=phone or None,
            school_no=school_no or None,
            department=department or None,
            faculty=faculty or None,
            status=status if status in ("cozuldu", "cozulmedi") else "cozulmedi",
            added_by=current_user.username,
        )
        db.session.add(s)
        db.session.commit()
        flash("Öğrenci eklendi.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_student.html", faculties=FACULTY_DEPARTMENTS)

@app.route("/student/<int:id>")
@login_required
def view_student(id):
    s = Student.query.get_or_404(id)

    # Form POST geldiyse: not ekle + durum değiştir
    if request.method == "POST":
        note_text = (request.form.get("note") or "").strip()
        new_status = (request.form.get("status") or "").strip()

        if note_text:
            n = StudentNote(student_id=id, text=note_text, author=current_user.username)
            db.session.add(n)

        if new_status in ("cozuldu", "cozulmedi"):
            s.status = new_status

        db.session.commit()
        flash("Detay güncellendi.", "success")
        return redirect(url_for("view_student", id=id))

    notes = StudentNote.query.filter_by(student_id=id) \
                             .order_by(StudentNote.created_at.desc()).all()
    return render_template("view_student.html", student=s, notes=notes)

@app.route("/student/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(id):
    s = Student.query.get_or_404(id)
    if request.method == "POST":
        s.name       = request.form.get("name", s.name)
        s.phone      = request.form.get("phone", s.phone)
        s.school_no  = request.form.get("school_no", s.school_no)
        s.department = request.form.get("department", s.department)
        s.faculty    = request.form.get("faculty", s.faculty)
        new_status   = request.form.get("status", s.status)
        if new_status in ("cozuldu", "cozulmedi"):
            s.status = new_status
        db.session.commit()
        flash("Öğrenci güncellendi.", "success")
        return redirect(url_for("view_student", id=id))

    return render_template("edit_student.html", student=s, faculties=FACULTY_DEPARTMENTS)

@app.route("/student/<int:id>/delete", methods=["POST"])
@login_required
def delete_student(id):
    s = Student.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Öğrenci silindi.", "success")
    return redirect(url_for("dashboard"))

@app.route("/student/<int:id>/note", methods=["POST"])
@login_required
def add_note(id):
    s = Student.query.get_or_404(id)
    note_text  = (request.form.get("note") or "").strip()
    new_status = (request.form.get("status") or "").strip()
    if note_text:
        n = StudentNote(student_id=id, text=note_text, author=current_user.username)
        db.session.add(n)
    if new_status in ("cozuldu", "cozulmedi"):
        s.status = new_status
    db.session.commit()
    flash("Detay güncellendi.", "success")
    return redirect(url_for("view_student", id=id))

@app.route("/note/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    n = StudentNote.query.get_or_404(note_id)
    if n.author != current_user.username and current_user.username != "helpadmin":
        flash("Bu notu silme yetkin yok.", "danger")
        return redirect(url_for("view_student", id=n.student_id))
    sid = n.student_id
    db.session.delete(n)
    db.session.commit()
    flash("Not silindi.", "success")
    return redirect(url_for("view_student", id=sid))

@app.route("/main")
@login_required
def main_screen():
    rows = db.session.query(Student.added_by, func.count(Student.id))\
        .group_by(Student.added_by)\
        .order_by(func.count(Student.id).desc())\
        .all()
    total = db.session.query(func.count(Student.id)).scalar() or 0
    return render_template("main.html", rows=rows, total=total)

@app.get("/__routes")
def __routes():
    lines = []
    for r in app.url_map.iter_rules():
        methods = ",".join(sorted(m for m in r.methods if m not in ("HEAD","OPTIONS")))
        lines.append(f"{r.rule:35s} -> {methods}  ({r.endpoint})")
    return "<pre>" + "\n".join(sorted(lines)) + "</pre>"

@app.route("/debug")
def debug():
    return {"cookies": dict(request.cookies)}

# -------------------------------
# Migration / bakım endpoint'leri
# -------------------------------
@app.get("/__seed_admin")
def seed_admin():
    token = request.args.get("token")
    if token != INIT_TOKEN:
        abort(403)
    if not User.query.filter_by(username="helpadmin").first():
        db.session.add(User(username="helpadmin",
                            password=generate_password_hash("Admin123!")))
        db.session.commit()
    return "OK: helpadmin/Admin123!", 200

@app.get("/__migrate_all")
def migrate_all():
    token = request.args.get("token")
    if token != INIT_TOKEN:
        abort(403)

    driver = db.engine.url.get_backend_name()  # 'postgresql' ya da 'sqlite'

    stmts = []
    # users.password -> TEXT
    stmts.append("ALTER TABLE users ALTER COLUMN password TYPE TEXT")

    if driver.startswith("postgresql"):
        # Postgres: IF NOT EXISTS var
        stmts += [
            "ALTER TABLE student ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'cozulmedi'",
            "ALTER TABLE student ADD COLUMN IF NOT EXISTS department VARCHAR(200)",
            "ALTER TABLE student ADD COLUMN IF NOT EXISTS faculty VARCHAR(200)",
            "ALTER TABLE student ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()",
        ]
    else:
        # SQLite: IF NOT EXISTS yok, try/except ile deneriz
        stmts += [
            "ALTER TABLE student ADD COLUMN status VARCHAR(20) DEFAULT 'cozulmedi'",
            "ALTER TABLE student ADD COLUMN department VARCHAR(200)",
            "ALTER TABLE student ADD COLUMN faculty VARCHAR(200)",
            "ALTER TABLE student ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]

    with db.engine.begin() as conn:
        for s in stmts:
            try:
                conn.execute(text(s))
            except Exception as e:
                print(f"[migrate_all] {s} -> {e}")

    return "OK: migrate_all", 200

@app.get("/__migrate_pwlen")
def migrate_pwlen():
    token = request.args.get("token")
    if token != INIT_TOKEN:
        abort(403)
    sql = "ALTER TABLE users ALTER COLUMN password TYPE TEXT"
    with db.engine.begin() as conn:
        try:
            conn.execute(text(sql))
        except Exception as e:
            print(f"[migrate_pwlen] {e}")
    return "OK: users.password -> TEXT", 200

@app.get("/__migrate_students")
def migrate_students():
    token = request.args.get("token")
    if token != INIT_TOKEN:
        abort(403)

    stmts = [
        "ALTER TABLE student ALTER COLUMN name TYPE VARCHAR(150)",
        "ALTER TABLE student ALTER COLUMN phone TYPE VARCHAR(30)",
        "ALTER TABLE student ALTER COLUMN school_no TYPE VARCHAR(30)",
        "ALTER TABLE student ALTER COLUMN added_by TYPE VARCHAR(80)",
        "ALTER TABLE student ALTER COLUMN status TYPE VARCHAR(20)",
        "ALTER TABLE student ALTER COLUMN department TYPE VARCHAR(200)",
        "ALTER TABLE student ALTER COLUMN faculty TYPE VARCHAR(200)",
    ]
    with db.engine.begin() as conn:
        for s in stmts:
            try:
                conn.execute(text(s))
            except Exception as e:
                print(f"[migrate_students] {s} -> {e}")
    return "OK: student columns normalized", 200

@app.get("/__migrate_created_at")
def migrate_created_at():
    token = request.args.get("token")
    if token != INIT_TOKEN:
        abort(403)

    driver = db.engine.url.get_backend_name()
    if driver.startswith("postgresql"):
        sql = "ALTER TABLE student ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()"
    else:
        sql = "ALTER TABLE student ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

    with db.engine.begin() as conn:
        try:
            conn.execute(text(sql))
        except Exception as e:
            print(f"[migrate_created_at] {e}")
    return "OK: created_at ensured", 200
# -------------------------------
# Çalıştırma
# -------------------------------
if __name__ == "__main__":
   
   with app.app_context():
    # Localde tablo yoksa oluştursun; prod'da migration endpointi kullanıyoruz
    db.create_all()
    # Parola TEXT'e zorla (PG'de eski şema varsa)
    try:
        if db.engine.url.get_backend_name().startswith("postgresql"):
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ALTER COLUMN password TYPE TEXT"))
    except Exception:
        pass
    # Admin yoksa ekle
    if not User.query.filter_by(username="helpadmin").first():
        db.session.add(User(username="helpadmin", password=generate_password_hash("Admin123!")))
        db.session.commit()
        print("✅ Admin oluşturuldu: helpadmin / Admin123!")
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
