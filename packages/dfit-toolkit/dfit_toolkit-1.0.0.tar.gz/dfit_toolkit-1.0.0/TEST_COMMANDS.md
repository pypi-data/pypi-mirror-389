🧪 DFIT Testing Commands
Step 1: Create a Test Image
bash


# Create a test image with some content
cd /home/ubuntu/DFIT
./venv/bin/python3 -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (1200, 800), color='lightblue')
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 1150, 750], fill='white', outline='black', width=3)
draw.ellipse([200, 150, 500, 450], fill='red')
draw.rectangle([600, 150, 900, 450], fill='green')
draw.polygon([(750, 500), (600, 700), (900, 700)], fill='yellow')
draw.text((100, 100), 'DFIT Test Image', fill='black')
img.save('my_test_image.jpg', quality=95)
print('✅ Test image created: my_test_image.jpg')
"
# Step 2: Test All DFIT Commands

## 1. Check Version & Help
bash
./venv/bin/dfit --version
./venv/bin/dfit --help

## 2. Metadata Extraction
bash
# Basic metadata
./venv/bin/dfit metadata -i my_test_image.jpg

# Export to JSON
./venv/bin/dfit metadata -i my_test_image.jpg -o metadata_report.json

# View the JSON
cat metadata_report.json | head -20

## 3. Tampering Detection
bash
# Detect tampering
./venv/bin/dfit detect-tampering -i my_test_image.jpg

# Export results to JSON
./venv/bin/dfit detect-tampering -i my_test_image.jpg -o tampering_report.json


## 4. Steganography Detection
bash
# Scan for hidden data
./venv/bin/dfit scan-stego -i my_test_image.jpg

# Export results to JSON
./venv/bin/dfit scan-stego -i my_test_image.jpg -o stego_report.json


##  5. Comprehensive Analysis
bash
# Run all analysis modules
./venv/bin/dfit analyze -i my_test_image.jpg

# Export comprehensive report
./venv/bin/dfit analyze -i my_test_image.jpg -o full_analysis.json


## 6. Extract Hidden Data (if any detected)
bash
./venv/bin/dfit extract -i my_test_image.jpg -o extracted_data.bin
Step 3: Test with Real Image (Optional)


# List all generated JSON reports
ls -lh *.json


# View full analysis
./venv/bin/python3 -m json.tool full_analysis.json | less
Step 6: Clean Up Test Files
bash
# Remove test files
rm -f my_test_image.jpg
rm -f metadata_report.json tampering_report.json stego_report.json full_analysis.json
rm -f extracted_data.bin sample.png