# test_pipeline.py
import os
from services.llm_report_engine import generate_sports_genomics_report

# عينة بيانات جينية كما تظهر مستخرجة من ملف PDF معملي
sample_patient_text = """
PATIENT & LAB METADATA:
Athlete Name: كابتن/ أحمد خالد
Age: 22
Sport: Football (Winger / High-Velocity Acceleration)
Clinical ID: SG-2026-PRO-99
Lab Test Date: November 2026

GENETIC PROFILE FINDINGS:
- ACTN3 (rs1815739): Genotype CC (Arg577Arg / Fast-twitch alpha-actinin-3 present)
- PPARGC1A (rs8192678): Genotype Gly482Ser (Moderate-to-high aerobic mitochondrial biogenesis)
- ACE (I/D): I/D Heterozygous (Mixed metabolic endurance & power potential)
- COL1A1 (rs1800012): Genotype GT (Sp1 binding site mutation - reduced collagen fibril regulation)
- COL5A1 (rs12722): Genotype TT (High risk allele for Achilles tendon & cruciate ligament strain)
- SOD2 (rs4880): Genotype Ala16Val (Val/Val - lower mitochondrial superoxide dismutase defense)
- IL6 (rs1800795): Genotype GG (-174 G allele - elevated post-exercise inflammatory response)
- CYP1A2 (rs762551): Genotype AC (*1F/*1A - intermediate to slow caffeine metabolizer)
- GSTM1: Null genotype (Decreased Phase II enzymatic detoxification efficiency)
"""

print("=================================================================")
print("  Running Sports Genomics AI Pipeline with Gemini 3.5 Flash...  ")
print("=================================================================\n")

report = generate_sports_genomics_report(sample_patient_text)

print(report)