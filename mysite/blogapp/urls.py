from django.urls import path
from .views import (
    ArticlesListView,
    ArticleDetailView,
)

app_name = "blogapp"

urlpatterns = [
    path("", ArticlesListView.as_view(), name="articles"),
    path("articles/", ArticlesListView.as_view(), name="articles_list"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="article_detail"),
]