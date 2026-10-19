"""
Modul Visualisasi untuk Sentimen.ai.id
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud
from typing import List, Dict, Optional
import io
import base64


# Palet warna konsisten
COLORS = {
    'Positif': '#22c55e',
    'Negatif': '#ef4444',
    'Netral': '#f59e0b',
    'background': '#0f172a',
    'card': '#1e293b',
    'text': '#f1f5f9',
    'accent': '#6366f1',
}

PLOTLY_TEMPLATE = dict(
    layout=go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9', family='Inter, sans-serif'),
        title_font=dict(color='#f1f5f9', size=16),
        legend=dict(
            bgcolor='rgba(30,41,59,0.8)',
            bordercolor='rgba(99,102,241,0.3)',
            borderwidth=1,
        ),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            zerolinecolor='rgba(255,255,255,0.1)',
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            zerolinecolor='rgba(255,255,255,0.1)',
        ),
    )
)


def create_pie_chart(df: pd.DataFrame, column: str = 'label_ensemble', title: str = "Distribusi Sentimen") -> go.Figure:
    """
    Buat pie chart distribusi sentimen.
    
    Args:
        df: DataFrame hasil analisis
        column: Kolom label yang digunakan
        title: Judul chart
    
    Returns:
        Plotly Figure
    """
    if column not in df.columns:
        return go.Figure()

    counts = df[column].value_counts().reset_index()
    counts.columns = ['Sentimen', 'Jumlah']

    color_sequence = [COLORS.get(s, '#94a3b8') for s in counts['Sentimen']]

    fig = go.Figure(data=[
        go.Pie(
            labels=counts['Sentimen'],
            values=counts['Jumlah'],
            hole=0.45,
            marker=dict(
                colors=color_sequence,
                line=dict(color='#0f172a', width=3)
            ),
            textinfo='label+percent',
            textfont=dict(size=13, color='white'),
            hovertemplate='<b>%{label}</b><br>Jumlah: %{value}<br>Persentase: %{percent}<extra></extra>',
            pull=[0.05 if s == counts['Sentimen'].iloc[0] else 0 for s in counts['Sentimen']]
        )
    ])

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=18, color='#f1f5f9')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9', family='Inter, sans-serif'),
        legend=dict(
            bgcolor='rgba(30,41,59,0.8)',
            bordercolor='rgba(99,102,241,0.3)',
            borderwidth=1,
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5
        ),
        margin=dict(t=60, b=80, l=20, r=20),
        height=380,
        annotations=[dict(
            text=f"<b>{counts['Jumlah'].sum()}</b><br>Teks",
            x=0.5, y=0.5,
            font=dict(size=16, color='#f1f5f9'),
            showarrow=False
        )]
    )

    return fig


def create_bar_chart(df: pd.DataFrame, title: str = "Perbandingan Hasil per Model") -> go.Figure:
    """
    Buat bar chart perbandingan jumlah sentimen per model.
    
    Returns:
        Plotly Figure
    """
    model_cols = {
        'VADER': 'label_vader',
        'TextBlob': 'label_textblob',
        'IndoBERT': 'label_indobert',
        'Ensemble': 'label_ensemble'
    }

    rows = []
    for model_name, col in model_cols.items():
        if col in df.columns:
            counts = df[col].value_counts()
            for sentiment, count in counts.items():
                rows.append({'Model': model_name, 'Sentimen': sentiment, 'Jumlah': count})

    if not rows:
        return go.Figure()

    plot_df = pd.DataFrame(rows)

    fig = px.bar(
        plot_df,
        x='Model',
        y='Jumlah',
        color='Sentimen',
        barmode='group',
        color_discrete_map=COLORS,
        text='Jumlah',
    )

    fig.update_traces(
        textposition='outside',
        textfont=dict(size=12, color='white'),
        marker_line_width=0,
        opacity=0.9
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=18, color='#f1f5f9')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9', family='Inter, sans-serif'),
        xaxis=dict(
            title='Model',
            gridcolor='rgba(255,255,255,0.05)',
            title_font=dict(color='#94a3b8'),
            tickfont=dict(color='#f1f5f9')
        ),
        yaxis=dict(
            title='Jumlah Teks',
            gridcolor='rgba(255,255,255,0.05)',
            title_font=dict(color='#94a3b8'),
            tickfont=dict(color='#f1f5f9')
        ),
        legend=dict(
            bgcolor='rgba(30,41,59,0.8)',
            bordercolor='rgba(99,102,241,0.3)',
            borderwidth=1,
            title_text='Sentimen'
        ),
        bargap=0.3,
        bargroupgap=0.1,
        height=400,
        margin=dict(t=60, b=60, l=60, r=20),
    )

    return fig


def create_confidence_chart(df: pd.DataFrame) -> go.Figure:
    """
    Buat chart distribusi confidence score per model.
    
    Returns:
        Plotly Figure (violin/box plot)
    """
    confidence_cols = {
        'VADER': 'confidence_vader',
        'TextBlob': 'confidence_textblob',
        'IndoBERT': 'confidence_indobert',
        'Ensemble': 'confidence_ensemble'
    }

    fig = go.Figure()

    colors_list = ['#6366f1', '#22c55e', '#f59e0b', '#ec4899']

    for i, (model_name, col) in enumerate(confidence_cols.items()):
        if col in df.columns:
            fig.add_trace(go.Box(
                y=df[col],
                name=model_name,
                marker_color=colors_list[i % len(colors_list)],
                boxmean=True,
                hovertemplate=f'<b>{model_name}</b><br>Confidence: %{{y:.3f}}<extra></extra>'
            ))

    fig.update_layout(
        title=dict(text='Distribusi Confidence Score per Model', x=0.5, xanchor='center', font=dict(size=18, color='#f1f5f9')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9', family='Inter, sans-serif'),
        xaxis=dict(title='Model', gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#f1f5f9')),
        yaxis=dict(title='Confidence Score', gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#f1f5f9'), range=[0, 1.1]),
        showlegend=False,
        height=380,
        margin=dict(t=60, b=60, l=60, r=20),
    )

    return fig


def create_wordcloud(texts: List[str], sentiment_label: str = None) -> Optional[plt.Figure]:
    """
    Buat word cloud dari teks.
    
    Args:
        texts: List teks untuk word cloud
        sentiment_label: Label sentimen untuk judul
    
    Returns:
        Matplotlib Figure atau None
    """
    if not texts:
        return None

    # Gabung semua teks
    combined = ' '.join([t for t in texts if isinstance(t, str) and t.strip()])
    if not combined.strip():
        return None

    # Tentukan warna berdasarkan sentimen
    color_map = {
        'Positif': 'Greens',
        'Negatif': 'Reds',
        'Netral': 'YlOrBr',
        None: 'Purples'
    }
    colormap = color_map.get(sentiment_label, 'Purples')

    try:
        wc = WordCloud(
            width=800,
            height=400,
            background_color='#0f172a',
            colormap=colormap,
            max_words=80,
            prefer_horizontal=0.7,
            min_font_size=10,
            max_font_size=100,
            collocations=False,
            relative_scaling=0.5,
        ).generate(combined)

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#0f172a')
        ax.set_facecolor('#0f172a')
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')

        if sentiment_label:
            emoji_map = {'Positif': '😊', 'Negatif': '😢', 'Netral': '😐'}
            emoji = emoji_map.get(sentiment_label, '')
            ax.set_title(
                f'{emoji} Word Cloud — {sentiment_label}',
                color='white',
                fontsize=14,
                pad=10,
                fontweight='bold'
            )

        plt.tight_layout(pad=0)
        return fig

    except Exception as e:
        return None


def create_wordclouds_by_sentiment(df: pd.DataFrame, text_col: str = 'teks_bersih', label_col: str = 'label_ensemble'):
    """
    Buat word cloud untuk setiap kategori sentimen.
    
    Returns:
        Dict dengan sentimen sebagai key dan Figure sebagai value
    """
    figures = {}

    if text_col not in df.columns or label_col not in df.columns:
        return figures

    for sentiment in ['Positif', 'Negatif', 'Netral']:
        filtered = df[df[label_col] == sentiment][text_col].dropna().tolist()
        if filtered:
            fig = create_wordcloud(filtered, sentiment_label=sentiment)
            if fig:
                figures[sentiment] = fig

    return figures


def create_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Buat heatmap kesepakatan antar model.
    
    Returns:
        Plotly Figure
    """
    model_cols = {
        'VADER': 'label_vader',
        'TextBlob': 'label_textblob',
        'IndoBERT': 'label_indobert',
    }

    available_cols = {k: v for k, v in model_cols.items() if v in df.columns}
    if len(available_cols) < 2:
        return go.Figure()

    # Hitung persentase kesepakatan
    models = list(available_cols.keys())
    n = len(models)
    agreement_matrix = np.zeros((n, n))

    for i, m1 in enumerate(models):
        for j, m2 in enumerate(models):
            col1 = available_cols[m1]
            col2 = available_cols[m2]
            if i == j:
                agreement_matrix[i][j] = 1.0
            else:
                agree = (df[col1] == df[col2]).mean()
                agreement_matrix[i][j] = agree

    fig = go.Figure(data=go.Heatmap(
        z=agreement_matrix,
        x=models,
        y=models,
        colorscale='Viridis',
        text=[[f'{v:.1%}' for v in row] for row in agreement_matrix],
        texttemplate='%{text}',
        textfont=dict(size=14, color='white'),
        hoverongaps=False,
        hovertemplate='%{y} ↔ %{x}<br>Kesepakatan: %{text}<extra></extra>',
        zmin=0, zmax=1
    ))

    fig.update_layout(
        title=dict(text='Heatmap Kesepakatan Antar Model', x=0.5, xanchor='center', font=dict(size=18, color='#f1f5f9')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9', family='Inter, sans-serif'),
        xaxis=dict(tickfont=dict(color='#f1f5f9')),
        yaxis=dict(tickfont=dict(color='#f1f5f9')),
        height=350,
        margin=dict(t=60, b=40, l=80, r=20),
    )

    return fig
