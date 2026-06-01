from django.urls import path
from . import views

app_name = 'converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('convert/', views.convert_page, name='convert'),
    path('api/merge/', views.merge_and_convert, name='merge_and_convert'),
    path('api/check-ffmpeg/', views.check_ffmpeg_status, name='check_ffmpeg'),
    path('api/preview/<str:filename>/', views.preview_file, name='preview_file'),
    path('api/download/<str:filename>/', views.download_file, name='download_file'),
]
