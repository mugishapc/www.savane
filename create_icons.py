from PIL import Image, ImageDraw, ImageFont
import os

# Create 512x512 icon
img = Image.new('RGB', (512, 512), color='#0d6efd')
d = ImageDraw.Draw(img)
try:
    fnt = ImageFont.truetype("arial.ttf", 100)
except:
    fnt = ImageFont.load_default()
d.text((150, 200), "SAVANE", fill="white", font=fnt)
img.save('static/icon-512.png')

# Create 192x192 icon
img = Image.new('RGB', (192, 192), color='#0d6efd')
d = ImageDraw.Draw(img)
try:
    fnt = ImageFont.truetype("arial.ttf", 40)
except:
    fnt = ImageFont.load_default()
d.text((50, 70), "SAVANE", fill="white", font=fnt)
img.save('static/icon-192.png')

print("Icons created successfully!")