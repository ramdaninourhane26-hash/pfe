from django.db import models
from django.conf import settings

class BlogPost(models.Model):
    STATUS_CHOICES = [
    ('pending', 'En attente'),      # Nouveau statut
    ('draft', 'Brouillon'),
    ('published', 'Publié'),
    ('rejected', 'Refusé'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField(help_text="Résumé court pour la carte")
    content = models.TextField(help_text="Contenu complet de l'article")
    featured_image = models.URLField(blank=True, help_text="URL de l'image")
    category = models.CharField(max_length=50, default='articles')
    read_time = models.CharField(max_length=20, default='5 min read')
    author = models.CharField(max_length=100, default='NutriLife Team')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts'
    )
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title