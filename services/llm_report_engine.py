# services/llm_report_engine.py
import json
import os
import time
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("LLMEngine")
KB_PATH = os.path.join(os.path.dirname(__file__), "..", "curated_genomics_data.json")

def get_llm():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY must be set in your .env file.")

    model_name = os.environ.get("OPENAI_MODEL", "google/gemini-2.5-flash")

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        extra_body={"reasoning": {"effort": "medium"}},
        temperature=0.0,
    )

def load_scientific_kb():
    if os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_sports_genomics_report(patient_raw_text: str, athlete_meta: dict = None) -> dict:
    llm = get_llm()
    kb = load_scientific_kb()
    kb_findings = json.dumps(kb.get("papers", [])[:15], ensure_ascii=False)

    meta = athlete_meta or {}
    athlete_profile_summary = f"""
ATHLETE ANTHROPOMETRIC & CLINICAL DOSSIER:
- Full Name: {meta.get('name', 'Elite Athlete')}
- Chronological Age: {meta.get('age', '22')} years
- Sport & Positional Role: {meta.get('sport', 'Football Winger')}
- Stature / Height: {meta.get('height', '180')} cm
- Body Mass / Weight: {meta.get('weight', '75')} kg
- Reported Musculoskeletal History: {meta.get('injuries', 'No prior major surgeries; recurring tendon tightness')}
"""

    system_instruction = f"""
You are a Senior Precision Sports & Clinical Genomicist and Evidence-Based Medicine (EBM) Performance Director.
Cross-reference the athlete's genes with the PubMed knowledge base AND synthesize their specific anthropometrics (stature, mass, velocity profile, injury history).

CURATED PUBMED EVIDENCE GROUND TRUTH:
{kb_findings}

CLINICAL SYNTHESIS GUIDELINES:
1. Integrate Anthropometrics with Genetics: Connect body mass, height, and sport mechanics with tendon/ligament predispositions (e.g., higher mass/velocity on COL1A1/COL5A1 variants exponentially increases mechanical strain on the ACL and Achilles tendon).
2. Factor in Chronological Age & History: Adjust recovery kinetics (SOD2, IL6) and tendon microcycle loading according to age and injury history.
3. Keep the output strictly in the standardized Arabic clinical layout below.

REQUIRED OUTPUT TEMPLATE:
================================================================================
               PRECISION SPORTS & CLINICAL GENOMICS PLATFORM
               مؤشر الجاهزية الإكلينيكية والوقائية للرياضيين (EBM-Driven)
================================================================================
• اسم الرياضي: {meta.get('name', 'كابتن / أحمد خالد')}               • العمر: {meta.get('age', '22')} سنة ({meta.get('height', '180')} سم / {meta.get('weight', '75')} كجم)
• الرياضة: {meta.get('sport', 'كرة قدم')}       • المعرف الإكلينيكي: SG-2026-PRO-99
• تاريخ التقارير الجينية: نوفمبر 2026         • مؤشر خطر الإصابة العام (IRI): [e.g. 74% - مرتفع ⚠️]
--------------------------------------------------------------------------------

[1] المسار الأول: البروفايل الفسيولوجي والأداء (TALENT & PERFORMANCE)
--------------------------------------------------------------------------------
• النمط الجيني للألياف العضلية (ACTN3 - rs1815739): [Genotype & Allele] -> [Muscle fiber speed/power vs endurance profile]
• استجابة التدريب الهوائي (PPARGC1A / ACE): [Mitochondrial biogenesis & aerobic adaptation capacity]
• التوجيه الميداني: [Practical coaching directives tailored to their body mass and sport]

--------------------------------------------------------------------------------
[2] المسار الثاني: مؤشر خطر الإصابات والتعافي (INJURY RISK & RECOVERY)
--------------------------------------------------------------------------------
• مؤشر خطورة الأنسجة الضامة والأوتار (Injury Predisposition): [مرتفع / متوسط / منخفض]
  - جين COL1A1 (rs1800012) و COL5A1 (rs12722): [Fibrillogenesis, tendon elasticity, and impact of body mass/stature on ACL/Achilles load]
• كفاءة التعافي ومقاومة الإجهاد التأكسدي (SOD2 / IL6): [Inflammatory cascade resolution & oxidative clearance]
• التوجيه الإكلينيكي والوقائي: [Directives considering previous injuries]

--------------------------------------------------------------------------------
[3] المسار الثالث: التغذية الجينية الدقيقة (PRECISION NUTRIGENOMICS)
--------------------------------------------------------------------------------
• بروتوكول دعم الأوتار والأنسجة الضامة: [Collagen + Vitamin C dosage & timing protocol adjusted for body weight]
• دعم مضادات الأكسدة ومسارات التخلص من السموم (Detoxification - GSTM1 / MTHFR): [Antioxidant & methylation support]
• أيض الكافيين ومحسنات الأداء (CYP1A2): [Caffeine timing & mg/kg dose]

--------------------------------------------------------------------------------
[4] المسار الرابع: توجيهات الأحمال والعودة للعب (WORKLOAD & RETURN-TO-PLAY)
--------------------------------------------------------------------------------
• تعديل أحمال التدريب (Microcycle Modulation): [ACWR workload ratio]
• بروتوكول التقوية اللامركزية (Eccentric Loading): [Eccentric tendon loading protocols]
• المراقبة الإكلينيكية المستمرة: [Key clinical biomarkers to track]
================================================================================
"""

    prompt = f"""
{athlete_profile_summary}

RAW GENETIC & LABORATORY DATA EXTRACTED FROM PDF:
\"\"\"
{patient_raw_text}
\"\"\"

Synthesize the final Precision Sports Genomics Report in Arabic adhering strictly to the template.
"""

    start_time = time.time()
    response = llm.invoke([
        SystemMessage(content=system_instruction),
        HumanMessage(content=prompt)
    ])
    duration = round(time.time() - start_time, 2)

    # حساب التوكينز والتكلفة (للسيرفر فقط)
    usage = getattr(response, "usage_metadata", {}) or {}
    prompt_tokens = usage.get("input_tokens", 0)
    completion_tokens = usage.get("output_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

    cost_usd = ((prompt_tokens / 1_000_000) * 0.075) + ((completion_tokens / 1_000_000) * 0.30)

    # طباعة التوكينز والتكلفة في الكونسول للمطور فقط
    logger.info(
        "\n" + "="*60 + "\n"
        f" [INTERNAL SERVER LOG - TOKEN & COST METRICS]\n"
        f"  • Athlete:       {meta.get('name', 'N/A')} ({meta.get('sport', 'N/A')})\n"
        f"  • Latency:       {duration}s\n"
        f"  • Input Tokens:  {prompt_tokens:,}\n"
        f"  • Output Tokens: {completion_tokens:,}\n"
        f"  • Total Tokens:  {total_tokens:,}\n"
        f"  • Cost (USD):    ${cost_usd:.6f} (~{cost_usd * 50:.4f} EGP)\n"
        + "="*60
    )

    return {
        "report": response.content,
        "metrics": {
            "model": llm.model_name,
            "latency": duration,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": cost_usd
        }
    }