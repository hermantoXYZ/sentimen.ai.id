from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SocialPost(db.Model):
    __tablename__ = 'social_posts'

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)        # youtube, instagram, twitter, facebook, tiktok
    username = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)       # positive, negative, neutral
    confidence = db.Column(db.Integer, default=50)             # 0 - 100%
    model_used = db.Column(db.String(30), default='textblob')  # textblob, sklearn, bert
    likes = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def engagement(self):
        return (self.likes or 0) + (self.shares or 0)