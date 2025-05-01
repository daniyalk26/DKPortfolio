# DS-4300 Practical 2: Chapin Wilson, Celine Cerezci, Joji Araki, Daniyal Khalid

# Overview

This repository implements Llama and DeepSeek to create a custom LLM using our team's notes for DS4300 as data. There are 4 python files in this repository: preprocess.py, compare.py, main.py, and model.py. The 3 python files that are necessary to run are preprocess.py, compare.py, and main.py. Model.py was used to compare embedding models with test data.

# Installation

- Ensure you are using Python 3.11. You can check this using the following command:
python --version
- Ensure you have downloaded Ollama, Docker, Redis, Llama3.2 and DeepSeek DeepSeek-r1:1.5b.

# Implementation

## Step 1: Preprocessing the data
To begin, make sure you have DS4300NotesTXT downloaded in your directory of choice. Then, head to preprocess.py. This code will save a new folder called "processed" to your directory of choice. In preprocces.py, change the variable "INPUT_DIR" to your directory that contains the downloaded DS4300NotesTXT folder. Change the "OUTPUT_DIR" variable to your directory of choice, but make sure the folder name is still named "processed". Run the code.

## Step 2: Ingesting the Data

After preprocessing the data, head to compare.py. This Python file ingests documents, generates embeddings using a pre-trained language model, and indexes/queries them using three different vector search engines. Update the "folder_path" variable to the pathway of your desired preprocessed dataset:
- For example, if you would like to ingest data in chunks of 500 terms with an overlap of 50, your folder path would resemble this: /path/to/project/preprocess/500 -- 50
Additionally, change the "file_pattern" variable to match your chunk/overlap size selection:
- For example, if you would like to ingest data in chunks of 500 terms with an overlap of 50, your file pattern would resemble this: os.path.join(folder_path, "*_chunk_500_overlap_50.txt")
  - Simply change the numbers "500" and "50" if you would like to use a different chunk or overlap size

At this point, you should open Docker and run a Redis stack. Update the port number on this line as needed: 
redis_client = redis.Redis(host='localhost', port=6383)

Now, run compare.py.

## Step 3: Running main.py

main.py retrieves text passages from a Redis-based vector index and then uses those passages to build a context-specific prompt for a local language model. Update the port number on this line as needed with the necessary port number: 

redis_client = redis.Redis(host='localhost', port=6383)

Run main.py. The terminal should prompt you to enter a query. You can now query the model for anything related to DS4300 conten. 


# Citations
Mark Fontenot's Website Resources 
https://markfontenot.net/teaching/ds4300/25s-ds4300/

StackOverFlow for general code suggestions

OpenSource AI models including deepseek, OpenAI, Perplexity, ChatGPT
Uses include greater clarification on subjects, he debugging, and for assistance when it comes to
preprocessing.
