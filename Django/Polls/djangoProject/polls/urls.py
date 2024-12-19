from django.urls import path
from debug_toolbar.toolbar import debug_toolbar_urls # type: ignore
from . import views

app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:pk>/vote/", views.VoteView.as_view(), name="vote"),
    
]+ debug_toolbar_urls()

