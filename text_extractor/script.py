import os
import pytesseract
from PIL import Image, ImageFilter
import csv
from spellchecker import SpellChecker
import re

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  # Adjust this if necessary

# Initialize the SpellChecker
spell = SpellChecker()

# Function to preprocess the image for better OCR results
def preprocess_image(image_path):
    with Image.open(image_path) as img:
        # Convert to grayscale
        img = img.convert('L')
        # Apply a Gaussian blur to reduce noise
        img = img.filter(ImageFilter.GaussianBlur(1))
        # Binarize the image (thresholding)
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        return img

# Function to perform OCR on an image and extract text using typed text recognition
def extract_text_typed(image_path):
    try:
        img = preprocess_image(image_path)
        # Use Tesseract for typed text
        text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
        return text.strip()
    except Exception as e:
        print(f"Error processing {image_path} for typed text: {e}")
        return ""

# Function to perform OCR on an image and extract text using handwritten text recognition
def extract_text_handwritten(image_path):
    try:
        img = preprocess_image(image_path)
        # Use Tesseract for handwritten text
        text = pytesseract.image_to_string(img, lang='eng+handwriting', config='--psm 6')
        return text.strip()
    except Exception as e:
        print(f"Error processing {image_path} for handwritten text: {e}")
        return ""

# Function to filter out unrecognized words from extracted text
def filter_recognized_words(text):
    # Allow single characters followed by a period (like U.S.D.A)
    text = re.sub(r'(?<=\b[A-Za-z]\.)[A-Za-z]', '', text)  # Remove trailing letters after a period

    # Remove unwanted characters while retaining common punctuation
    text = re.sub(r'[^a-zA-Z0-9\s.,;\'"?!-]', '', text)  # Keep letters, numbers, spaces, and some punctuation
    # Split the text into words
    words = text.split()

    # Length filtering: Discard words shorter than 2 characters or longer than 15 characters
    words = [word for word in words if 2 <= len(word) <= 15]

    # Pattern filtering: Discard repeated characters and numeric-only words
    words = [word for word in words if not re.search(r'(.)\1{2,}', word) and not re.match(r'^\d+$', word)]

    # Filter words using the spell checker and dictionary
    recognized_words = [word for word in words if word in spell]

    # Join the recognized words back into a string
    return ' '.join(recognized_words)

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

            # Try extracting text as typed
            text = extract_text_typed(input_image_path)

            # If no text found, try extracting as handwritten
            if not text:
                text = extract_text_handwritten(input_image_path)

            # Filter out unrecognized words
            filtered_text = filter_recognized_words(text)

            if filtered_text:  # If any recognized text is detected
                # Format the text for CSV output
                formatted_text = f'includes the text: "{filtered_text}"'
                csv_rows.append([filename, formatted_text])
            else:
                # If no text is detected, leave the column empty
                csv_rows.append([filename, "No text detected"])

    # Sort the rows alphabetically by filename (first column)
    csv_rows.sort(key=lambda x: x[0].lower())  # Sort case-insensitively

    # Write the transcriptions to a CSV file with UTF-8 encoding
    csv_output_path = os.path.join(output_folder, output_csv)
    with open(csv_output_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file)
        # Write the header
        writer.writerow(['Filename', 'Transcribed Text'])

        # Write the rows
        for row in csv_rows:
            # Only write the transcribed text without additional quotes
            writer.writerow([row[0], row[1].replace('"', '')])  # Remove extra quotes

    print(f"Saved transcriptions to {csv_output_path}")

if __name__ == "__main__":
    # Set the correct paths for Folder A (input images) and Folder B (output CSV)
    input_folder = "A"  # Relative path to Folder A
    output_folder = "B"  # Relative path to Folder B
    output_csv = "transcriptions.csv"

    process_images(input_folder, output_folder, output_csv)
