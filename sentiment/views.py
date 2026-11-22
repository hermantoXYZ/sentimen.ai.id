import os
import re
import json
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import UserQuota, AnalysisLog


def analyze_with_local_sia(text, category):
    """
    Fallback Lexicon-Based Sentiment Analyzer Indonesia (SIA).
    Berjalan lokal di Python tanpa dependensi berat (aman untuk Vercel)
    dan menghasilkan struktur output yang identik dengan Gemini AI.
    """
    pos_words = {
        # Umum & UMKM
        'bagus', 'baik', 'puas', 'memuaskan', 'mantap', 'keren', 'ramah', 'cepat',
        'enak', 'lezat', 'pas', 'murah', 'terjangkau', 'berkualitas', 'rapi', 'aman',
        'suka', 'senang', 'hebat', 'juara', 'terbaik', 'rekomendasi', 'recommended',
        'gokil', 'kece', 'top', 'lancar', 'sukses', 'membantu', 'solusi', 'amanah',
        # Market & Saham
        'naik', 'menguat', 'bullish', 'cuan', 'untung', 'laba', 'tumbuh', 'solid',
        'ekspansi', 'dividen', 'rebound', 'breakout', 'akumulasi', 'positif', 'surplus'
    }
    neg_words = {
        # Umum & UMKM
        'buruk', 'jelek', 'kecewa', 'mengecewakan', 'lama', 'lambat', 'mahal',
        'kasar', 'rusak', 'penyok', 'basi', 'hambar', 'asin', 'pahit', 'kotor',
        'bohong', 'penipu', 'tipu', 'parah', 'ancur', 'hancur', 'susah', 'sulit',
        'ribet', 'gagal', 'error', 'lemot', 'kendor', 'rugi', 'batal', 'komplain',
        # Market & Saham
        'turun', 'melemah', 'bearish', 'anjlok', 'longsor', 'boncos', 'cutloss',
        'koreksi', 'arb', 'suspen', 'defisit', 'utang', 'gagal', 'negatif', 'drop'
    }
    negations = {'tidak', 'tak', 'bukan', 'kurang', 'belum', 'jangan', 'tanpa', 'gak', 'nggak', 'ga'}

    def score_single_line(line):
        tokens = re.findall(r'\b\w+\b', line.lower())
        pos_score = 0
        neg_score = 0
        found_keywords = []

        for i, word in enumerate(tokens):
            has_negation = (i > 0 and tokens[i - 1] in negations) or (i > 1 and tokens[i - 2] in negations)
            if word in pos_words:
                found_keywords.append(word)
                if has_negation:
                    neg_score += 1
                else:
                    pos_score += 1
            elif word in neg_words:
                found_keywords.append(word)
                if has_negation:
                    pos_score += 1
                else:
                    neg_score += 1

        total_hits = pos_score + neg_score
        if pos_score > neg_score:
            sentiment = "Positif"
            confidence = min(92, 60 + (pos_score - neg_score) * 12)
            emotion = "Optimis / Puas" if category != "Market & Saham" else "Bullish / Optimis"
        elif neg_score > pos_score:
            sentiment = "Negatif"
            confidence = min(92, 60 + (neg_score - pos_score) * 12)
            emotion = "Kecewa / Kritis" if category != "Market & Saham" else "Bearish / Waspada"
        else:
            sentiment = "Netral"
            confidence = 65 if total_hits == 0 else 55
            emotion = "Informatif / Netral"

        unique_kw = list(dict.fromkeys(found_keywords))[:5]
        return sentiment, confidence, emotion, unique_kw

    is_batch = (category == 'Batch List Data')
    if is_batch:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        summary = {"positif": 0, "netral": 0, "negatif": 0}
        items = []
        for ln in lines:
            sent, conf, _, _ = score_single_line(ln)
            summary[sent.lower()] += 1
            items.append({
                "text": ln,
                "sentiment": sent,
                "score": conf
            })
        result_obj = {
            "summary": summary,
            "items": items
        }
    else:
        sent, conf, emotion, keywords = score_single_line(text)
        result_obj = {
            "sentiment": sent,
            "confidence": conf,
            "emotion": f"{emotion} [Mode SIA Lokal]",
            "keywords": keywords if keywords else ["(tidak ada kata kunci spesifik)"],
            "summary": f"Dianalisis menggunakan mesin cadangan SIA Lokal karena server AI sedang sibuk. Terdeteksi kecenderungan {sent.lower()} pada kategori {category}."
        }

    # Bungkus dalam struktur kandidat JSON agar kompatibel 100% dengan frontend index.html
    return {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps(result_obj, ensure_ascii=False)
                }]
            }
        }],
        "engine_used": "SIA_LOCAL_FALLBACK"
    }


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error = "Username atau password salah!"

    return render(request, 'sentiment/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def index(request):
    quota, _ = UserQuota.objects.get_or_create(user=request.user)
    quota.check_and_reset()
    return render(request, 'sentiment/index.html', {
        'quota': quota,
    })


@login_required
@require_POST
def analyze_sentiment(request):
    quota, _ = UserQuota.objects.get_or_create(user=request.user)
    quota.check_and_reset()

    # Cek apakah kuota harian user sudah habis
    if quota.used_today >= quota.daily_limit:
        return JsonResponse({
            'error': f'Kuota harian Anda ({quota.daily_limit}x) sudah habis. Silakan coba lagi besok atau hubungi admin.'
        }, status=429)

    try:
        body = json.loads(request.body)
        prompt = body.get('prompt', '').strip()
        system_instruction = body.get('systemInstruction', '')
        category = body.get('category', 'Umum')

        if not prompt:
            return JsonResponse({'error': 'Teks tidak boleh kosong.'}, status=400)

        api_key = os.environ.get('GEMINI_API_KEY')
        data = None
        ai_success = False

        # 1. Coba Gemini AI terlebih dahulu (dengan model utama & cadangan)
        if api_key:
            models_to_try = [
                "gemini-3.8-flash",
                "gemini-3.8-flash-lite",
                "gemini-2.5-flash-lite",
            ]
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }

            for model_name in models_to_try:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                    response = requests.post(url, json=payload, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        data['engine_used'] = model_name
                        ai_success = True
                        break
                except requests.RequestException:
                    continue

        # 2. Jika AI gagal/sibuk/timeout, otomatis gunakan SIA Lokal
        if not ai_success:
            data = analyze_with_local_sia(prompt, category)

        # Potong kuota & catat log
        quota.used_today += 1
        quota.save(update_fields=['used_today'])
        AnalysisLog.objects.create(
            user=request.user,
            category=f"{category} ({data.get('engine_used', 'AI')})",
            input_preview=prompt[:140]
        )

        # Sisipkan info sisa kuota terbaru ke response JSON
        data['remaining_quota'] = quota.remaining
        data['daily_limit'] = quota.daily_limit
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)