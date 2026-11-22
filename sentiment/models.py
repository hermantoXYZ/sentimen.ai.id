from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserQuota(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='quota')
    daily_limit = models.PositiveIntegerField(default=10, help_text="Batas analisis per hari")
    used_today = models.PositiveIntegerField(default=0)
    last_reset = models.DateField(default=timezone.localdate)

    def check_and_reset(self):
        today = timezone.localdate()
        if self.last_reset < today:
            self.used_today = 0
            self.last_reset = today
            self.save(update_fields=['used_today', 'last_reset'])

    @property
    def remaining(self):
        self.check_and_reset()
        return max(0, self.daily_limit - self.used_today)

    def __str__(self):
        return f"{self.user.username} ({self.used_today}/{self.daily_limit})"


class AnalysisLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    input_preview = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.category} ({self.created_at:%Y-%m-%d %H:%M})"


# Otomatis buat profil kuota setiap kali user baru ditambahkan
@receiver(post_save, sender=User)
def create_user_quota(sender, instance, created, **kwargs):
    if created:
        UserQuota.objects.create(user=instance)