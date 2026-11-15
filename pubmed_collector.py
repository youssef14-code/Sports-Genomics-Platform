import os
import time
import json
from Bio import Entrez

# ==========================================
# 1. إعدادات NCBI
# ==========================================
# استبدل بالبريد الإلكتروني الخاص بك (شرط أساسي من NCBI)
Entrez.email = "yh2767058@gmail.com"
Entrez.tool = "precision_sports_genomics"

# في حال توفر API Key يتم قراءته من الـ Environment Variables
api_key = os.getenv("NCBI_API_KEY")
if api_key:
    Entrez.api_key = api_key

# معدل الانتظار بين الطلبات لتجنب الحظر:
# 0.35 ثانية بدون Key (أقل من 3 طلبات/ثانية)
# 0.11 ثانية مع Key (أقل من 10 طلبات/ثانية)
REQUEST_DELAY = 0.11 if api_key else 0.35

# ==========================================
# 2. استعلامات البحث (Search Queries)
# ==========================================
# Sports Genomics Query (دقة أعلى: الجينات شرط أساسي)
SPORTS_GENOMICS_QUERY = """
(
    gene[Title/Abstract] 
    OR genetic*[Title/Abstract] 
    OR genomic*[Title/Abstract] 
    OR polymorphism*[Title/Abstract] 
    OR "single nucleotide polymorphism"[Title/Abstract] 
    OR variant*[Title/Abstract] 
    OR allele*[Title/Abstract]
)
AND
(
    "athletic performance"[Title/Abstract] 
    OR "sports performance"[Title/Abstract] 
    OR "exercise performance"[Title/Abstract] 
    OR "muscle damage"[Title/Abstract] 
    OR "tendon injury"[Title/Abstract] 
    OR "ligament injury"[Title/Abstract] 
    OR "exercise recovery"[Title/Abstract]
)
"""

# Nutrigenomics Query (دقة أعلى: التفاعل بين الغذاء والجينات)
NUTRIGENOMICS_QUERY = """
(
    nutrigenom*[Title/Abstract] 
    OR nutrigenet*[Title/Abstract] 
    OR "gene-diet interaction"[Title/Abstract] 
    OR "gene-nutrient interaction"[Title/Abstract]
    OR (
        (gene[Title/Abstract] OR genetic*[Title/Abstract] OR polymorphism*[Title/Abstract])
        AND
        (nutrition[Title/Abstract] OR diet[Title/Abstract] OR supplement*[Title/Abstract] OR micronutrient*[Title/Abstract])
    )
)
AND
(
    athlete*[Title/Abstract] 
    OR sport*[Title/Abstract] 
    OR exercise[Title/Abstract] 
    OR recovery[Title/Abstract] 
    OR "muscle metabolism"[Title/Abstract]
)
"""

QUERIES = {
    "sports_genomics": SPORTS_GENOMICS_QUERY,
    "nutrigenomics": NUTRIGENOMICS_QUERY
}

# ==========================================
# 3. دوال السحب والمعالجة
# ==========================================
def search_pubmed(query: str, max_results: int = 100) -> list[str]:
    """البحث في PubMed واسترجاع قائمة بأرقام PMID"""
    time.sleep(REQUEST_DELAY)
    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=max_results,
        sort="relevance"
    )
    results = Entrez.read(handle)
    handle.close()
    return results.get("IdList", [])

def parse_abstract(article_data: dict) -> list[dict]:
    """استخراج نص الـ Abstract سواء كان مقسماً أو نصاً واحداً"""
    abstract_sections = []
    article = article_data.get("Article", {})
    abstract = article.get("Abstract", {})
    abstract_texts = abstract.get("AbstractText", [])

    if not abstract_texts:
        return abstract_sections

    for item in abstract_texts:
        text = str(item)
        # التحقق مما إذا كان القسم يحتوي على Label (مثل BACKGROUND أو METHODS)
        label = "UNLABELLED"
        if hasattr(item, "attributes") and item.attributes:
            label = item.attributes.get("Label", "UNLABELLED")
        
        abstract_sections.append({
            "section": label,
            "text": text.strip()
        })
    return abstract_sections

def extract_doi(pub_data: dict) -> str | None:
    """استخراج DOI للدراسة إن وجد"""
    article_ids = pub_data.get("ArticleIdList", [])
    for aid in article_ids:
        if getattr(aid, "attributes", {}).get("IdType") == "doi":
            return str(aid)
    return None

def fetch_details_batch(pmid_list: list[str], batch_size: int = 50) -> list[dict]:
    """سحب تفاصيل الدراسات على دفعات لتسريع العملية"""
    parsed_articles = []
    
    for i in range(0, len(pmid_list), batch_size):
        chunk = pmid_list[i : i + batch_size]
        print(f"--> سحب بيانات الدفعة من {i + 1} إلى {min(i + batch_size, len(pmid_list))}...")
        
        time.sleep(REQUEST_DELAY)
        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(chunk),
            rettype="xml",
            retmode="xml"
        )
        records = Entrez.read(handle)
        handle.close()

        for article_record in records.get("PubmedArticle", []):
            medline = article_record.get("MedlineCitation", {})
            article = medline.get("Article", {})
            pub_data = article_record.get("PubmedData", {})

            pmid = str(medline.get("PMID", ""))
            title = article.get("ArticleTitle", "").strip()
            journal = article.get("Journal", {}).get("Title", "")
            
            # تاريخ النشر
            pub_date = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            pub_year = pub_date.get("Year", "Unknown")

            # أنواع المنشورات
            pub_types = [str(pt) for pt in article.get("PublicationTypeList", [])]
            
            # الـ Abstract والـ DOI
            abstract = parse_abstract(medline)
            doi = extract_doi(pub_data)

            parsed_articles.append({
                "pmid": pmid,
                "doi": doi,
                "title": title,
                "journal": journal,
                "year": pub_year,
                "publication_types": pub_types,
                "abstract": abstract,
                "source": "PubMed"
            })

    return parsed_articles

# ==========================================
# 4. نقطة الانطلاق الرئيسية (Pipeline Execution)
# ==========================================
def main():
    all_pmids_map = {}  # {pmid: [categories]}

    print("=== المرحلة 1: البحث وتجميع الـ PMIDs ===")
    for category, query in QUERIES.items():
        print(f"جاري البحث عن تصنيف: '{category}' (أول 100 نتيجة)...")
        pmids = search_pubmed(query, max_results=100)
        print(f"تم العثور على {len(pmids)} دراسة في {category}.")
        
        for pmid in pmids:
            if pmid not in all_pmids_map:
                all_pmids_map[pmid] = []
            all_pmids_map[pmid].append(category)

    unique_pmids = list(all_pmids_map.keys())
    print(f"\nإجمالي الدراسات الفريدة (بدون تكرار): {len(unique_pmids)}")

    print("\n=== المرحلة 2: سحب الـ Metadata والـ Abstracts ===")
    articles = fetch_details_batch(unique_pmids, batch_size=50)

    # إضافة وسوم التصنيف لكل دراسة
    for art in articles:
        art["tags"] = all_pmids_map.get(art["pmid"], [])

    # حفظ النتائج
    output_filename = "pubmed_sample.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\nتم الانتهاء بنجاح! تم حفظ {len(articles)} دراسة في ملف '{output_filename}'.")

if __name__ == "__main__":
    main()