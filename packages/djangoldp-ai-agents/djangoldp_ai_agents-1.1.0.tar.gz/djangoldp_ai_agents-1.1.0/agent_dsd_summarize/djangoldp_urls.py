from django.urls import path

from .views import DSDSummarizeView

urlpatterns = [
    path("dsd-summarize/", DSDSummarizeView.as_view(), name="dsd_summarize"),
]
