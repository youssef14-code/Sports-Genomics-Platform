# services/llm_report_engine.py
import json
import os
import time
import logging
from config import Config
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("LLMEngine")

def get_gemini():
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set in your .env file.")

    return ChatOpenAI(
        model=Config.OPENAI_MODEL,
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        use_responses_api=True,
        reasoning={"effort": "medium"},
        temperature=0.0,
    )

def load_scientific_kb():
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    possible_names = ["curated_genomics_data.json", "extracted_genomics_knowledge.json"]
    for name in possible_names:
        path = os.path.join(base_dir, name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}

def generate_sports_genomics_report(patient_raw_text: str, athlete_meta: dict = None) -> dict:
    llm = get_gemini()
    kb = load_scientific_kb()
    kb_findings = json.dumps(kb.get("papers", [])[:15], ensure_ascii=False)

    meta = athlete_meta or {}
    athlete_profile_summary = f"""
ATHLETE ANTHROPOMETRIC & CLINICAL DOSSIER:
- Full Name: {meta.get('name', 'كابتن / رياضي')}
- Chronological Age: {meta.get('age', '22')} years
- Sport & Positional Role: {meta.get('sport', 'كرة قدم')}
- Stature / Height: {meta.get('height', '180')} cm
- Body Mass / Weight: {meta.get('weight', '75')} kg
- Reported Musculoskeletal History: {meta.get('injuries', 'لا يوجد')}
"""

    system_instruction = f"""
You are a Senior Precision Sports & Clinical Genomicist and Clinical Data Auditor.

GATE 1: DOCUMENT AUTHENTICITY & CLASSIFICATION (MANDATORY FIRST STEP):
Examine the uploaded document text thoroughly.
- IF the document is NOT an authentic athletic genetic / sports genomics DNA laboratory report (e.g., if it is a CV/Resume, dermatology/skin report, cosmetic analysis, blood test without genetic variants/rsIDs, invoice, or unrelated text):
  YOU MUST IMMEDIATELY TERMINATE AND OUTPUT ONLY:
  INVALID_DOCUMENT: [سبب الرفض بالعربية مع تحديد طبيعة الملف المرفوع مثل: هذا الملف يمثل تقرير فحص جلدي (Skin Report) ولا يحتوي على تحاليل جينات رياضية أو طفرات أداء]
  DO NOT OUTPUT ANY REPORT TEMPLATE OR SECTION.

GATE 2: DYNAMIC INJURY RISK INDEX (IRI%) CALCULATION:
If and only if the document contains genuine sports DNA variants:
Calculate the IRI dynamically based on the detected variants + physical data:
- Base Risk: 15%
- Tendon Genetics (COL5A1 TT/CT: +15-25%, COL1A1 GT/GG: +10-15%, COL1A1 TT: -10%)
- Recovery Genetics (SOD2 Val/Val: +10%, IL6 GG: +10%)
- Biomechanical & History: Previous injury history (+15%), High body mass at explosive sprinting (+10%)
Sum the score and output the exact calculated percentage (e.g. 68% or 45% or 82%) with classification [منخفض / متوسط / مرتفع].

CURATED PUBMED EVIDENCE GROUND TRUTH:
{kb_findings}

REQUIRED CLINICAL REPORT TEMPLATE:
================================================================================
               PRECISION SPORTS & CLINICAL GENOMICS PLATFORM
               مؤشر الجاهزية الإكلينيكية والوقائية للرياضيين (EBM-Driven)
================================================================================
• اسم الرياضي: {meta.get('name')}               • العمر: {meta.get('age')} سنة ({meta.get('height')} سم / {meta.get('weight')} كجم)
• الرياضة: {meta.get('sport')}       • المعرف الإكلينيكي: SG-2026-PRO
• تاريخ التقارير الجينية: نوفمبر 2026         • مؤشر خطر الإصابة العام (IRI): [النسبة المحسوبة % - التصنيف]
--------------------------------------------------------------------------------

[1] المسار الأول: البروفايل الفسيولوجي والأداء (TALENT & PERFORMANCE)
--------------------------------------------------------------------------------
• النمط الجيني للألياف العضلية (ACTN3): [التحليل والتفاصيل]
• استجابة التدريب الهوائي والميتوكوندريا (PPARGC1A / ACE): [التحليل]
• التوجيه الميداني التخصصي: [توجيهات التدريب]

--------------------------------------------------------------------------------
[2] المسار الثاني: مؤشر خطر الإصابات والتعافي (INJURY RISK & RECOVERY)
--------------------------------------------------------------------------------
• مؤشر خطورة الأنسجة الضامة والأوتار: [تقييم الأوتار والرباط الصليبي بناء على جينات الكولاجين]
• كفاءة التعافي ومقاومة الإجهاد التأكسدي: [تقييم الالتهاب والتعافي]
• التوجيه الإكلينيكي والوقائي: [بروتوكول الوقاية وإدارة الأحمال]

--------------------------------------------------------------------------------
[3] المسار الثالث: التغذية الجينية الدقيقة (PRECISION NUTRIGENOMICS)
--------------------------------------------------------------------------------
• بروتوكول دعم الأوتار والأنسجة الضامة: [توصيات الكولاجين وفيتامين C والجرعة والتوقيت]
• دعم مضادات الأكسدة ومسارات الديتوكس: [مضادات الأكسدة الموجهة]
• أيض الكافيين ومحسنات الأداء (CYP1A2): [التوقيت والجرعة]

--------------------------------------------------------------------------------
[4] المسار الرابع: توجيهات الأحمال والعودة للعب (WORKLOAD & RETURN-TO-PLAY)
--------------------------------------------------------------------------------
• تعديل أحمال التدريب (Microcycle Modulation): [إدارة ACWR]
• بروتوكول التقوية اللامركزية (Eccentric Loading): [تمارين الأوتار اللامركزية]
• المراقبة الإكلينيكية المستمرة: [المؤشرات الدورية]
================================================================================
"""

    prompt = f"""
{athlete_profile_summary}

RAW TEXT EXTRACTED FROM UPLOADED PDF:
\"\"\"
{patient_raw_text}
\"\"\"

Classify the document. If it is not a sports genomics report, refuse with INVALID_DOCUMENT. If valid, calculate the IRI% and synthesize the full Arabic clinical report.
"""

    logger.info("Executing LLM evaluation (Classification + Clinical Report Synthesis)...")
    start_time = time.time()

    response = llm.invoke([
        SystemMessage(content=system_instruction),
        HumanMessage(content=prompt)
    ])
    duration = round(time.time() - start_time, 2)

    raw_content = response.content
    if isinstance(raw_content, list):
        report_text = "\n".join(b.get("text", str(b)) if isinstance(b, dict) else str(b) for b in raw_content)
    elif isinstance(raw_content, dict):
        report_text = raw_content.get("text", str(raw_content))
    else:
        report_text = str(raw_content)

    # التحقق من رفض المستند
    if "INVALID_DOCUMENT:" in report_text:
        rejection_reason = report_text.split("INVALID_DOCUMENT:")[1].strip()
        logger.warning(f"Document rejected by AI: {rejection_reason}")
        return {
            "success": False,
            "error": rejection_reason
        }

    usage = getattr(response, "usage_metadata", {}) or {}
    logger.info(f"Report generated successfully in {duration}s!")

    return {
        "success": True,
        "report": report_text,
        "metrics": {
            "model": Config.OPENAI_MODEL,
            "latency": duration,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
    }