import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30000)
)

MODEL_NAME = "gemini-3.5-flash"

def extract_insights_from_paper(paper: dict, max_retries: int = 3) -> dict:
    abstract_text = " ".join([sec.get("text", "") for sec in paper.get("abstract", [])])
    pmid = paper.get("pmid", "")
    
    if not abstract_text.strip():
        return {
            "pmid": pmid,
            "title": paper.get("title", ""),
            "has_actionable_genomics": False,
            "findings": []
        }

    prompt = f"""
    You are an expert sports genomics & nutrigenomics researcher.
    Analyze this research study and extract structured findings.
    
    Return ONLY a valid JSON object matching this structure:
    {{
      "pmid": "{pmid}",
      "title": "{paper.get('title', '').replace('"', '')}",
      "has_actionable_genomics": true,
      "findings": [
        {{
          "gene_symbol": "Gene name (e.g., ACTN3, ACE, CYP1A2, COL5A1)",
          "variant_rsid": "Variant or rsID (e.g., R577X, rs1815739, rs762551) or null",
          "category": "Power / Endurance / Injury_Risk / Recovery / Nutrition / Metabolism",
          "nutrition_interaction": "Nutrient, supplement or food interaction if any, else null",
          "summary": "1-2 sentence concise scientific finding",
          "recommendation": "Practical training or dietary action recommendation"
        }}
      ]
    }}

    If no specific genes or genetic variants are discussed, set "has_actionable_genomics": false and "findings": [].

    Title: {paper.get('title')}
    Abstract: {abstract_text}
    """

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            return json.loads(response.text)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                return {"pmid": pmid, "title": paper.get("title", ""), "error": str(e)}

def main():
    input_file = "pubmed_sample.json"
    output_file = "extracted_genomics_knowledge.json"

    with open(input_file, "r", encoding="utf-8") as f:
        papers = json.load(f)

    total = len(papers)
    print(f"🚀 بدء استخراج البيانات من {total} دراسة باستخدام [{MODEL_NAME}]...")
    extracted_data = []

    for idx, paper in enumerate(papers):
        pmid = paper.get("pmid")
        title_snippet = paper.get("title", "")[:45]
        print(f"[{idx + 1}/{total}] دراسة PMID: {pmid} - {title_snippet}...", flush=True)
        
        result = extract_insights_from_paper(paper)
        extracted_data.append(result)
        
        # حفظ فوري للتقدم كل 5 دراسات
        if (idx + 1) % 5 == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            print(f"  💾 [تم حفظ تقدم {idx + 1}/{total} دراسة بنجاح]", flush=True)

        time.sleep(0.5)  # نصف ثانية راحة بين الطلبات لضمان استقرار الـ Rate Limit

    # الحفظ النهائي
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 تم الانتهاء بنجاح تام! تم حفظ جميع النتائج في: {output_file}")

if __name__ == "__main__":
    main()