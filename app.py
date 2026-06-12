import streamlit as st
import pdfplumber
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re

st.set_page_config(page_title="PDF Summarizer Pro", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📄 PDF Intelligence Engine</div>', unsafe_allow_html=True)


def load_assets():
    model_name = "facebook/bart-large-cnn"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return model, tokenizer

model, tokenizer = load_assets()

def extract_pdf_content(file, max_pages=50):
    full_text = ""
    try:
        with pdfplumber.open(file) as pdf:
            pages_to_read = min(len(pdf.pages), max_pages)
            for i in range(pages_to_read):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    full_text += page_text + "\n"
        return full_text
    except Exception as e:
        return None

def clean_text(text):
    if not text: return ""
    txt = str(text)
    txt = re.sub(r'[{}[\];+=><_()\-:|\\/]', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt)
    return txt.strip()

st.markdown("### 📥 Document Upload")
uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])

if uploaded_file and st.button("Process & Summarize", type="primary", use_container_width=True):
    with st.spinner("Analyzing document structure..."):
        raw_content = extract_pdf_content(uploaded_file)
        
    if raw_content:
        clean = clean_text(raw_content)
        
        st.markdown("### 📄 Extracted Content")
        st.text_area("Document Preview", value=raw_content, height=200)
        
        words = clean.split()
        chunks = [" ".join(words[i:i+600]) for i in range(0, len(words), 600)]
        
        st.markdown("### 📋 Executive Summary")
        summaries = []
        for chunk in chunks:
            if len(chunk.strip()) < 40: continue
            try:
                inputs = tokenizer(chunk, max_length=1024, truncation=True, padding=True, return_tensors="pt")
                with torch.no_grad():
                    ids = model.generate(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"], max_length=140, min_length=40, num_beams=4, no_repeat_ngram_size=3, repetition_penalty=2.5, length_penalty=1.0, early_stopping=True)
                summary = tokenizer.decode(ids[0], skip_special_tokens=True)
                if summary: summaries.append(summary.strip())
            except: continue
            
        if summaries:
            st.markdown("\n\n".join([f"• {s.capitalize()}" for s in summaries]))
        else:
            st.warning("Could not generate summary.")
    else:
        st.error("Failed to extract text from PDF. Please check if the file is readable.")