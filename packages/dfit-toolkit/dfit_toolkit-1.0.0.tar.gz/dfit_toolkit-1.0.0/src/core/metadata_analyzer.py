# src/core/metadata_analyzer.py
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ExifTags
import exifread
import os
import hashlib

def file_info(path: str) -> Dict[str, Any]:
    st = os.stat(path)
    with Image.open(path) as im:
        width, height = im.size
        mode = im.mode
        fmt = im.format
        mime = Image.MIME.get(fmt, "application/octet-stream")
    return {
        "path": os.path.abspath(path),
        "size_bytes": st.st_size,
        "format": fmt,
        "mime": mime,
        "dimensions": {"width": width, "height": height},
        "mode": mode,
    }

def compute_hashes(path: str, algos=("md5", "sha256")) -> Dict[str, str]:
    hashes = {a: hashlib.new(a) for a in algos}
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            for h in hashes.values():
                h.update(chunk)
    return {name: h.hexdigest() for name, h in hashes.items()}

def _exif_dict_pillow(path: str) -> Dict[str, Any]:
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            tag_map = {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()}
            return tag_map
    except Exception:
        return {}

def _exif_dict_exifread(path: str) -> Dict[str, Any]:
    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)
        # Convert keys to simple strings
        return {str(k): str(v) for k, v in tags.items()}
    except Exception:
        return {}

def _parse_gps_from_pillow(exif: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    # GPSInfo structure varies; this keeps it simple and robust
    gps = exif.get("GPSInfo")
    if not gps:
        return None
    try:
        # Pillow returns rational tuples; convert to decimal degrees
        def to_deg(values, ref):
            d = values[0] / values[1]
            m = values[1] / values[1][1]
            s = values[2] / values[2][1]
            deg = d + m/60.0 + s/3600.0
            if ref in ["S", "W"]:
                deg = -deg
            return deg
        lat = to_deg(gps[2], gps[1])
        lon = to_deg(gps[3], gps[4])
        return (lat, lon)
    except Exception:
        return None

def extract_metadata(path: str) -> Dict[str, Any]:
    info = file_info(path)
    hashes = compute_hashes(path)
    exif_pil = _exif_dict_pillow(path)
    exif_er = _exif_dict_exifread(path)
    gps = _parse_gps_from_pillow(exif_pil)

    # Timestamp fields commonly used
    timestamps = {
        "DateTimeOriginal": exif_pil.get("DateTimeOriginal") or exif_er.get("EXIF DateTimeOriginal"),
        "CreateDate": exif_pil.get("DateTimeDigitized") or exif_er.get("EXIF DateTimeDigitized"),
        "ModifyDate": exif_pil.get("DateTime") or exif_er.get("Image DateTime"),
        "Software": exif_pil.get("Software") or exif_er.get("Image Software"),
    }

    camera = {
        "Make": exif_pil.get("Make") or exif_er.get("Image Make"),
        "Model": exif_pil.get("Model") or exif_er.get("Image Model"),
        "LensModel": exif_pil.get("LensModel") or exif_er.get("EXIF LensModel"),
    }

    result = {
        "file": info,
        "hashes": hashes,
        "camera": camera,
        "timestamps": timestamps,
        "gps": {"lat": gps[0], "lon": gps[1]} if gps else None,
        "exif_pillow": exif_pil,
        "exif_exifread": exif_er,
    }
    return result
