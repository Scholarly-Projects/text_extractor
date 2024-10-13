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
        # Resize the image slightly
        img = img.resize((int(img.width * 1.1), int(img.height * 1.1)), Image.LANCZOS)  # Increase size by 10%

        # Convert to grayscale
        img = img.convert('L')
        # Apply a Gaussian blur to reduce noise
        img = img.filter(ImageFilter.GaussianBlur(1))
        # Binarize the image (thresholding)
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        return img

# Function to calculate text density
def calculate_text_density(image):
    # Convert to black and white to count pixels
    bw_image = image.convert('1')  # Convert to binary (black and white)
    total_pixels = bw_image.size[0] * bw_image.size[1]
    text_pixels = sum(1 for pixel in bw_image.getdata() if pixel == 0)  # Count black pixels (text)

    return text_pixels / total_pixels if total_pixels > 0 else 0

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

# Function to extract text using the eng+handwriting model
def extract_text(image_path, attempt=1, max_attempts=3):
    try:
        img = preprocess_image(image_path)
        text = pytesseract.image_to_string(img, lang='eng+handwriting', config='--psm 6').strip()

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
    
    # Filter out common nonsensical words or excessive gibberish
    words = [word for word in words if len(word) > 2 and len(set(word)) > 1]  # Requires more than one unique character

    # Filter words using the spell checker and dictionary
    recognized_words = [word for word in words if word in spell]

    # Join the recognized words back into a string
    return ' '.join(recognized_words)

# Function to check if the image likely contains meaningful text
def is_text_image(image):
    # Calculate the text density
    density_threshold = 0.2  # You can adjust this threshold
    density = calculate_text_density(image)

    return density >= density_threshold

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

            # Extract text using the eng+handwriting model, with rescan for nonsensical results
            text = extract_text(input_image_path)

            # Open image to check if it likely contains text
            with Image.open(input_image_path) as img:
                if is_text_image(img):
                    # Filter out unrecognized words
                    filtered_text = filter_recognized_words(text)

                    if filtered_text:  # If any recognized text is detected
                        # Format the text for CSV output
                        formatted_text = f'includes the text: "{filtered_text}"'
                        csv_rows.append([filename, formatted_text])
                    else:
                        # If no text is detected, leave the column empty
                        csv_rows.append([filename, "No text detected"])
                else:
                    print(f"Skipped {filename}: Not enough text density.")
                    csv_rows.append([filename, "Not enough text density"])

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
