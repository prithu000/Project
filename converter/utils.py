"""
Utility functions for Cam Cap — drive detection, FFmpeg operations, file management.
"""
import os
import re
import subprocess
import shutil
import tempfile
import time
import uuid
import glob
from pathlib import Path
from datetime import datetime

import psutil

# Cache for discovered FFmpeg paths
_ffmpeg_cache = {}


def _find_ffmpeg_binary(name='ffmpeg'):
    """
    Find the ffmpeg (or ffprobe) binary.
    Checks PATH first, then common Windows install locations.
    Returns the full path string, or just the name if found on PATH.
    """
    if name in _ffmpeg_cache:
        return _ffmpeg_cache[name]

    # 1. Check if it's on PATH via shutil.which
    found = shutil.which(name)
    if found:
        _ffmpeg_cache[name] = found
        return found

    # 2. Search common Windows install locations
    search_dirs = []
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    user_profile = os.environ.get('USERPROFILE', '')
    program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
    program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')

    if local_app_data:
        # WinGet installs here
        search_dirs.append(os.path.join(local_app_data, 'Microsoft', 'WinGet', 'Packages'))
        # Links directory (winget aliases)
        search_dirs.append(os.path.join(local_app_data, 'Microsoft', 'WinGet', 'Links'))
    if user_profile:
        search_dirs.append(os.path.join(user_profile, 'ffmpeg'))
        search_dirs.append(os.path.join(user_profile, 'scoop', 'shims'))
    search_dirs.append(os.path.join(program_files, 'FFmpeg', 'bin'))
    search_dirs.append(os.path.join(program_files_x86, 'FFmpeg', 'bin'))
    search_dirs.append('C:\\ffmpeg\\bin')

    exe_name = f'{name}.exe' if os.name == 'nt' else name

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        # Direct check
        candidate = os.path.join(search_dir, exe_name)
        if os.path.isfile(candidate):
            _ffmpeg_cache[name] = candidate
            return candidate
        # Recursive search (for WinGet nested folders)
        for root, dirs, files in os.walk(search_dir):
            if exe_name in files:
                candidate = os.path.join(root, exe_name)
                _ffmpeg_cache[name] = candidate
                return candidate

    return None


def get_ffmpeg_path():
    """Get path to ffmpeg binary, or None if not found."""
    return _find_ffmpeg_binary('ffmpeg')


def get_ffprobe_path():
    """Get path to ffprobe binary, or None if not found."""
    return _find_ffmpeg_binary('ffprobe')


def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return False, 'FFmpeg not found. Please install FFmpeg from https://ffmpeg.org/download.html and restart the application.'
    try:
        result = subprocess.run(
            [ffmpeg, '-version'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            # Extract version string
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        return False, 'FFmpeg returned non-zero exit code'
    except FileNotFoundError:
        return False, 'FFmpeg not found. Please install FFmpeg and add it to your system PATH.'
    except subprocess.TimeoutExpired:
        return False, 'FFmpeg check timed out.'
    except Exception as e:
        return False, str(e)


def get_removable_drives():
    """
    Detect removable drives (SD cards, USB drives) on Windows.
    Returns a list of dicts with drive info.
    """
    drives = []
    
    for partition in psutil.disk_partitions(all=False):
        try:
            # On Windows, check for removable drives
            drive_type = 'unknown'
            opts = partition.opts.lower() if partition.opts else ''
            fstype = partition.fstype.lower() if partition.fstype else ''
            
            # Try to get drive type via WMI on Windows
            if os.name == 'nt':
                try:
                    drive_letter = partition.mountpoint.rstrip('\\')
                    result = subprocess.run(
                        ['wmic', 'logicaldisk', 'where', f'DeviceID="{drive_letter}"', 'get', 'DriveType', '/value'],
                        capture_output=True, text=True, timeout=5
                    )
                    output = result.stdout.strip()
                    # DriveType=2 is Removable, DriveType=3 is Local, DriveType=5 is CD-ROM
                    if 'DriveType=2' in output:
                        drive_type = 'removable'
                    elif 'DriveType=3' in output:
                        drive_type = 'local'
                    elif 'DriveType=5' in output:
                        drive_type = 'cdrom'
                    else:
                        drive_type = 'other'
                except Exception:
                    pass
            
            # Get disk usage
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total, used, free, percent = usage.total, usage.used, usage.free, usage.percent
            except (SystemError, Exception):
                # psutil.disk_usage can fail on certain Windows paths;
                # fall back to shutil.disk_usage
                try:
                    disk = shutil.disk_usage(partition.mountpoint)
                    total, used, free = disk.total, disk.used, disk.free
                    percent = round((used / total) * 100, 1) if total > 0 else 0
                except Exception:
                    continue
            
            drive_info = {
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'fstype': partition.fstype,
                'type': drive_type,
                'total': total,
                'used': used,
                'free': free,
                'percent': percent,
                'total_display': format_size(total),
                'used_display': format_size(used),
                'free_display': format_size(free),
            }
            drives.append(drive_info)
            
        except (PermissionError, OSError, SystemError):
            continue
    
    return drives


def format_size(size_bytes):
    """Format bytes to human-readable size string."""
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"


def browse_directory(dir_path):
    """
    Browse a directory and return its contents.
    Returns folders and .build files sorted by name.
    """
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        return None, 'Directory does not exist'
    
    if not dir_path.is_dir():
        return None, 'Path is not a directory'
    
    items = {
        'current_path': str(dir_path),
        'parent_path': str(dir_path.parent) if dir_path.parent != dir_path else None,
        'folders': [],
        'files': [],
        'build_file_count': 0,
        'total_build_size': 0,
    }
    
    try:
        for entry in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                if entry.is_dir():
                    # Count .build files in subfolder
                    build_count = count_build_files(entry)
                    items['folders'].append({
                        'name': entry.name,
                        'path': str(entry),
                        'build_count': build_count,
                    })
                elif entry.suffix.lower() == '.build' and not entry.name.startswith('._'):
                    stat = entry.stat()
                    file_info = {
                        'name': entry.name,
                        'path': str(entry),
                        'size': stat.st_size,
                        'size_display': format_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'modified_ts': stat.st_mtime,
                    }
                    # Try to get duration via FFmpeg
                    duration = get_media_duration(str(entry))
                    if duration:
                        file_info['duration'] = duration
                        file_info['duration_display'] = format_duration(duration)
                    else:
                        file_info['duration'] = None
                        file_info['duration_display'] = 'Unknown'
                    
                    items['files'].append(file_info)
                    items['build_file_count'] += 1
                    items['total_build_size'] += stat.st_size
            except (PermissionError, OSError):
                continue
        
        items['total_build_size_display'] = format_size(items['total_build_size'])
        
    except PermissionError:
        return None, 'Permission denied'
    
    return items, None


def count_build_files(dir_path):
    """Count .build files in a directory (non-recursive for performance)."""
    count = 0
    try:
        for entry in dir_path.iterdir():
            if entry.is_file() and entry.suffix.lower() == '.build' and not entry.name.startswith('._'):
                count += 1
    except (PermissionError, OSError):
        pass
    return count


def get_media_duration(file_path):
    """Get media file duration in seconds using FFprobe."""
    ffprobe = get_ffprobe_path()
    if not ffprobe:
        return None
    try:
        result = subprocess.run(
            [
                ffprobe, '-v', 'quiet',
                '-print_format', 'json',
                '-show_entries', 'format=duration',
                file_path
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            return duration if duration > 0 else None
    except Exception:
        pass
    return None


def format_duration(seconds):
    """Format seconds to MM:SS or HH:MM:SS string."""
    if seconds is None:
        return 'Unknown'
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def merge_build_files(file_paths, output_dir, sort_by='name'):
    """
    Merge multiple .build files into a single MP4 using FFmpeg.
    
    Args:
        file_paths: List of absolute paths to .build files
        output_dir: Directory to save the output MP4
        sort_by: 'name' or 'date' — how to sort files before merging
    
    Returns:
        (success, output_path_or_error_message)
    """
    if not file_paths:
        return False, 'No files provided'
    
    # Find FFmpeg binary
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return False, (
            'FFmpeg is not installed or not found. '
            'Please install FFmpeg from https://ffmpeg.org/download.html '
            'and restart the application.'
        )
    
    # Sort files
    if sort_by == 'date':
        file_paths = sorted(file_paths, key=lambda f: os.path.getmtime(f))
    else:
        file_paths = sorted(file_paths, key=lambda f: os.path.basename(f).lower())
    
    # Filter out macOS resource fork files (._* prefix)
    file_paths = [fp for fp in file_paths if not os.path.basename(fp).startswith('._')]
    
    if not file_paths:
        return False, 'No valid video files found (macOS resource fork files were filtered out)'
    
    # Verify all files exist
    for fp in file_paths:
        if not os.path.isfile(fp):
            return False, f'File not found: {fp}'
    
    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:6]
    output_filename = f'CamCap_{timestamp}_{unique_id}.mp4'
    
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename
    
    # Create concat file for FFmpeg
    concat_file = output_dir / f'concat_{unique_id}.txt'
    try:
        with open(concat_file, 'w', encoding='utf-8') as f:
            for fp in file_paths:
                # FFmpeg concat requires forward slashes and single-quote escaping
                safe_path = Path(fp).as_posix().replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
        
        # Run FFmpeg concat
        cmd = [
            ffmpeg, '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-movflags', '+faststart',
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            # If copy codec fails, try re-encoding
            cmd_reencode = [
                ffmpeg, '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd_reencode,
                capture_output=True, text=True, timeout=1800  # 30 minute timeout for re-encoding
            )
            
            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else 'Unknown FFmpeg error'
                return False, f'FFmpeg error: {error_msg}'
        
        # Verify output file exists and has size
        if output_path.exists() and output_path.stat().st_size > 0:
            return True, {
                'filename': output_filename,
                'path': str(output_path),
                'size': output_path.stat().st_size,
                'size_display': format_size(output_path.stat().st_size),
            }
        else:
            return False, 'Output file was not created'
        
    except subprocess.TimeoutExpired:
        return False, 'FFmpeg merge operation timed out'
    except Exception as e:
        return False, str(e)
    finally:
        # Clean up concat file
        if concat_file.exists():
            concat_file.unlink()


def delete_build_files(file_paths):
    """
    Delete the specified .build files.
    Returns (success_count, fail_count, errors)
    """
    success_count = 0
    fail_count = 0
    errors = []
    
    for fp in file_paths:
        try:
            fp_path = Path(fp)
            if fp_path.exists() and fp_path.suffix.lower() == '.build':
                fp_path.unlink()
                success_count += 1
            else:
                fail_count += 1
                errors.append(f'File not found or not .build: {fp}')
        except Exception as e:
            fail_count += 1
            errors.append(f'Error deleting {fp}: {str(e)}')
    
    return success_count, fail_count, errors
