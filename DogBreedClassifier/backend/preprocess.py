import os
import xml.etree.ElementTree as ET
from PIL import Image

# Define directories (relative to the script location)
annotations_dir = "dataset/Annotation"
images_dir = "dataset/Images"
output_dir = "processed_new_new_images"

print("🔁 Script started.")

# Ensure output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"📁 Created output directory: {output_dir}")
else:
    print(f"📁 Output directory already exists: {output_dir}")

def process_annotation(xml_file):
    """
    Parse a single annotation XML file to extract relevant details.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Get folder info and ensure it matches the expected image folder naming
    folder_from_xml = root.find('folder').text
    # Prepend 'n' if missing (so "02085620" becomes "n02085620")
    if not folder_from_xml.startswith("n"):
        folder_from_xml = "n" + folder_from_xml

    # Get the filename without extension (as given in the annotation)
    filename = root.find('filename').text
    breed = root.find("object/name").text

    # Extract bounding box coordinates
    bndbox = root.find("object/bndbox")
    xmin = int(bndbox.find("xmin").text)
    ymin = int(bndbox.find("ymin").text)
    xmax = int(bndbox.find("xmax").text)
    ymax = int(bndbox.find("ymax").text)

    return folder_from_xml, filename, breed, (xmin, ymin, xmax, ymax)

def preprocess_images():
    print("🚀 Starting preprocessing...")

    # Recursively collect all annotation XML files.
    # Also allow files with no extension in case any annotations lack a '.xml'
    xml_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(annotations_dir)
        for file in files if file.lower().endswith('.xml') or '.' not in file
    ]

    if not xml_files:
        print("⚠️ No annotation files found. Please check the dataset path.")
        return

    print(f"📄 Found {len(xml_files)} annotation files.")

    for xml_file in xml_files:
        try:
            folder_from_xml, filename, breed, bbox = process_annotation(xml_file)
        except Exception as e:
            print(f"❌ Error parsing {xml_file}: {e}")
            continue

        # Build the expected image folder name using the folder and breed information.
        image_folder_name = f"{folder_from_xml}-{breed}"
        # Append ".jpg" to the filename as it's missing in the annotation.
        image_path = os.path.join(images_dir, image_folder_name, filename + ".jpg")

        if not os.path.exists(image_path):
            print(f"⚠️ Image not found: {image_path}")
            continue

        try:
            with Image.open(image_path) as img:
                # Crop the image with the bounding box and resize to 224x224
                cropped_img = img.crop(bbox)
                resized_img = cropped_img.resize((300, 300))

                # Make sure the output breed folder exists
                breed_folder = os.path.join(output_dir, breed)
                os.makedirs(breed_folder, exist_ok=True)

                output_path = os.path.join(breed_folder, filename + ".jpg")
                resized_img.save(output_path)
                print(f"✅ Saved: {output_path}")
        except Exception as e:
            print(f"❌ Error processing image {image_path}: {e}")

if __name__ == "__main__":
    preprocess_images()
