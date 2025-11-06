import exifread
import os

def extract_gps_coordinates_exifread(image_path):
    """
    Extract GPS coordinates from an image using exifread.
    Returns a dict with 'lat', 'lon', 'map_url_osm', and 'map_url_google' if available, else None.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
    def to_deg(values, ref):
        d = float(values[0].values)
        m = float(values[1].values)
        s = float(values[2].values)
        deg = d + m / 60.0 + s / 3600.0
        if ref in ['S', 'W']:
            deg = -deg
        return deg
    try:
        lat = to_deg(tags['GPS GPSLatitude'], tags['GPS GPSLatitudeRef'].printable)
        lon = to_deg(tags['GPS GPSLongitude'], tags['GPS GPSLongitudeRef'].printable)
        gps = {
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'map_url_osm': f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}",
            'map_url_google': f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        }
        return gps
    except KeyError:
        return None

# Optional: generate static HTML map with folium
try:
    import folium
    def generate_gps_html_map(lat, lon, output_file="photo_gps_map.html"):
        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], popup="Photo Location").add_to(m)
        m.save(output_file)
        return os.path.abspath(output_file)
except ImportError:
    folium = None
    def generate_gps_html_map(lat, lon, output_file="photo_gps_map.html"):
        raise ImportError("folium is not installed. Run 'pip install folium'.")


# Example usage in CLI/toolkit:
if __name__ == "__main__":
    imgpath = "examples/sample_images/photo.jpg"  # <- set correct path!
    gps = extract_gps_coordinates_exifread(imgpath)
    if gps:
        print(f"Latitude:  {gps['lat']}")
        print(f"Longitude: {gps['lon']}")
        print(f"OpenStreetMap URL:  {gps['map_url_osm']}")
        print(f"Google Maps URL:    {gps['map_url_google']}")
        # Generate HTML map if folium is available
        if folium:
            html_path = generate_gps_html_map(gps['lat'], gps['lon'])
            print(f"GPS map saved: {html_path}")
    else:
        print("No GPS data found in image.")

