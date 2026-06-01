"""
Views for Cam Cap — API endpoints and page rendering.
"""
import json
import os
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import utils


def index(request):
    """Render the landing page."""
    return render(request, 'converter/index.html')


def convert_page(request):
    """Render the File System Access API converter page."""
    return render(request, 'converter/convert.html')


@require_GET
def check_ffmpeg_status(request):
    """Check if FFmpeg is installed and return status."""
    installed, message = utils.check_ffmpeg()
    return JsonResponse({
        'installed': installed,
        'message': message,
    })


@require_GET
def list_drives(request):
    """List all detected drives, highlighting removable ones."""
    try:
        drives = utils.get_removable_drives()
        return JsonResponse({
            'success': True,
            'drives': drives,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@require_GET
def browse_folder(request):
    """Browse a folder and return its contents (subfolders + .build files)."""
    folder_path = request.GET.get('path', '')
    
    if not folder_path:
        return JsonResponse({
            'success': False,
            'error': 'No path provided',
        }, status=400)
    
    # Security: normalize path
    folder_path = os.path.normpath(folder_path)
    
    items, error = utils.browse_directory(folder_path)
    
    if error:
        return JsonResponse({
            'success': False,
            'error': error,
        }, status=400)
    
    return JsonResponse({
        'success': True,
        'data': items,
    })


@csrf_exempt
@require_POST
def merge_and_convert(request):
    """Merge uploaded .build files into a single MP4."""
    try:
        files = request.FILES.getlist('files')
        sort_by = request.POST.get('sort_by', 'name')  # 'name' or 'date'
        
        if not files:
            return JsonResponse({
                'success': False,
                'error': 'No files uploaded',
            }, status=400)
        
        import tempfile
        import shutil
        
        # Save uploaded files to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            for f in files:
                temp_path = os.path.join(temp_dir, f.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
                file_paths.append(temp_path)
            
            # Default to media directory for output
            output_dir = str(settings.MEDIA_ROOT / 'converted')
            
            success, result = utils.merge_build_files(file_paths, output_dir, sort_by)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'data': result,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result,
                }, status=500)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@csrf_exempt
@require_POST
def delete_files(request):
    """Delete the specified .build files from the SD card."""
    try:
        body = json.loads(request.body)
        file_paths = body.get('files', [])
        
        if not file_paths:
            return JsonResponse({
                'success': False,
                'error': 'No files specified for deletion',
            }, status=400)
        
        success_count, fail_count, errors = utils.delete_build_files(file_paths)
        
        return JsonResponse({
            'success': True,
            'data': {
                'deleted': success_count,
                'failed': fail_count,
                'errors': errors,
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON body',
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@require_GET
def preview_file(request, filename):
    """Serve converted MP4 file for in-browser preview."""
    file_path = settings.MEDIA_ROOT / 'converted' / filename
    
    if not file_path.exists():
        raise Http404('File not found')
    
    response = FileResponse(
        open(file_path, 'rb'),
        content_type='video/mp4'
    )
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@require_GET
def download_file(request, filename):
    """Serve converted MP4 file for download."""
    # Check in media/converted first, then check custom paths
    file_path = settings.MEDIA_ROOT / 'converted' / filename
    
    if not file_path.exists():
        raise Http404('File not found')
    
    response = FileResponse(
        open(file_path, 'rb'),
        content_type='video/mp4',
        as_attachment=True,
        filename=filename
    )
    return response
