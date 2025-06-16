from django.contrib.syndication.views import Feed
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy, reverse

from blogapp.models import Article


class BasedView(ListView):
    queryset = (
        Article.objects
        .select_related("author", "category")
        .prefetch_related("tags")
        .defer("content")
    )
    template_name = "blogapp/article_list.html"
    context_object_name = "articles"

class ArticlesListView(ListView):
    queryset = (
            Article.objects
            .filter(pub_date__isnull=False)
            .order_by("-pub_date")
        )
    template_name = "blogapp/article_list.html"
    context_object_name = "articles"


class ArticleDetailView(DetailView):
    model = Article

class LatestArticlesFeed(Feed):
    title = "Blog articles(latets)"
    description = "Update on changes and additon blog acticles"
    link = reverse_lazy("blogapp:articles")

    def items(self):
        return (
            Article.objects
            .filter(pub_date__isnull=False)
            .order_by("-pub_date")[:5]
        )

    def item_title(self, item: Article):
        return item.title

    def item_description(self, item: Article):
        return item.content[:200]

    # def item_link(self, item: Article):
    #     return reverse("blogapp:article", kwargs={"pk":item.pk})
