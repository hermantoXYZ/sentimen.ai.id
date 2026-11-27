import io
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from sqlalchemy import func
from dotenv import load_dotenv

from config import Config
from model.models import db, SocialPost
from layanan.nlp_service import analyze_sentiment, extract_top_keywords
from layanan.youtube_service import analyze_youtube_url
from layanan.threads_service import analyze_threads_url
from layanan.tiktok_service import analyze_tiktok_url
from layanan.twitter_service import analyze_twitter_url
from layanan.instagram_service import analyze_instagram_url, analyze_instagram_manual

load_dotenv()

app = Flask(
    __name__,
    template_folder='template',
    static_folder='statis',
    static_url_path='/statis'
)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    db.create_all()

# 1. DASHBOARD
@app.route('/')
@app.route('/dashboard')
def dashboard():
    total_posts = SocialPost.query.count()
    pos_count = SocialPost.query.filter_by(sentiment='positive').count()
    neg_count = SocialPost.query.filter_by(sentiment='negative').count()
    neu_count = SocialPost.query.filter_by(sentiment='neutral').count()

    # Skor Sentimen 0 - 100
    if total_posts > 0:
        raw_score = int(round(((pos_count - neg_count) / total_posts) * 100))
        sentiment_score = max(0, min(100, raw_score if raw_score > 0 else int((pos_count / total_posts) * 100)))
    else:
        sentiment_score = 0

    platform_counts = dict(
        db.session.query(SocialPost.platform, func.count(SocialPost.id))
        .group_by(SocialPost.platform).all()
    )
    recent_posts = SocialPost.query.order_by(SocialPost.created_at.desc()).limit(50).all()

    return render_template(
        'dashboard.html',
        sentiment_score=sentiment_score,
        total_posts=total_posts,
        pos_count=pos_count,
        neg_count=neg_count,
        neu_count=neu_count,
        platform_counts=platform_counts,
        recent_posts=recent_posts
    )


@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    text = request.form.get('text', '').strip()
    platform = request.form.get('platform', 'text').lower().strip() or 'text'
    username = request.form.get('username', '@anonim').strip() or '@anonim'
    engine = request.form.get('engine', 'textblob')

    if not text:
        flash('Harap masukkan teks yang ingin dianalisis.', 'danger')
        return redirect(url_for('dashboard'))

    res = analyze_sentiment(text, engine=engine)
    _upsert_social_post(
        platform=platform,
        username=username if username.startswith('@') else f'@{username}',
        content=text,
        sentiment=res['sentiment'],
        confidence=res['confidence'],
        model_used=engine,
        likes=0,
        shares=0,
        created_at=datetime.utcnow()
    )
    db.session.commit()
    flash(
        f"Hasil Analisis ({engine.upper()}): {res['sentiment'].upper()} ({res['confidence']}%) — Data berhasil ditambahkan!",
        'success'
    )
    return redirect(url_for('dashboard'))

def _upsert_social_post(platform: str, username: str, content: str, sentiment: str,
                        confidence: int, model_used: str, likes: int, shares: int, created_at: datetime):
    existing = SocialPost.query.filter_by(
        platform=platform,
        username=username,
        content=content
    ).first()
    if existing:
        existing.sentiment = sentiment
        existing.confidence = confidence
        existing.model_used = model_used
        existing.likes = likes
        existing.shares = shares
        existing.created_at = created_at
    else:
        db.session.add(SocialPost(
            platform=platform,
            username=username,
            content=content,
            sentiment=sentiment,
            confidence=confidence,
            model_used=model_used,
            likes=likes,
            shares=shares,
            created_at=created_at
        ))


# 2. UPLOAD DATA CSV
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        engine = request.form.get('engine', 'textblob')

        if not file or not file.filename.endswith('.csv'):
            flash('Harap pilih file CSV yang valid.', 'danger')
            return redirect(request.url)

        import pandas as pd
        df = pd.read_csv(file)
        required = {'platform', 'username', 'text'}
        if not required.issubset(df.columns):
            flash(f'Kolom wajib CSV: {", ".join(required)}', 'danger')
            return redirect(request.url)

        for _, row in df.iterrows():
            content = str(row['text']).strip()
            res = analyze_sentiment(content, engine=engine)
            dt = (
                pd.to_datetime(row['created_at'])
                if 'created_at' in df.columns and pd.notna(row['created_at'])
                else datetime.utcnow()
            )
            _upsert_social_post(
                platform=str(row['platform']).lower().strip(),
                username=str(row['username']).strip(),
                content=content,
                sentiment=res['sentiment'],
                confidence=res['confidence'],
                model_used=engine,
                likes=int(row['likes']) if 'likes' in df.columns and pd.notna(row['likes']) else 0,
                shares=int(row['shares']) if 'shares' in df.columns and pd.notna(row['shares']) else 0,
                created_at=dt
            )

        db.session.commit()
        flash(f'Berhasil menganalisis {len(df)} data menggunakan {engine.upper()}!', 'success')
        return redirect(url_for('analysis'))

    return render_template('upload.html')

@app.route('/download-sample-csv')
def download_sample_csv():
    sample = (
        "platform,username,text,created_at,likes,shares\n"
        "tokopedia,@buyer_rina,Produk UMKM lokal ini kualitasnya luar biasa bagus dan packaging rapi!,2026-11-20 10:30:00,320,78\n"
        "shopee,@konsumen_budi,Penipu! Barang tidak sampai uang sudah ditransfer. Sangat kecewa.,2026-11-21 11:15:00,5,2\n"
        "tiktok,@reviewer_ani,Review produk skincare UMKM Indonesia — biasa saja belum terlalu terasa manfaatnya,2026-11-22 12:00:00,890,120\n"
        "instagram,@pelanggan_doni,Seller sangat responsif pengiriman cepat recommended banget buat belanja produk lokal,2026-11-23 09:00:00,210,45\n"
        "twitter,@umkm_watcher,Digitalisasi UMKM Indonesia terus tumbuh pesat omzet meningkat signifikan,2026-11-24 14:00:00,150,60\n"
    )
    return send_file(
        io.BytesIO(sample.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='sample_social_media_data.csv'
    )

# ─── Helper: Hitung Precision, Recall, F1, Accuracy dari data posts ─────────
def _compute_metrics(posts):
    """
    Karena tidak ada ground-truth label, pendekatan yang digunakan:
    - confidence >= 60  → dianggap prediksi 'yakin/benar' (True Positive proxy)
    - confidence < 60   → dianggap prediksi 'ragu/salah' (False Positive proxy)
    Metrik ini bersifat SELF-CONFIDENCE estimate, bukan evaluasi eksternal.
    """
    classes = ['positive', 'negative', 'neutral']
    total = len(posts)
    if total == 0:
        return None

    correct = sum(1 for p in posts if (p.confidence or 0) >= 60)
    accuracy = round(correct / total * 100, 1)

    per_class = {}
    for c in classes:
        tp = sum(1 for p in posts if p.sentiment == c and (p.confidence or 0) >= 60)
        fp = sum(1 for p in posts if p.sentiment == c and (p.confidence or 0) < 60)
        fn = sum(1 for p in posts if p.sentiment != c and (p.confidence or 0) >= 60)
        support = sum(1 for p in posts if p.sentiment == c)

        precision = round(tp / (tp + fp) * 100, 1) if (tp + fp) > 0 else 0.0
        recall    = round(tp / (tp + fn) * 100, 1) if (tp + fn) > 0 else 0.0
        f1        = round(2 * precision * recall / (precision + recall), 1) if (precision + recall) > 0 else 0.0

        per_class[c] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': support
        }

    # Macro-average
    macro_p  = round(sum(v['precision'] for v in per_class.values()) / 3, 1)
    macro_r  = round(sum(v['recall']    for v in per_class.values()) / 3, 1)
    macro_f1 = round(sum(v['f1']        for v in per_class.values()) / 3, 1)

    return {
        'accuracy': accuracy,
        'per_class': per_class,
        'macro': {'precision': macro_p, 'recall': macro_r, 'f1': macro_f1},
        'total': total
    }


# 3. ANALYSIS PAGE
@app.route('/analyze')
def analysis():
    selected_platform = request.args.get('platform', 'ALL')
    query = SocialPost.query
    if selected_platform != 'ALL':
        query = query.filter_by(platform=selected_platform)

    posts = query.all()
    total_likes = sum(p.likes or 0 for p in posts)
    total_shares = sum(p.shares or 0 for p in posts)
    avg_engagement = int(round((total_likes + total_shares) / len(posts))) if posts else 0

    top_posts = sorted(posts, key=lambda x: (x.engagement, x.created_at), reverse=True)[:50]
    top_keywords = extract_top_keywords([p.content for p in posts], top_n=35)
    max_kw_freq = top_keywords[0][1] if top_keywords else 1
    platforms = [r[0] for r in db.session.query(SocialPost.platform).distinct().all()]
    metrics = _compute_metrics(posts)

    return render_template(
        'analysis.html',
        total_likes=f"{total_likes:,}".replace(',', '.'),
        total_shares=f"{total_shares:,}".replace(',', '.'),
        avg_engagement=avg_engagement,
        top_posts=top_posts,
        top_keywords=top_keywords,
        max_kw_freq=max_kw_freq,
        platforms=platforms,
        selected_platform=selected_platform,
        metrics=metrics
    )

@app.route('/api/analysis-charts')
def analysis_charts():
    platform = request.args.get('platform', 'ALL')
    query = SocialPost.query
    if platform != 'ALL':
        query = query.filter_by(platform=platform)
    posts = query.all()

    sent_dist = {
        'negative': sum(1 for p in posts if p.sentiment == 'negative'),
        'neutral': sum(1 for p in posts if p.sentiment == 'neutral'),
        'positive': sum(1 for p in posts if p.sentiment == 'positive'),
    }

    plat_counts = {}
    for p in posts:
        plat_counts[p.platform.capitalize()] = plat_counts.get(p.platform.capitalize(), 0) + 1

    today = datetime.utcnow().date()
    days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    pos_7d = {d: 0 for d in days}
    neg_7d = {d: 0 for d in days}
    neu_7d = {d: 0 for d in days}

    for p in posts:
        d_str = p.created_at.strftime('%Y-%m-%d')
        if d_str in pos_7d:
            if p.sentiment == 'positive':
                pos_7d[d_str] += 1
            elif p.sentiment == 'negative':
                neg_7d[d_str] += 1
            else:
                neu_7d[d_str] += 1

    top_keywords = extract_top_keywords([p.content for p in posts], top_n=35)

    return jsonify({
        'sentiment': sent_dist,
        'platforms': plat_counts,
        'days': days,
        'pos_7d': list(pos_7d.values()),
        'neg_7d': list(neg_7d.values()),
        'neu_7d': list(neu_7d.values()),
        'keywords': [[w, c] for w, c in top_keywords],
    })

# 4. YOUTUBE ANALYZER (VIDEO COMMENTS & CHANNEL)
@app.route('/youtube-analyzer', methods=['GET', 'POST'])
def youtube_analyzer():
    result = None
    channel_id = ''
    engine = 'textblob'
    if request.method == 'POST':
        channel_id = request.form.get('channel_id', '').strip()
        engine = request.form.get('engine', 'textblob')
        try:
            result = analyze_youtube_url(channel_id)
            pos_count = 0
            neg_count = 0
            neu_count = 0
            for item in result['posts']:
                res = analyze_sentiment(item['content'], engine=engine)
                item['sentiment'] = res['sentiment']
                item['confidence'] = res['confidence']
                item['model_used'] = engine
                if res['sentiment'] == 'positive':
                    pos_count += 1
                elif res['sentiment'] == 'negative':
                    neg_count += 1
                else:
                    neu_count += 1

                _upsert_social_post(
                    platform='youtube',
                    username=item['username'],
                    content=item['content'],
                    sentiment=res['sentiment'],
                    confidence=res['confidence'],
                    model_used=engine,
                    likes=item['likes'],
                    shares=item['shares'],
                    created_at=item['created_at']
                )
            db.session.commit()
            total = len(result['posts']) or 1
            result['sentiment_summary'] = {
                'positive': pos_count,
                'negative': neg_count,
                'neutral': neu_count,
                'score': max(0, min(100, int(round((pos_count / total) * 100))))
            }
            if result.get('mode') == 'video_comments':
                flash(
                    f"Berhasil menganalisis {result['videos_analyzed']} komentar dari video \"{result['video_title']}\" ({engine.upper()})",
                    'success'
                )
            else:
                flash(f"Successfully analyzed {result['videos_analyzed']} videos from {result['channel_title']} ({engine.upper()})", 'success')
        except Exception as e:
            flash(f'Gagal menganalisis YouTube: {str(e)}', 'danger')

    return render_template('youtube_analyzer.html', result=result, channel_id=channel_id, engine=engine)


# 4B. THREADS ANALYZER
@app.route('/threads-analyzer', methods=['GET', 'POST'])
def threads_analyzer():
    result = None
    threads_url = ''
    engine = 'textblob'
    if request.method == 'POST':
        threads_url = request.form.get('threads_url', '').strip()
        engine = request.form.get('engine', 'textblob')
        try:
            result = analyze_threads_url(threads_url)
            pos_count = 0
            neg_count = 0
            neu_count = 0
            for item in result['posts']:
                res = analyze_sentiment(item['content'], engine=engine)
                item['sentiment'] = res['sentiment']
                item['confidence'] = res['confidence']
                item['model_used'] = engine
                if res['sentiment'] == 'positive':
                    pos_count += 1
                elif res['sentiment'] == 'negative':
                    neg_count += 1
                else:
                    neu_count += 1

                _upsert_social_post(
                    platform='threads',
                    username=item['username'],
                    content=item['content'],
                    sentiment=res['sentiment'],
                    confidence=res['confidence'],
                    model_used=engine,
                    likes=item['likes'],
                    shares=item['shares'],
                    created_at=item['created_at']
                )
            db.session.commit()
            total = len(result['posts']) or 1
            result['sentiment_summary'] = {
                'positive': pos_count,
                'negative': neg_count,
                'neutral': neu_count,
                'score': max(0, min(100, int(round((pos_count / total) * 100))))
            }
            flash(
                f"Berhasil menganalisis {result['total_posts']} post/balasan Threads dari {result['target']} ({engine.upper()})",
                'success'
            )
        except Exception as e:
            flash(f'Gagal menganalisis Threads: {str(e)}', 'danger')

    return render_template('threads_analyzer.html', result=result, threads_url=threads_url, engine=engine)


def _score_and_save_posts(posts: list, platform: str, engine: str) -> dict:
    """Analyze sentiment for a list of social posts, persist them, and return summary."""
    pos_count, neg_count, neu_count = 0, 0, 0
    for item in posts:
        res = analyze_sentiment(item['content'], engine=engine)
        item['sentiment'] = res['sentiment']
        item['confidence'] = res['confidence']
        item['model_used'] = engine
        if res['sentiment'] == 'positive':
            pos_count += 1
        elif res['sentiment'] == 'negative':
            neg_count += 1
        else:
            neu_count += 1

        _upsert_social_post(
            platform=platform,
            username=item['username'],
            content=item['content'],
            sentiment=res['sentiment'],
            confidence=res['confidence'],
            model_used=engine,
            likes=item['likes'],
            shares=item['shares'],
            created_at=item['created_at']
        )
    db.session.commit()
    total = len(posts) or 1
    return {
        'positive': pos_count,
        'negative': neg_count,
        'neutral': neu_count,
        'score': max(0, min(100, int(round((pos_count / total) * 100))))
    }


# 4C. TIKTOK ANALYZER
@app.route('/tiktok-analyzer', methods=['GET', 'POST'])
def tiktok_analyzer():
    result = None
    tiktok_url = ''
    engine = 'textblob'
    if request.method == 'POST':
        tiktok_url = request.form.get('tiktok_url', '').strip()
        engine = request.form.get('engine', 'textblob')
        try:
            result = analyze_tiktok_url(tiktok_url)
            result['sentiment_summary'] = _score_and_save_posts(result['posts'], 'tiktok', engine)
            flash(
                f"Berhasil menganalisis {result['total_posts']} item TikTok dari {result['target']} ({engine.upper()})",
                'success'
            )
        except Exception as e:
            flash(f'Gagal menganalisis TikTok: {str(e)}', 'danger')

    return render_template('tiktok_analyzer.html', result=result, tiktok_url=tiktok_url, engine=engine)


# 4D. TWITTER / X ANALYZER
@app.route('/twitter-analyzer', methods=['GET', 'POST'])
def twitter_analyzer():
    result = None
    twitter_url = ''
    engine = 'textblob'
    if request.method == 'POST':
        twitter_url = request.form.get('twitter_url', '').strip()
        engine = request.form.get('engine', 'textblob')
        try:
            result = analyze_twitter_url(twitter_url)
            result['sentiment_summary'] = _score_and_save_posts(result['posts'], 'twitter', engine)
            flash(
                f"Berhasil menganalisis {result['total_posts']} tweet dari {result['target']} ({engine.upper()})",
                'success'
            )
        except Exception as e:
            flash(f'Gagal menganalisis Twitter/X: {str(e)}', 'danger')

    return render_template('twitter_analyzer.html', result=result, twitter_url=twitter_url, engine=engine)


# 4E. INSTAGRAM ANALYZER
@app.route('/instagram-analyzer', methods=['GET', 'POST'])
def instagram_analyzer():
    result = None
    instagram_url = ''
    ig_account = ''
    raw_comments = ''
    engine = 'textblob'
    if request.method == 'POST':
        mode = request.form.get('mode', 'url')
        engine = request.form.get('engine', 'textblob')
        try:
            if mode == 'manual':
                ig_account = request.form.get('ig_account', '').strip()
                raw_comments = request.form.get('raw_comments', '')
                result = analyze_instagram_manual(ig_account, raw_comments)
            else:
                instagram_url = request.form.get('instagram_url', '').strip()
                result = analyze_instagram_url(instagram_url)

            result['sentiment_summary'] = _score_and_save_posts(result['posts'], 'instagram', engine)
            flash(
                f"Berhasil menganalisis {result['total_posts']} post Instagram dari {result['target']} ({engine.upper()})",
                'success'
            )
        except Exception as e:
            flash(f'Gagal menganalisis Instagram: {str(e)}', 'danger')

    return render_template(
        'instagram_analyzer.html',
        result=result,
        instagram_url=instagram_url,
        ig_account=ig_account,
        raw_comments=raw_comments,
        engine=engine
    )


@app.route('/clear-data', methods=['POST'])
def clear_data():
    deleted = SocialPost.query.delete()
    db.session.commit()
    flash(f'Berhasil menghapus {deleted} data analisis lama.', 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/panduan')
def panduan():
    return render_template('panduan.html')


# 5. LIVE MONITOR
@app.route('/live-monitor')
def live_monitor():
    return render_template('live_monitor.html')

@app.route('/api/live-feed')
def api_live_feed():
    posts = SocialPost.query.order_by(SocialPost.created_at.desc()).limit(15).all()
    total = len(posts) or 1
    pos_rate = round((sum(1 for p in posts if p.sentiment == 'positive') / total) * 100, 1)
    neg_rate = round((sum(1 for p in posts if p.sentiment == 'negative') / total) * 100, 1)
    neu_rate = round(100 - pos_rate - neg_rate, 1)

    platform_activity = dict(
        db.session.query(SocialPost.platform, func.count(SocialPost.id))
        .group_by(SocialPost.platform).all()
    )

    feed_data = [{
        'platform': p.platform,
        'username': p.username,
        'content': p.content,
        'sentiment': p.sentiment,
        'likes': p.likes,
        'time_ago': p.created_at.strftime('%Y-%m-%d %H:%M')
    } for p in posts]

    return jsonify({
        'posts_per_min': len(posts),
        'pos_rate': pos_rate,
        'neg_rate': neg_rate,
        'neu_rate': neu_rate,
        'platform_activity': platform_activity,
        'feed': feed_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)