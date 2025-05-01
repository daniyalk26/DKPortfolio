import os
import re

INPUT_DIR = "/Users/celinecerezci/downloads/DS4300NotesTXT" 
OUTPUT_DIR = "/Users/celinecerezci/downloads/processed"  
CHUNK_SIZES = [200, 500, 1000]  
OVERLAP_SIZES = [0, 50, 100]

def read_file(file_path):
    """
    reads a .txt file and returns its text content
    """

    # confirm that code is reading the folder
    print(f"trying to read: {file_path}")  

    # open and read files
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"error reading file {file_path}: {e}")
        return ""

def clean_text(text):
    """
    lowercasing, remove punctuation, and extra whitespace
    """
    # lowercase
    text = text.lower()
    # remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())
    return text

def tokenize(text):
    """
    split on whitespace to tokenize words
    """
    return text.split()

def chunk_tokens(tokens, chunk_size, overlap):
    """
    creates segments from lists of tokens of given size with a specified overlap
    """
    # list to store chunks
    chunks = []
    n = len(tokens)
    # calculate number of tokens
    step = max(chunk_size - overlap, 1)
    # loop over tokens
    for i in range(0, n, step):
        # create chunk
        chunk = tokens[i:i + chunk_size]
        if chunk:
            chunks.append(" ".join(chunk))
    return chunks

def process_file(file_path, chunk_sizes, overlaps):
    """
    reads and processes a file; generating chunks
    """
    # read file
    raw_text = read_file(file_path)

    # clean text and tokenzize
    cleaned = clean_text(raw_text)
    tokens = tokenize(cleaned)

    # initialize chunk dictionary
    chunks_dictionary = {}

    # loop over each chunk size
    for size in chunk_sizes:
        for overlap in overlaps:
            # create key as chunk size, overlap
            key = (size, overlap)
            # generate chunks
            chunks = chunk_tokens(tokens, size, overlap)
            # store list of chunks
            chunks_dictionary[key] = chunks
    return chunks_dictionary

def main():
    """
    processes each .txt file from input directory and writes the output into subfolders based on chunk and overlap sizes
    """

    # for loop that goes trough all sub-directories and files
    for root, dirs, files in os.walk(INPUT_DIR):
        # iterates over each file
        for filename in files:
            # process only .txt files
            if filename.lower().endswith(".txt"):
                # make the full path to the text file
                file_path = os.path.join(root, filename)

                # chunks based on different sizes/overlaps
                chunks_dictionary = process_file(file_path, CHUNK_SIZES, OVERLAP_SIZES)
                
                # find path from input directory
                rel_path = os.path.relpath(root, INPUT_DIR)
                # create directory/path in the output directory
                out_subdir = os.path.join(OUTPUT_DIR, rel_path)
                os.makedirs(out_subdir, exist_ok=True)

                # extract file name for organization reasons
                base_name = os.path.splitext(filename)[0]

                # loop through various configurations
                for (chunk_size, overlap), chunks in chunks_dictionary.items():
                    # create folder name
                    config_folder = f"{chunk_size} -- {overlap}"

                    # create subdirectory
                    config_subdir = os.path.join(out_subdir, config_folder)
                    os.makedirs(config_subdir, exist_ok=True)

                    # make the file name
                    out_filename = f"{base_name}_{chunk_size}_{overlap}.txt"
                    out_path = os.path.join(config_subdir, out_filename)

                    # open file
                    with open(out_path, "w", encoding="utf-8") as f:
                        for chunk in chunks:
                            f.write(chunk + "\n\n")

if __name__ == "__main__":
    main()
