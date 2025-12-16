from django.db import models


class PublishedModel(models.Model):
    """Абстрактная модель с полем публикации."""

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )

    class Meta:
        abstract = True


class CreatedModel(models.Model):
    """Абстрактная модель с полем времени создания."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено',
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class BaseModel(PublishedModel, CreatedModel):
    """Базовая модель, объединяющая PublishedModel и CreatedModel."""

    class Meta:
        abstract = True
