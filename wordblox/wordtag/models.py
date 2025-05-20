from django.db import models

# Create your models here.

class TextAbstractModel(models.Model):
    text = models.CharField(max_length=75)

    class Meta:
        abstract = True

class Domain(models.Model): # Questionable, consider before migrating
    url = models.URLField(unique=True)

class Tag(TextAbstractModel):
    domain = models.ForeignKey(Domain, related_name="tags", on_delete=models.CASCADE)

class Word(TextAbstractModel):
    tag = models.ForeignKey(Tag, related_name="words", on_delete=models.CASCADE)
    details = models.TextField()

    class Meta:
        unique_together = ("text", "tag")