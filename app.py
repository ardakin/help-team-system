from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import text, inspect
from sqlalchemy import text, inspect, func, or_
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, abort
import os
# User(password=generate_password_hash('Admin123!', method='pbkdf2:sha256'))



import os

load_dotenv()

# -------------------------------
# Fakülte -> Bölümler sözlüğü
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

app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,    # PaaS HTTPS arkasında
    REMEMBER_COOKIE_SECURE=True
)

# HTTPS güvenlik başlıkları (CSP’yi sade tuttum)
csp = {
  'default-src': ["'self'"],
  'img-src': ["'self'", "data:", "https:"],
  'style-src': ["'self'", "'unsafe-inline'", "https:"],
  'script-src': ["'self'", "'unsafe-inline'", "https:"],
  'font-src': ["'self'", "https:", "data:"]
}
Talisman(app, content_security_policy=csp, force_https=True, strict_transport_security=True)

# IP başına oran sınırlama (genel)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"])
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///students.db')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ------------------ Modeller ------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    school_no = db.Column(db.String(20))
    added_by = db.Column(db.String(150))
    status = db.Column(db.String(20), default='cozulmedi')  # 'cozuldu' | 'cozulmedi'
    department = db.Column(db.String(200))   # Bölüm
    faculty = db.Column(db.String(200))      # Fakülte

class StudentNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ Form ------------------
class LoginForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit = SubmitField("Giriş Yap")

# ------------------ Rotalar ------------------

@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Kullanıcı adı veya şifre hatalı", "danger")
    return render_template("login.html", form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    q = request.args.get('q', '').strip()              # <-- tek serbest arama kutusu
    status = request.args.get('status', '').strip()
    department = request.args.get('department', '').strip()
    faculty = request.args.get('faculty', '').strip()
    added_by = request.args.get('added_by', '').strip()

    query = Student.query
    if q:
        query = query.filter(or_(                      # isim/telefon/okul no birlikte
            Student.name.ilike(f"%{q}%"),
            Student.phone.ilike(f"%{q}%"),
            Student.school_no.ilike(f"%{q}%"),
        ))
    if department:
        query = query.filter(Student.department.ilike(f"%{department}%"))
    if faculty:
        query = query.filter(Student.faculty.ilike(f"%{faculty}%"))
    if status in ('cozuldu', 'cozulmedi'):
        query = query.filter(Student.status == status)
    if added_by:
        query = query.filter(Student.added_by == added_by)

    students = query.order_by(Student.id.desc()).all()

    added_by_options = [row[0] for row in db.session.query(Student.added_by)
                        .distinct().order_by(Student.added_by.asc()).all() if row[0]]

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
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        school_no = request.form.get("school_no", "").strip()
        status = request.form.get("status", "cozulmedi")
        department = request.form.get("department", "").strip()
        faculty = request.form.get("faculty", "").strip()

        if not name:
            flash("İsim zorunlu.", "danger")
            return render_template("add_student.html", faculties=FACULTY_DEPARTMENTS)

        s = Student(
            name=name,
            phone=phone or None,
            school_no=school_no or None,
            added_by=current_user.username,
            status=status if status in ("cozuldu", "cozulmedi") else "cozulmedi",
            department=department or None,
            faculty=faculty or None
        )
        db.session.add(s)
        db.session.commit()
        flash("Öğrenci eklendi.", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_student.html", faculties=FACULTY_DEPARTMENTS)

@app.route("/student/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(id):
    s = Student.query.get_or_404(id)
    if request.method == "POST":
        s.name = request.form.get("name", s.name)
        s.phone = request.form.get("phone", s.phone)
        s.school_no = request.form.get("school_no", s.school_no)
        s.department = request.form.get("department", s.department)
        s.faculty = request.form.get("faculty", s.faculty)
        new_status = request.form.get("status", s.status)
        if new_status in ("cozuldu", "cozulmedi"):
            s.status = new_status
        db.session.commit()
        flash("Öğrenci bilgileri güncellendi.", "success")
        return redirect(url_for("view_student", id=id))
    return render_template("edit_student.html", student=s, faculties=FACULTY_DEPARTMENTS)

@app.route("/note/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    n = StudentNote.query.get_or_404(note_id)
    # yalnızca yazan veya admin silebilir
    if n.author != current_user.username and current_user.username != "helpadmin":
        flash("Bu notu silme yetkin yok.", "danger")
        return redirect(url_for("view_student", id=n.student_id))
    sid = n.student_id
    db.session.delete(n)
    db.session.commit()
    flash("Not silindi.", "success")
    return redirect(url_for("view_student", id=sid))

@app.route("/student/<int:id>/delete", methods=["POST"])
@login_required
def delete_student(id):
    s = Student.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Öğrenci silindi.", "success")
    return redirect(url_for("dashboard"))

@app.route("/student/<int:id>", methods=["GET", "POST"])
@login_required
def view_student(id):
    s = Student.query.get_or_404(id)
    if request.method == "POST":
        note_text = request.form.get("note", "").strip()
        new_status = request.form.get("status", "").strip()
        if note_text:
            n = StudentNote(student_id=id, text=note_text, author=current_user.username)
            db.session.add(n)
        if new_status in ("cozuldu", "cozulmedi"):
            s.status = new_status
        db.session.commit()
        flash("Detay güncellendi.", "success")
        return redirect(url_for("view_student", id=id))

    notes = StudentNote.query.filter_by(student_id=id).order_by(StudentNote.created_at.desc()).all()
    return render_template("view_student.html", student=s, notes=notes)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/main")
@login_required
def main_screen():
    rows = db.session.query(
        Student.added_by, func.count(Student.id)
    ).group_by(Student.added_by).order_by(func.count(Student.id).desc()).all()

    total = db.session.query(func.count(Student.id)).scalar() or 0
    return render_template("main.html", rows=rows, total=total)

@app.route("/init_db")
def init_db():
    token = request.args.get("token", "")
    if token != os.getenv("INIT_TOKEN"):
        abort(403)
    with app.app_context():
        db.create_all()
        from app import User
        if not User.query.filter_by(username="helpadmin").first():
            u = User(username="helpadmin", password=generate_password_hash("Admin123!", method="pbkdf2:sha256"))
            db.session.add(u)
            db.session.commit()
    return "✅ Veritabanı oluşturuldu, admin: helpadmin / Admin123!"

# ------------------ Main ------------------
if __name__ == "__main__":
    # DB migration-benzeri güvenli eklemeler
    with app.app_context():
        db.create_all()
        insp = inspect(db.engine)
        cols = [c["name"] for c in insp.get_columns("student")]

        if "status" not in cols:
            db.session.execute(text("ALTER TABLE student ADD COLUMN status VARCHAR(20) DEFAULT 'cozulmedi'"))
            db.session.commit()
        if "department" not in cols:
            db.session.execute(text("ALTER TABLE student ADD COLUMN department VARCHAR(200)"))
            db.session.commit()
        if "faculty" not in cols:
            db.session.execute(text("ALTER TABLE student ADD COLUMN faculty VARCHAR(200)"))
            db.session.commit()

    app.run(debug=True)
