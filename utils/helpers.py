"""
Helper utilities untuk Sentimen.ai.id
"""

import io
import base64
import pandas as pd
import numpy as np
from typing import List, Optional
import streamlit as st


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Konversi DataFrame ke bytes CSV untuk download"""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding='utf-8-sig')
    return buffer.getvalue().encode('utf-8-sig')


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Konversi DataFrame ke bytes Excel untuk download"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Hasil Analisis')
    return buffer.getvalue()


def parse_text_input(text_input: str) -> List[str]:
    """
    Parse teks input dari textarea (satu teks per baris).
    Hapus baris kosong dan whitespace berlebih.
    """
    if not text_input:
        return []
    lines = text_input.strip().split('\n')
    return [line.strip() for line in lines if line.strip()]


def get_sentiment_badge_html(label: str) -> str:
    """Buat HTML badge untuk label sentimen"""
    colors = {
        'Positif': ('rgba(34,197,94,0.15)', '#22c55e', '😊'),
        'Negatif': ('rgba(239,68,68,0.15)', '#ef4444', '😢'),
        'Netral': ('rgba(245,158,11,0.15)', '#f59e0b', '😐'),
        'N/A': ('rgba(148,163,184,0.15)', '#94a3b8', '❓'),
    }
    bg, color, emoji = colors.get(label, ('rgba(148,163,184,0.15)', '#94a3b8', '❓'))
    return (
        f'<span style="background:{bg}; color:{color}; border:1px solid {color}; '
        f'border-radius:20px; padding:3px 12px; font-size:13px; font-weight:600;">'
        f'{emoji} {label}</span>'
    )


def format_confidence(score: float) -> str:
    """Format confidence score ke persentase"""
    return f"{score * 100:.1f}%"


def create_metric_card_html(title: str, value: str, subtitle: str = "", color: str = "#6366f1") -> str:
    """Buat HTML untuk metric card"""
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(99,102,241,0.05));
        border: 1px solid {color}40;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
    ">
        <p style="color: #94a3b8; font-size: 13px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 1px;">{title}</p>
        <p style="color: {color}; font-size: 28px; font-weight: 700; margin: 0 0 4px 0;">{value}</p>
        {f'<p style="color: #64748b; font-size: 12px; margin: 0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """


def get_sample_texts() -> List[str]:
    """Contoh teks untuk demo aplikasi"""
    return [
        "Produk ini sangat bagus! Saya sangat puas dengan kualitasnya, recommended banget!",
        "Pelayanan sangat buruk, paket terlambat seminggu dan tidak ada kabar sama sekali.",
        "Biasa saja, tidak ada yang spesial dari produk ini. Sesuai ekspektasi.",
        "Mantap jiwa! Harganya murah tapi kualitasnya premium, gak nyesel beli disini.",
        "Kecewa banget, barang datang rusak dan penjual tidak mau bertanggung jawab.",
        "Lumayan lah buat harga segitu, pengiriman cepat walaupun packagingnya kurang rapi.",
        "Luar biasa! Ini adalah produk terbaik yang pernah saya beli. Benar-benar recommended!",
        "Jelek banget, gak sesuai foto di website. Menipu konsumen!",
        "Oke sih, tapi masih ada beberapa kekurangan yang perlu diperbaiki.",
        "Terima kasih sudah memberikan pelayanan yang sangat memuaskan! Customer service ramah."
    ]
