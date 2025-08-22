import pytesseract

from PIL import Image

print(pytesseract.image_to_string(Image.open(r'D:\Coding\Projects\Python\ChatRtx\pdf\test.png')))