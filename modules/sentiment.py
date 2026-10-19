"""
Modul Analisis Sentimen untuk Sentimen.ai.id
Mendukung IndoBERT, VADER, TextBlob, dan Ensemble
"""

import os
import re
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import streamlit as st

# ─────────────────────────────────────────────────────────────────
# VADER
# ─────────────────────────────────────────────────────────────────
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────
# TextBlob
# ─────────────────────────────────────────────────────────────────
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────
# IndoBERT (Hugging Face Transformers)
# ─────────────────────────────────────────────────────────────────
INDOBERT_AVAILABLE = False
indobert_pipeline = None

def load_indobert():
    """Load model IndoBERT dari Hugging Face"""
    global INDOBERT_AVAILABLE, indobert_pipeline
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
        
        # Model sentimen IndoBERT yang sudah di-fine-tune
        model_name = "mdhugol/indonesia-bert-sentiment-classification"
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        indobert_pipeline = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            return_all_scores=True
        )
        INDOBERT_AVAILABLE = True
        return True
    except Exception as e:
        INDOBERT_AVAILABLE = False
        return False


# ─────────────────────────────────────────────────────────────────
# LABEL MAPPING
# ─────────────────────────────────────────────────────────────────

# Mapping label IndoBERT ke sentimen standar
INDOBERT_LABEL_MAP = {
    'positive': 'Positif',
    'negative': 'Negatif', 
    'neutral': 'Netral',
    'LABEL_0': 'Negatif',
    'LABEL_1': 'Netral',
    'LABEL_2': 'Positif',
}

SENTIMENT_COLORS = {
    'Positif': '#22c55e',
    'Negatif': '#ef4444',
    'Netral': '#f59e0b',
}

SENTIMENT_EMOJIS = {
    'Positif': '😊',
    'Negatif': '😢',
    'Netral': '😐',
}


# ─────────────────────────────────────────────────────────────────
# FUNGSI ANALISIS SENTIMEN
# ─────────────────────────────────────────────────────────────────

def analyze_vader(text: str) -> Dict:
    """
    Analisis sentimen menggunakan VADER.
    
    Returns:
        Dict dengan label, skor, dan confidence
    """
    if not VADER_AVAILABLE or not text:
        return {
            'label': 'Netral',
            'skor_positif': 0.0,
            'skor_negatif': 0.0,
            'skor_netral': 1.0,
            'compound': 0.0,
            'confidence': 0.0,
            'model': 'VADER',
            'tersedia': VADER_AVAILABLE
        }

    try:
        scores = vader_analyzer.polarity_scores(text)
        compound = scores['compound']

        if compound >= 0.05:
            label = 'Positif'
            confidence = scores['pos']
        elif compound <= -0.05:
            label = 'Negatif'
            confidence = scores['neg']
        else:
            label = 'Netral'
            confidence = scores['neu']

        return {
            'label': label,
            'skor_positif': round(scores['pos'], 4),
            'skor_negatif': round(scores['neg'], 4),
            'skor_netral': round(scores['neu'], 4),
            'compound': round(compound, 4),
            'confidence': round(abs(compound), 4),
            'model': 'VADER',
            'tersedia': True
        }
    except Exception as e:
        return {
            'label': 'Netral',
            'skor_positif': 0.0,
            'skor_negatif': 0.0,
            'skor_netral': 1.0,
            'compound': 0.0,
            'confidence': 0.0,
            'model': 'VADER',
            'tersedia': False,
            'error': str(e)
        }


def analyze_textblob(text: str) -> Dict:
    """
    Analisis sentimen menggunakan TextBlob.
    
    Returns:
        Dict dengan label, polaritas, dan subjektivitas
    """
    if not TEXTBLOB_AVAILABLE or not text:
        return {
            'label': 'Netral',
            'polaritas': 0.0,
            'subjektivitas': 0.0,
            'confidence': 0.0,
            'model': 'TextBlob',
            'tersedia': TEXTBLOB_AVAILABLE
        }

    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        if polarity > 0.05:
            label = 'Positif'
        elif polarity < -0.05:
            label = 'Negatif'
        else:
            label = 'Netral'

        return {
            'label': label,
            'polaritas': round(polarity, 4),
            'subjektivitas': round(subjectivity, 4),
            'skor_positif': round(max(polarity, 0), 4),
            'skor_negatif': round(abs(min(polarity, 0)), 4),
            'skor_netral': round(1 - abs(polarity), 4),
            'confidence': round(abs(polarity), 4),
            'model': 'TextBlob',
            'tersedia': True
        }
    except Exception as e:
        return {
            'label': 'Netral',
            'polaritas': 0.0,
            'subjektivitas': 0.0,
            'confidence': 0.0,
            'model': 'TextBlob',
            'tersedia': False,
            'error': str(e)
        }


def analyze_indobert(text: str) -> Dict:
    """
    Analisis sentimen menggunakan IndoBERT.
    
    Returns:
        Dict dengan label, skor per kelas, dan confidence
    """
    if not INDOBERT_AVAILABLE or indobert_pipeline is None or not text:
        return {
            'label': 'Netral',
            'skor_positif': 0.0,
            'skor_negatif': 0.0,
            'skor_netral': 1.0,
            'confidence': 0.0,
            'model': 'IndoBERT',
            'tersedia': INDOBERT_AVAILABLE
        }

    try:
        # Truncate teks jika terlalu panjang untuk BERT (max 512 token)
        if len(text) > 512:
            text = text[:512]

        results = indobert_pipeline(text)[0]

        scores = {}
        for item in results:
            label_raw = item['label'].lower()
            # Map label ke format standar
            if 'pos' in label_raw or label_raw == 'label_2':
                scores['Positif'] = item['score']
            elif 'neg' in label_raw or label_raw == 'label_0':
                scores['Negatif'] = item['score']
            elif 'neu' in label_raw or label_raw == 'label_1':
                scores['Netral'] = item['score']

        # Fallback jika mapping gagal
        if not scores:
            scores = {'Positif': 0.0, 'Negatif': 0.0, 'Netral': 1.0}

        best_label = max(scores, key=scores.get)
        best_score = scores[best_label]

        return {
            'label': best_label,
            'skor_positif': round(scores.get('Positif', 0.0), 4),
            'skor_negatif': round(scores.get('Negatif', 0.0), 4),
            'skor_netral': round(scores.get('Netral', 0.0), 4),
            'confidence': round(best_score, 4),
            'model': 'IndoBERT',
            'tersedia': True
        }
    except Exception as e:
        return {
            'label': 'Netral',
            'skor_positif': 0.0,
            'skor_negatif': 0.0,
            'skor_netral': 1.0,
            'confidence': 0.0,
            'model': 'IndoBERT',
            'tersedia': False,
            'error': str(e)
        }


def analyze_ensemble(
    vader_result: Dict,
    textblob_result: Dict,
    indobert_result: Dict,
    weights: Optional[Dict] = None
) -> Dict:
    """
    Ensemble analisis dari VADER, TextBlob, dan IndoBERT.
    Menggunakan weighted voting berdasarkan confidence masing-masing model.
    
    Args:
        weights: Dict bobot per model {'VADER': 0.2, 'TextBlob': 0.2, 'IndoBERT': 0.6}
    """
    if weights is None:
        # IndoBERT mendapat bobot lebih tinggi untuk Bahasa Indonesia
        indobert_w = 0.6 if indobert_result.get('tersedia') else 0
        vader_w = 0.25 if vader_result.get('tersedia') else 0
        textblob_w = 0.15 if textblob_result.get('tersedia') else 0

        # Normalisasi bobot
        total_w = indobert_w + vader_w + textblob_w
        if total_w == 0:
            weights = {'VADER': 0.33, 'TextBlob': 0.33, 'IndoBERT': 0.34}
        else:
            weights = {
                'VADER': vader_w / total_w,
                'TextBlob': textblob_w / total_w,
                'IndoBERT': indobert_w / total_w
            }

    # Kumpulkan skor per sentimen
    score_positif = (
        vader_result.get('skor_positif', 0) * weights['VADER'] +
        textblob_result.get('skor_positif', 0) * weights['TextBlob'] +
        indobert_result.get('skor_positif', 0) * weights['IndoBERT']
    )
    score_negatif = (
        vader_result.get('skor_negatif', 0) * weights['VADER'] +
        textblob_result.get('skor_negatif', 0) * weights['TextBlob'] +
        indobert_result.get('skor_negatif', 0) * weights['IndoBERT']
    )
    score_netral = (
        vader_result.get('skor_netral', 1) * weights['VADER'] +
        textblob_result.get('skor_netral', 1) * weights['TextBlob'] +
        indobert_result.get('skor_netral', 1) * weights['IndoBERT']
    )

    # Normalisasi
    total = score_positif + score_negatif + score_netral
    if total > 0:
        score_positif /= total
        score_negatif /= total
        score_netral /= total

    # Tentukan label berdasarkan skor tertinggi
    scores = {
        'Positif': score_positif,
        'Negatif': score_negatif,
        'Netral': score_netral
    }
    best_label = max(scores, key=scores.get)
    confidence = scores[best_label]

    return {
        'label': best_label,
        'skor_positif': round(score_positif, 4),
        'skor_negatif': round(score_negatif, 4),
        'skor_netral': round(score_netral, 4),
        'confidence': round(confidence, 4),
        'model': 'Ensemble',
        'bobot': weights
    }


def analyze_text_full(
    text: str,
    use_vader: bool = True,
    use_textblob: bool = True,
    use_indobert: bool = True
) -> Dict:
    """
    Analisis sentimen lengkap menggunakan semua model yang dipilih.
    
    Returns:
        Dict berisi hasil dari semua model dan ensemble
    """
    results = {
        'teks': text,
        'vader': {},
        'textblob': {},
        'indobert': {},
        'ensemble': {}
    }

    if use_vader:
        results['vader'] = analyze_vader(text)

    if use_textblob:
        results['textblob'] = analyze_textblob(text)

    if use_indobert:
        results['indobert'] = analyze_indobert(text)

    # Hitung ensemble
    results['ensemble'] = analyze_ensemble(
        results.get('vader', {}),
        results.get('textblob', {}),
        results.get('indobert', {})
    )

    return results


def analyze_batch(
    texts: List[str],
    use_vader: bool = True,
    use_textblob: bool = True,
    use_indobert: bool = True,
    progress_callback=None
) -> pd.DataFrame:
    """
    Analisis sentimen untuk banyak teks.
    
    Returns:
        DataFrame dengan hasil analisis lengkap
    """
    rows = []
    total = len(texts)

    for i, text in enumerate(texts):
        if progress_callback:
            progress_callback(i / total, f"Menganalisis teks {i+1}/{total}...")

        if not text or not isinstance(text, str) or len(text.strip()) < 2:
            rows.append({
                'teks': text,
                'label_vader': 'N/A',
                'label_textblob': 'N/A',
                'label_indobert': 'N/A',
                'label_ensemble': 'N/A',
                'confidence_vader': 0,
                'confidence_textblob': 0,
                'confidence_indobert': 0,
                'confidence_ensemble': 0,
            })
            continue

        full = analyze_text_full(text, use_vader, use_textblob, use_indobert)

        rows.append({
            'teks': text,
            'label_vader': full['vader'].get('label', 'N/A'),
            'compound_vader': full['vader'].get('compound', 0),
            'confidence_vader': full['vader'].get('confidence', 0),
            'label_textblob': full['textblob'].get('label', 'N/A'),
            'polaritas_textblob': full['textblob'].get('polaritas', 0),
            'subjektivitas_textblob': full['textblob'].get('subjektivitas', 0),
            'confidence_textblob': full['textblob'].get('confidence', 0),
            'label_indobert': full['indobert'].get('label', 'N/A'),
            'confidence_indobert': full['indobert'].get('confidence', 0),
            'label_ensemble': full['ensemble'].get('label', 'N/A'),
            'skor_positif_ensemble': full['ensemble'].get('skor_positif', 0),
            'skor_negatif_ensemble': full['ensemble'].get('skor_negatif', 0),
            'skor_netral_ensemble': full['ensemble'].get('skor_netral', 0),
            'confidence_ensemble': full['ensemble'].get('confidence', 0),
        })

    if progress_callback:
        progress_callback(1.0, "Analisis selesai!")

    return pd.DataFrame(rows)
