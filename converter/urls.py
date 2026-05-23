from django.urls import path
from . import views

app_name = 'converter'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/drives/', views.list_drives, name='list_drives'),
    path('api/browse/', views.browse_folder, name='browse_folder'),
    path('api/merge/', views.merge_and_convert, name='merge_and_convert'),
    path('api/delete/', views.delete_files, name='delete_files'),
    path('api/check-ffmpeg/', views.check_ffmpeg_status, name='check_ffmpeg'),
    path('api/preview/<str:filename>/', views.preview_file, name='preview_file'),
    path('api/download/<str:filename>/', views.download_file, name='download_file'),
]
