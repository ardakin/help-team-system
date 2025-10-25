import os
from datetime import datetime

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for, flash, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import text, func, or_
from sqlalchemy.exc import DataError, ProgrammingError
from werkzeug.security import check_password_hash, generate_password_hash

# -------------------------------------------------------------------
# 0) ENV + Fakülte/Bölüm sözlüğü
# -------------------------------------------------------------------
load_dotenv()

FACULTY_DEPARTMENTS = {
    "Tıp Fakültesi": ["TIP"],
    "Diş Hekimliği Fakültesi": ["DİŞ HEKİMLİĞİ"],
    "İktisadi, İdari ve Sosyal Bilimler Fakültesi": [
        "EKONOMİ", "EKONOMİ VE FİNANS", "FİNANS VE BANKACILIK",
        "HALKLA İLİŞKİLER VE REKLAMCILIK",
        "HAVACILIK YÖNETİMİ (TÜRKÇE-İNGİLİZCE)",
        "İNGİLİZ DİLİ VE EDEBİYATI (İNGİLİZCE)",
        "İNGİLİZCE MÜTERCİM TERCÜMANLIK",
        "İŞLETME (TÜRKÇE - İNGİLİZCE)",
        "PSİKOLOJİ (TÜRKÇE-İNGİLİZCE)",
        "SİYASET BİLİMİ VE KAMU YÖNETİMİ",
        "MUHASEBE VE FİNANS YÖNETİMİ",
        "SERMAYE PİYASASI",
        "SOSYAL HİZMET", "SOSYOLOJİ", "TURİZM İŞLETMECİLİĞİ",
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
        "DİJİTAL OYUN TASARIMI", "ENDÜSTRİYEL TASARIM",
        "GASTRONOMİ VE MUTFAK SANATLARI (TÜRKÇE - İNGİLİZCE)",
        "GRAFİK TASARIMI", "İLETİŞİM VE TASARIMI",
        "RADYO, TELEVİZYON VE SİNEMA",
        "Tekstil ve Moda Tasarımı", "İÇ MİMARLIK (TÜRKÇE-İNGİLİZCE)",
    ],
    "Konservatuvar": ["MÜZİK", "SAHNE SANATLARI"],
    "Beden Eğitimi ve Spor Yüksekokulu": [
        "ANTRENÖRLÜK EĞİTİMİ", "EGZERSİZ VE SPOR BİLİMLERİ",
        "REKREASYON", "SPOR YÖNETİCİLİĞİ",
    ],
    "Sivil Havacılık Yüksekokulu": [
        "HAVA TRAFİK KONTROLÜ", "HAVACILIK ELEKTRİK VE ELEKTRONİĞİ",
        "PİLOTAJ (İNGİLİZCE)", "UÇAK BAKIM VE ONARIM",
    ],
    "Uygulamalı Bilimler Yüksekokulu": [
        "BİLİŞİM SİSTEMLERİ VE TEKNOLOJİLERİ",
        "TURİZM REHBERLİĞİ", "ULUSLARARASI TİCARET VE İŞLETMECİLİK",
        "VERİ BİLİMİ VE ANALİTİĞİ", "YAZILIM GELİŞTİRME",
    ],
    "Sağlık Bilimleri Fakültesi": [
        "BESLENME VE DİYETETİK", "DİL VE KONUŞMA TERAPİSİ",
        "FİZYOTERAPİ VE REHABİLİTASYON", "HEMŞİRELİK", "EBELİK",
    ],
    "Meslek Yüksekokulu": [
        "AŞÇILIK", "BANKACILIK VE SİGORTACILIK",
        "BİLGİSAYAR PROGRAMCILIĞI", "DENİZ ULAŞTIRMA VE İŞLETME",
        "DIŞ TİCARET", "ELEKTRİK", "FOTOĞRAFÇILIK VE KAMERAMANLIK",
        "GRAFİK TASARIMI", "HALKLA İLİŞKİLER VE TANITIM",
        "İÇ MEKAN TASARIMI", "İNŞAAT TEKNOLOJİSİ",
        "İŞLETME YÖNETİMİ", "LOJİSTİK PROGRAMI", "MAKİNE",
        "MEKATRONİK", "Mobil Teknolojileri", "MİMARİ RESTORASYON",
        "MODA TASARIMI", "MUHASEBE VE VERGİ UYGULAMALARI",
        "Otomotiv Teknolojisi", "RADYO VE TELEVİZYON PROGRAMCILIĞI",
        "SİVİL HAVA ULAŞTIRMA İŞLETMECİLİĞİ",
        "SİVİL HAVACILIK KABİN HİZMETLERİ",
        "SPOR YÖNETİMİ", "TURİST REHBERLİĞİ",
        "TURİZM VE OTEL İŞLETMECİLİĞİ",
        "Uçak Teknolojisi", "ELEKTRONİK TEKNOLOJİSİ",
        "İNSANSIZ ARAÇ TEKNİKERLİĞİ", "MARINA VE YAT İŞLETMECİLİĞİ",
        "WEB TASARIMI VE KODLAMA", "YEŞİL VE EKOLOJİK BİNA TEKNİKERLİĞİ",
        "MAHKEME BÜRO HİZMETLERİ", "İNTERNET VE AĞ TEKNOLOJİLERİ",
    ],
    "Sağlık Hizmetleri Meslek Yüksekokulu": [
        "AĞIZ VE DİŞ SAĞLIĞI", "AMELİYATHANE HİZMETLERİ", "ANESTEZİ",
        "ÇOCUK GELİŞİMİ", "DİŞ PROTEZ TEKNOLOJİSİ", "DİYALİZ",
        "ECZANE HİZMETLERİ", "ELEKTRONÖROFİZYOLOJİ", "FİZYOTERAPİ",
        "İLK VE ACİL YARDIM", "İŞ SAĞLIĞI VE GÜVENLİĞİ", "ODYOMETRİ",
        "OPTİSYENLİK", "ORTOPEDİK PROTEZ VE ORTEZ",
        "PATOLOJİ LABORATUVAR TEKNİKLERİ", "RADYOTERAPİ",
        "SOSYAL HİZMETLER", "TIBBİ DOKÜMANTASYON VE SEKRETERLİK",
        "TIBBİ GÖRÜNTÜLEME TEKNİKLERİ", "TIBBİ LABORATUVAR TEKNİKLERİ",
        "TIBBİ VERİ İŞLEME TEKNİKERLİĞİ", "DİJİTAL SAĞLIK SİSTEMLERİ TEKNİKERLİĞİ",
        "BİYOMEDİKAL CİHAZ TEKNOLOJİLERİ",
    ],
}

# -------------------------------------------------------------------
# 1) APP + DB + LOGIN
# -------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

uri = os.getenv("DATABASE_URL", "sqlite:///students.db")
# Render gibi ortamlarda eski "postgres://" gelebilir → normalize et
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

INIT_TOKEN = os.getenv("INIT_TOKEN", "dev-token")  # /__migrate_pwlen ve /__init_db için


# -------------------------------------------------------------------
# 2) MODELLER
# -------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # UZUN HASH'LER İÇİN TEXT: scrypt/argon vs rahat sığar.
    password = db.Column(db.Text, nullable=False)


class Student(db.Model):
    __tablename__ = "student"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    phone      = db.Column(db.String(20))
    school_no  = db.Column(db.String(20))
    added_by   = db.Column(db.String(150))
    status     = db.Column(db.String(20), default="cozulmedi")  # cozuldu / cozulmedi
    department = db.Column(db.String(200))  # Bölüm
    faculty    = db.Column(db.String(200))  # Fakülte


class StudentNote(db.Model):
    __tablename__ = "student_note"
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    text       = db.Column(db.Text, nullable=False)
    author     = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id: str):
    # SQLAlchemy 2.0 stili:
    return db.session.get(User, int(user_id))


# -------------------------------------------------------------------
# 3) FORMLAR
# -------------------------------------------------------------------
class LoginForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit   = SubmitField("Giriş Yap")


# -------------------------------------------------------------------
# 4) ROTALAR
# -------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    """Login ekranı (hem GET hem POST)."""
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data.strip()).first()
        if u and check_password_hash(u.password, form.password.data):
            login_user(u)
            return redirect(url_for("dashboard"))
        flash("Kullanıcı adı veya şifre hatalı", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    """Liste + arama + filtre ekranı."""
    q          = request.args.get("q", "").strip()
    status     = request.args.get("status", "").strip()
    department = request.args.get("department", "").strip()
    faculty    = request.args.get("faculty", "").strip()
    added_by   = request.args.get("added_by", "").strip()

    query = Student.query

    if q:
        query = query.filter(or_(
            Student.name.ilike(f"%{q}%"),
            Student.phone.ilike(f"%{q}%"),
            Student.school_no.ilike(f"%{q}%"),
        ))
    if department:
        query = query.filter(Student.department.ilike(f"%{department}%"))
    if faculty:
        query = query.filter(Student.faculty.ilike(f"%{faculty}%"))
    if status in ("cozuldu", "cozulmedi"):
        query = query.filter(Student.status == status)
    if added_by:
        query = query.filter(Student.added_by == added_by)

    students = query.order_by(Student.id.desc()).all()

    added_by_options = [
        row[0] for row in (
            db.session.query(Student.added_by)
                      .distinct().order_by(Student.added_by.asc()).all()
        ) if row[0]
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
    """Öğrenci ekleme."""
    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        phone      = request.form.get("phone", "").strip()
        school_no  = request.form.get("school_no", "").strip()
        status     = request.form.get("status", "cozulmedi").strip()
        department = request.form.get("department", "").strip()
        faculty    = request.form.get("faculty", "").strip()

        if not name:
            flash("İsim zorunludur.", "danger")
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


@app.route("/student/<int:student_id>", methods=["GET", "POST"])
@login_required
def view_student(student_id: int):
    """Öğrenci detay + not ekle + durum güncelle."""
    s = db.session.get(Student, student_id) or abort(404)

    if request.method == "POST":
        note_text = request.form.get("note", "").strip()
        new_status = request.form.get("status", "").strip()

        if note_text:
            n = StudentNote(student_id=student_id, text=note_text,
                            author=current_user.username)
            db.session.add(n)

        if new_status in ("cozuldu", "cozulmedi"):
            s.status = new_status

        db.session.commit()
        flash("Detay güncellendi.", "success")
        return redirect(url_for("view_student", student_id=student_id))

    notes = (StudentNote.query
             .filter_by(student_id=student_id)
             .order_by(StudentNote.created_at.desc())
             .all())

    return render_template("view_student.html", student=s, notes=notes)


@app.route("/student/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id: int):
    """Öğrenci temel bilgileri düzenleme."""
    s = db.session.get(Student, student_id) or abort(404)

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
        flash("Öğrenci bilgileri güncellendi.", "success")
        return redirect(url_for("view_student", student_id=student_id))

    return render_template("edit_student.html", student=s,
                           faculties=FACULTY_DEPARTMENTS)


@app.route("/student/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id: int):
    """Öğrenci silme."""
    s = db.session.get(Student, student_id) or abort(404)
    db.session.delete(s)
    db.session.commit()
    flash("Öğrenci silindi.", "success")
    return redirect(url_for("dashboard"))


@app.route("/note/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id: int):
    """Not silme (sadece yazan veya helpadmin)."""
    n = db.session.get(StudentNote, note_id) or abort(404)
    if n.author != current_user.username and current_user.username != "helpadmin":
        flash("Bu notu silme yetkin yok.", "danger")
        return redirect(url_for("view_student", student_id=n.student_id))

    sid = n.student_id
    db.session.delete(n)
    db.session.commit()
    flash("Not silindi.", "success")
    return redirect(url_for("view_student", student_id=sid))


@app.route("/main")
@login_required
def main_screen():
    """Kimin kaç öğrenci eklediğine dair küçük özet."""
    rows = (db.session.query(Student.added_by, func.count(Student.id))
            .group_by(Student.added_by)
            .order_by(func.count(Student.id).desc())
            .all())

    total = db.session.query(func.count(Student.id)).scalar() or 0
    return render_template("main.html", rows=rows, total=total)


# -------------------------------------------------------------------
# 5) YÖNETİM / İLK KURULUM ENDPOINT'LERİ (token'lı)
# -------------------------------------------------------------------
@app.get("/__migrate_pwlen")
def migrate_pwlen():
    """
    Amaç: PostgreSQL'de users.password kolonunu TEXT'e büyütmek.
    Kullanım: /__migrate_pwlen?token=<INIT_TOKEN>
    """
    token = request.args.get("token", "")
    if token != INIT_TOKEN:
        abort(403)

    # SQLite'ta ALTER TYPE yok; Postgres'te çalışır
    if db.engine.url.get_backend_name().startswith("postgresql"):
        sql = "ALTER TABLE users ALTER COLUMN password TYPE TEXT;"
        try:
            with db.engine.begin() as conn:
                conn.execute(text(sql))
        except ProgrammingError:
            # tablo veya kolon yoksa vb. hata → görmezden gel
            pass
    else:
        # SQLite / MySQL durumunda model TEXT olduğu için genellikle sorun çıkmaz.
        pass

    return "OK: users.password -> TEXT", 200


@app.get("/__init_db")
def init_db():
    """
    Amaç: Tabloları oluştur ve admin yoksa 'helpadmin / Admin123!' ekle.
    Kullanım: /__init_db?token=<INIT_TOKEN>
    """
    token = request.args.get("token", "")
    if token != INIT_TOKEN:
        abort(403)

    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(username="helpadmin").first()
        if not admin:
            admin = User(
                username="helpadmin",
                password=generate_password_hash("Admin123!")
            )
            db.session.add(admin)
            try:
                db.session.commit()
            except DataError:
                # Kolon dar ise önce migrate endpoint'ini çalıştır.
                return ("HATA: users.password kolonu dar. "
                        "Önce /__migrate_pwlen?token=... çağırın."), 500

    return "OK: DB hazır + admin eklendi (helpadmin / Admin123!)", 200


# -------------------------------------------------------------------
# 6) LOCAL ÇALIŞTIRMA
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Local geliştirme için:
    # - İlk kez kurulumda sırayla:
    #   1) /__migrate_pwlen?token=INIT_TOKEN
    #   2) /__init_db?token=INIT_TOKEN
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
