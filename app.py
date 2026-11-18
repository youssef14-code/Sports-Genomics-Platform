# app.py
import logging
import sys
from flask import Flask, request, jsonify, render_template
from config import Config
from models.models import db, Athlete, GenomicsReport
from services.pdf_service import extract_text_from_pdf
from services.llm_report_engine import generate_sports_genomics_report

# إعداد الـ Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("App")

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    """عرض صفحة الـ Dashboard الإكلينيكية"""
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze_endpoint():
    """استقبال الـ PDF وبيانات الرياضي وتوليد التقرير الجيني"""
    if "pdf" not in request.files:
        return jsonify({"success": False, "error": "يرجى رفع ملف فحص الـ PDF"}), 400

    pdf_file = request.files["pdf"]
    if pdf_file.filename == "":
        return jsonify({"success": False, "error": "اسم الملف فارغ"}), 400

    # استقبال البيانات الإكلينيكية والقياسات
    athlete_meta = {
        "name": request.form.get("name", "كابتن / رياضي"),
        "age": request.form.get("age", "22"),
        "sport": request.form.get("sport", "كرة قدم"),
        "height": request.form.get("height", "180"),
        "weight": request.form.get("weight", "75"),
        "injuries": request.form.get("injuries", "لا توجد إصابات سابقة مسجلة")
    }

    try:
        logger.info(f"Processing athlete: {athlete_meta['name']} | Sport: {athlete_meta['sport']}")
        
        # 1. استخراج النص من ملف الـ PDF
        raw_text = extract_text_from_pdf(pdf_file.read())
        if not raw_text.strip():
            return jsonify({"success": False, "error": "ملف الـ PDF لا يحتوي على نصوص قابلة للقراءة (تأكد أنه ليس صورة ممسوحة ضوئياً)."}), 400

        # 2. توليد التقرير وفحص المستند بواسطة الـ LLM
        result = generate_sports_genomics_report(raw_text, athlete_meta)

        # إذا رفض الـ AI المستند لأنه ليس فحصاً جينياً رياضياً
        if not result.get("success", False):
            rejection_reason = result.get("error", "المستند المرفوع لا يحتوي على تحاليل جينية رياضية صالحة.")
            logger.warning(f"Analysis rejected: {rejection_reason}")
            return jsonify({
                "success": False,
                "error": rejection_reason
            }), 400

        # تحويل محتوى الرد إلى نص صريح تماماً
        raw_report = result.get("report", "")
        if isinstance(raw_report, list):
            report_text = "\n".join(b.get("text", str(b)) if isinstance(b, dict) else str(b) for b in raw_report)
        elif isinstance(raw_report, dict):
            report_text = raw_report.get("text", str(raw_report))
        else:
            report_text = str(raw_report)

        if not report_text.strip():
            return jsonify({"success": False, "error": "لم يتم استخراج أي بيانات جينية من الملف."}), 400

        # 3. حفظ بيانات الرياضي والتقرير في قاعدة البيانات (MySQL)
        try:
            athlete = Athlete.query.filter_by(full_name=athlete_meta["name"]).first()
            if not athlete:
                athlete = Athlete(
                    full_name=athlete_meta["name"],
                    sport=athlete_meta["sport"]
                )
                db.session.add(athlete)
                db.session.commit()

            metrics = result.get("metrics", {})
            report_rec = GenomicsReport(
                athlete_id=athlete.id,
                filename=pdf_file.filename,
                raw_text=raw_text[:2500],
                generated_report=report_text,
                prompt_tokens=int(metrics.get("input_tokens", 0)),
                completion_tokens=int(metrics.get("output_tokens", 0)),
                total_tokens=int(metrics.get("total_tokens", 0)),
                cost_usd=float(metrics.get("cost_usd", 0.0)),
                latency_sec=float(metrics.get("latency", 0.0))
            )
            db.session.add(report_rec)
            db.session.commit()
            logger.info(f"Report saved to DB with ID: {report_rec.id}")
        except Exception as db_err:
            logger.warning(f"Database save warning: {db_err}")
            db.session.rollback()

        # 4. إرجاع النتيجة للـ UI
        return jsonify({
            "success": True,
            "report": report_text
        })

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4500, debug=True)