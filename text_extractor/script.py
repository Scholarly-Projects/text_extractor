import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import csv

# Function to perform OCR on an image and extract text
def extract_text_from_image(image_path):
    try:
        # Open the image file
        with Image.open(image_path) as img:
            # Convert image to grayscale
            img = img.convert("L")

            # Enhance the image contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2)  # Increase contrast

            # Apply a threshold filter to binarize the image
            img = img.point(lambda x: 0 if x < 128 else 255, '1')

            # Use Tesseract to do OCR on the processed image
            text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return ""

# Function to process images in folder A and export transcriptions to a CSV file in folder B
def process_images(input_folder, output_folder, output_csv):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    csv_rows = []

    # Iterate through each file in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".png", ".tiff", ".jpg", ".jpeg")):
            input_image_path = os.path.join(input_folder, filename)
            print(f"Processing {filename}...")

            # Extract text from the image
            text = extract_text_from_image(input_image_path)

            if text:  # If text is detected
                # Format the text for CSV output
                formatted_text = f'includes the text: "{text}"'
                csv_rows.append([filename, formatted_text])
            else:
                # If no text is detected, leave the column empty
                csv_rows.append([filename, "No text detected"])

    # Write the transcriptions to a CSV file
    csv_output_path = os.path.join(output_folder, output_csv)
    with open(csv_output_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        # Write the header
        writer.writerow(['Filename', 'Transcribed Text'])

        # Write the rows
        for row in csv_rows:
            writer.writerow(row)

    print(f"Saved transcriptions to {csv_output_path}")

if __name__ == "__main__":
    # Set the correct paths for Folder A (input images) and Folder B (output CSV)
    input_folder = "A"  # Relative path to Folder A
    output_folder = "B"  # Relative path to Folder B
    output_csv = "transcriptions.csv"

    process_images(input_folder, output_folder, output_csv)
