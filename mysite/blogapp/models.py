from django.db import models
from django.urls import reverse


class Author(models.Model):
    name = models.CharField(max_length=100, null=False)
    bio = models.TextField(blank=True)


class Category(models.Model):
    name = models.CharField(max_length=40, null=False, blank=True)


class Tag(models.Model):
    name = models.CharField(max_length=20, null=False, blank=True)


class Article(models.Model):
    class Meta:
        ordering = ["pk", "title"]

    title = models.CharField(max_length=200, null=False, blank=True)
    content = models.TextField(blank=True)
    pub_date = models.DateTimeField(null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, related_name="article_tags")

    def __str__(self):
        return f"Article(pk={self.pk}, name={self.title!r})"

    def get_absolute_url(self):
        return reverse("blogapp:article", kwargs={"pk":self.pk})
