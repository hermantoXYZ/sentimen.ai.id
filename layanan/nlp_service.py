import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

for res in ['punkt', 'stopwords']:
    try:
        nltk.data.find(f'corpora/{res}' if res == 'stopwords' else f'tokenizers/{res}')
    except LookupError:
        nltk.download(res, quiet=True)

try:
    _EN_STOPWORDS = set(stopwords.words('english'))
except LookupError:
    _EN_STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be',
        'this', 'that', 'it', 'its', 'my', 'your', 'our', 'their', 'i', 'you'
    }

STOPWORDS = _EN_STOPWORDS.union({
    'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'untuk', 'pada',
    'dengan', 'adalah', 'saya', 'tidak', 'yg', 'nya', 'aja', 'saja',
    'akan', 'atau', 'juga', 'sudah', 'bisa', 'ada', 'karena', 'jadi'
})


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join([w for w in text.split() if w not in STOPWORDS and len(w) > 2])


POS_ID = {
    'bagus', 'berkualitas', 'tinggi', 'mantap', 'keren', 'win', 'cepat', 'puas',
    'terbaik', 'hebat', 'membantu', 'suka', 'cinta', 'senang', 'gembira', 'bahagia',
    'nyaman', 'aman', 'lancar', 'murah', 'promo', 'diskon', 'gratis', 'berhasil',
    'sukses', 'juara', 'rekomendasi', 'recommended', 'ramah', 'bersih', 'rapi',
    'sempurna', 'top', 'oke', 'sip', 'jos', 'mantul', 'luarbiasa', 'unik',
    'menarik', 'seru', 'asik', 'asyik', 'positif', 'unggul', 'memuaskan', 'worth',
    'good', 'great', 'best', 'awesome', 'amazing', 'happy', 'love', 'nice', 'super'
}

NEG_ID = {
    'buruk', 'kecewa', 'parah', 'lambat', 'rugi', 'error', 'gagal', 'jelek',
    'sampah', 'pensiun', 'benci', 'marah', 'kesal', 'mahal', 'lemot', 'macet',
    'rusak', 'cacat', 'palsu', 'penipu', 'bohong', 'hoax', 'susah', 'sulit',
    'ribet', 'bingung', 'bosan', 'mengecewakan', 'menyesal', 'hancur', 'kacau',
    'negatif', 'bahaya', 'toxic', 'scam', 'terburuk', 'payah', 'kurang',
    'terrible', 'bad', 'worst', 'hate', 'broken', 'fail', 'failed', 'slow', 'awful'
}

NEGATIONS = {'tidak', 'bukan', 'tak', 'gak', 'ga', 'nggak', 'enggak', 'jangan', 'kurang', 'belum', 'not', 'no', 'never'}


def _analyze_textblob(text: str) -> dict:
    tokens = re.findall(r'\w+', text.lower())
    pos_score = 0
    neg_score = 0

    for i, tok in enumerate(tokens):
        prev = tokens[i - 1] if i > 0 else ''
        is_negated = prev in NEGATIONS
        if tok in POS_ID:
            if is_negated:
                neg_score += 1
            else:
                pos_score += 1
        elif tok in NEG_ID:
            if is_negated:
                pos_score += 1
            else:
                neg_score += 1

    if pos_score > neg_score:
        diff = pos_score - neg_score
        return {'sentiment': 'positive', 'confidence': min(98, 65 + diff * 12)}
    elif neg_score > pos_score:
        diff = neg_score - pos_score
        return {'sentiment': 'negative', 'confidence': min(98, 65 + diff * 12)}

    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return {'sentiment': 'positive', 'confidence': int(min(98, 58 + polarity * 40))}
    elif polarity < -0.1:
        return {'sentiment': 'negative', 'confidence': int(min(98, 58 + abs(polarity) * 40))}
    return {'sentiment': 'neutral', 'confidence': 52}


_TRAINING_DATA = [
    # Positive (Indonesian & English)
    ("produk ini sangat bagus dan berkualitas tinggi", "positive"),
    ("pelayanan sangat ramah cepat dan memuaskan", "positive"),
    ("barang sampai dengan aman packing rapi mantap", "positive"),
    ("sangat puas belanja disini recommended banget", "positive"),
    ("harga murah kualitas terbaik tidak mengecewakan", "positive"),
    ("aplikasi ini sangat membantu dan mudah digunakan", "positive"),
    ("keren banget fiturnya lancar jaya tanpa kendala", "positive"),
    ("video ini sangat menginspirasi dan bermanfaat sekali", "positive"),
    ("tutorial yang sangat jelas mudah dipahami sukses selalu", "positive"),
    ("jump over the lava win mantap keren amazing", "positive"),
    ("i built 100 houses and gave them away best day ever", "positive"),
    ("my honest life update super happy awesome video", "positive"),
    ("great content love this channel so much", "positive"),
    ("best product ever works smoothly and fast", "positive"),
    ("senang sekali hasilnya luar biasa sempurna", "positive"),
    ("pengiriman cepat respon admin baik sekali", "positive"),
    # Negative (Indonesian & English)
    ("pelayanan sangat buruk sangat kecewa parah", "negative"),
    ("error gagal lambat mengecewakan sekali", "negative"),
    ("barang rusak cacat tidak sesuai deskripsi rugi", "negative"),
    ("aplikasi lemot sering crash macet susah dipakai", "negative"),
    ("harga mahal kualitas sampah menyesal beli ini", "negative"),
    ("penipu hoax palsu jangan percaya channel ini", "negative"),
    ("respon lambat admin tidak ramah sangat buruk", "negative"),
    ("tidak bagus sama sekali mengecewakan dan jelek", "negative"),
    ("reviewing terrible mobile game ads worst ever", "negative"),
    ("most dangerous trap fail and lose awful", "negative"),
    ("terrible experience broken and slow waste of money", "negative"),
    ("hate this update worst performance ever", "negative"),
    ("windows 10 segera pensiun bikin ribet pengguna", "negative"),
    ("bosen banget kontennya garing tidak menarik", "negative"),
    ("kecewa berat barang tidak sampai uang hilang", "negative"),
    ("kurang memuaskan hasil tidak sesuai harapan", "negative"),
    # Neutral (Indonesian & English)
    ("pengalaman unboxing biasa saja standar", "neutral"),
    ("hirarki data dari bit sampai database", "neutral"),
    ("demo aplikasi spk metode saw dengan fitur api", "neutral"),
    ("1 minggu menuju akhir masa pakainya", "neutral"),
    ("jadwal rilis pembaruan sistem bulan depan", "neutral"),
    ("cara menginstall python di komputer windows", "neutral"),
    ("daftar harga paket internet terbaru hari ini", "neutral"),
    ("informasi cuaca untuk wilayah jakarta dan sekitarnya", "neutral"),
    ("reading fan comments and memes this week", "neutral"),
    ("unboxing tech gadgets from online store", "neutral"),
    ("tried building my own pc setup again", "neutral"),
    ("survive 100 days in bunker challenge", "neutral"),
    ("perbandingan spesifikasi laptop untuk kerja", "neutral"),
    ("pengumuman pemeliharaan server malam ini", "neutral"),
    ("ringkasan berita teknologi minggu ini", "neutral"),
    ("panduan dasar belajar pemrograman web", "neutral"),
]

_SAMPLES = [t for t, _ in _TRAINING_DATA]
_LABELS = [l for _, l in _TRAINING_DATA]
_vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
_clf = MultinomialNB(alpha=0.5).fit(_vec.fit_transform(_SAMPLES), _LABELS)


def _analyze_sklearn(text: str) -> dict:
    X = _vec.transform([text.lower()])
    if X.nnz == 0:
        # Fallback ke lexicon jika tidak ada kata yang cocok di vocabulary
        return _analyze_textblob(text)
    pred = _clf.predict(X)[0]
    prob = int(round(max(_clf.predict_proba(X)[0]) * 100))
    return {'sentiment': pred, 'confidence': prob}


_bert_pipe = None


def _analyze_bert(text: str) -> dict:
    global _bert_pipe
    try:
        if _bert_pipe is None:
            from transformers import pipeline
            _bert_pipe = pipeline(
                "sentiment-analysis",
                model="mdhugol/indonesia-bert-sentiment-classification"
            )
        out = _bert_pipe(text[:512])[0]
        lbl = out['label'].upper()
        conf = int(round(out['score'] * 100))
        if 'POS' in lbl or lbl == 'LABEL_0':
            return {'sentiment': 'positive', 'confidence': conf}
        elif 'NEG' in lbl or lbl == 'LABEL_2':
            return {'sentiment': 'negative', 'confidence': conf}
        return {'sentiment': 'neutral', 'confidence': conf}
    except ImportError:
        return _analyze_sklearn(text)


def analyze_sentiment(text: str, engine: str = 'textblob') -> dict:
    if engine == 'sklearn':
        return _analyze_sklearn(text)
    elif engine == 'bert':
        return _analyze_bert(text)
    return _analyze_textblob(text)


def extract_top_keywords(texts: list, top_n: int = 10) -> list:
    words = []
    for t in texts:
        words.extend(clean_text(t).split())
    return Counter(words).most_common(top_n)
