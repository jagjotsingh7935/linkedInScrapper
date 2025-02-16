from django.urls import path
from .views import JobSearchView, DownloadCSVView

urlpatterns = [
    path('search/', JobSearchView.as_view(), name='job-search'),
    path('download-csv/', DownloadCSVView.as_view(), name='download-csv'),
]