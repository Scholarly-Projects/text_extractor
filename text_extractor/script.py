import os
import pytesseract
import cv2
import numpy as np
import csv
from spellchecker import SpellChecker
import re

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  # Adjust this if necessary

# Initialize the SpellChecker
spell = SpellChecker()

# Function to preprocess the image using OpenCV for better OCR results
def preprocess_image(image_path):
    # Read the image using OpenCV
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    
    # Resize the image slightly to make it larger
    img = cv2.resize(img, (int(img.shape[1] * 1.1), int(img.shape[0] * 1.1)), interpolation=cv2.INTER_LINEAR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply thresholding for binarization
    _, thresh_img = cv2.threshold(blurred, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh_img

# Function to save the first preprocessed image as example_image.png
def save_example_image(image_path, output_folder):
    preprocessed_img = preprocess_image(image_path)
    example_image_path = os.path.join(output_folder, 'example_image.png')
    cv2.imwrite(example_image_path, preprocessed_img)
    print(f"Example image saved as {example_image_path}")

# Function to merge new recognized words into existing text
def merge_text(existing_text, new_text):
    if not existing_text:
        return new_text.strip()
    
    # Split existing text and new text into word lists
    existing_words = set(existing_text.split())
    new_words = set(new_text.split())

    # Combine both sets of words
    combined_words = existing_words.union(new_words)

    # Reconstruct text from combined words
    combined_text = ' '.join(combined_words)
    return combined_text.strip()

# Function to extract text using Tesseract OCR
def extract_text(image_path, attempt=1, max_attempts=3):
    try:
        img = preprocess_image(image_path)
        # Convert the image array back to PIL Image for compatibility with Tesseract
        # Use psm 12 for table/column recognition
        text = pytesseract.image_to_string(img, lang='eng+handwriting', config='--psm 12').strip()

        if not text:
            return text
        
        return text

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return ""

# Function to filter out unrecognized words from extracted text
def filter_recognized_words(text):
    # Allow single characters followed by a period (like U.S.D.A)
    text = re.sub(r'(?<=\b[A-Za-z]\.)[A-Za-z]', '', text)  # Remove trailing letters after a period

    # Remove unwanted characters while retaining common punctuation
    text = re.sub(r'[^a-zA-Z0-9\s.,;\'"?!-]', '', text)  # Keep letters, numbers, spaces, and some punctuation

    # Split the text into words
    words = text.split()

    # Length filtering: Discard words shorter than 3 characters or longer than 15 characters
    words = [word for word in words if 3 <= len(word) <= 15]

    # Pattern filtering: Discard repeated characters, numeric-only words, and gibberish
    words = [word for word in words if not re.search(r'(.)\1{2,}', word) and not re.match(r'^\d+$', word)]
    
    # Filter words using the spell checker
    recognized_words = [word for word in words if word in spell]

    # Join the recognized words back into a string
    return ' '.join(recognized_words)

# Function to process images in folder A and export transcriptions to a CSV file in folder B
def process_images(input_folder, output_folder, output_csv):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    csv_rows = []
    first_image_path = None

    # Iterate through each file in the input folder
    for filename in sorted(os.listdir(input_folder)):
        if filename.lower().endswith((".png", ".tiff", ".jpg", ".jpeg")):
            input_image_path = os.path.join(input_folder, filename)
            print(f"Processing {filename}...")

            # Set the first image for saving an example
            if first_image_path is None:
                first_image_path = input_image_path

            # Extract text using Tesseract OCR
            text = extract_text(input_image_path)

            # Filter out unrecognized words
            filtered_text = filter_recognized_words(text)

            if filtered_text:  # If any recognized text is detected
                # Format the text for CSV output
                formatted_text = f'includes the text: "{filtered_text}"'
                csv_rows.append([filename, formatted_text])
            else:
                # If no text is detected, leave the column empty
                csv_rows.append([filename, "No text detected"])

    # Save an example image for visual inspection
    if first_image_path:
        save_example_image(first_image_path, output_folder)

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
