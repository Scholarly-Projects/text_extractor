import os
import pytesseract
from PIL import Image, ImageFilter, ImageOps
import csv

# Function to preprocess the image for better OCR results
def preprocess_image(image_path):
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale
            img = img.convert("L")

            # Apply binarization
            img = img.point(lambda x: 0 if x < 128 else 255, '1')

            # Optional: apply a filter to reduce noise
            img = img.filter(ImageFilter.MedianFilter(size=3))

            # Optionally resize the image
            img = img.resize((img.width * 2, img.height * 2), Image.ANTIALIAS)

            return img
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

# Function to perform OCR on an image and extract text
def extract_text_from_image(image_path):
    img = preprocess_image(image_path)
    if img is None:
        return ""

    try:
        # Use Tesseract to do OCR on the preprocessed image
        # Adjust psm for better recognition; try different modes if needed
        text = pytesseract.image_to_string(img, config='--psm 6')  # Assume a single block of text
        return text.strip()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return ""

# Function to process images in folder A and export transcriptions to a CSV file in folder B
def process_images(input_folder, output_folder, output_csv):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    csv_rows = []

    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".png", ".tiff", ".jpg", ".jpeg")):
            input_image_path = os.path.join(input_folder, filename)
            print(f"Processing {filename}...")

            # Extract text from the image
            text = extract_text_from_image(input_image_path)

            if text:  # If text is detected
                formatted_text = f'includes the text: "{text}"'
                csv_rows.append([filename, formatted_text])
            else:
                csv_rows.append([filename, "No text detected"])

    # Write the transcriptions to a CSV file
    csv_output_path = os.path.join(output_folder, output_csv)
    with open(csv_output_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Filename', 'Transcribed Text'])
        for row in csv_rows:
            writer.writerow(row)

    print(f"Saved transcriptions to {csv_output_path}")

if __name__ == "__main__":
    input_folder = "A"  # Relative path to Folder A
    output_folder = "B"  # Relative path to Folder B
    output_csv = "transcriptions.csv"

    process_images(input_folder, output_folder, output_csv)
