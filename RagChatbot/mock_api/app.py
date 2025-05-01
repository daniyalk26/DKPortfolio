from flask import Flask, jsonify, request, render_template, send_from_directory, Response
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import pandas as pd
import numpy as np
import tempfile
import os
import pickle
from pydub import AudioSegment
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from pinecone_text.sparse import BM25Encoder
from tensorflow.keras.models import load_model, model_from_json
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
import speech_recognition as sr
from openai import OpenAI
import io
import numpy as np
import requests
from dotenv import load_dotenv
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments, DataCollatorWithPadding, AutoTokenizer
import joblib
import torch

class IntentClassifier:
    def __init__(self,classes,model,tokenizer,label_encoder):
        self.classes = classes
        self.classifier = model
        self.tokenizer = tokenizer
        self.label_encoder = label_encoder

    def get_intent(self,text):
        self.text = [text]
        self.test_keras = self.tokenizer.texts_to_sequences(self.text)
        self.test_keras_sequence = pad_sequences(self.test_keras, maxlen=16, padding='post')
        self.pred = self.classifier.predict(self.test_keras_sequence)
        return self.label_encoder.inverse_transform(np.argmax(self.pred,1))[0]

load_dotenv()
app = Flask(__name__, static_folder='www')
CORS(app)
model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)
openai_key = os.getenv('OPENAI_API_KEY')
pinecone_key = os.getenv('PINECONE_API_KEY')
recognizer = sr.Recognizer()
client = OpenAI(
    api_key=openai_key
)
pc = Pinecone(api_key=pinecone_key)
chat_index = "payactiv-chatbot-index"
hybrid_index = "payactiv-hybrid-index"

df = pd.read_csv('embeddings.csv')
df = df.drop_duplicates(subset='Url', keep='first')

bm25 = BM25Encoder()
bm25.fit(df['Text'].tolist())


# with open('utils/classes.pkl','rb') as file:
#   classes = pickle.load(file)

# with open('utils/tokenizer.pkl','rb') as file:
#   tokenizer = pickle.load(file)

# with open('utils/label_encoder.pkl','rb') as file:
#   label_encoder = pickle.load(file)

# # Load model architecture
# with open('models/model_architecture.json', 'r') as json_file:
#     model_json = json_file.read()
# intent_model = model_from_json(model_json)

# # Load model weights
# intent_model.load_weights('models/model.weights.h5')

# # Compile the model (necessary to load weights properly)
# intent_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['acc'])

# nlu = IntentClassifier(classes,intent_model,tokenizer,label_encoder)

# Load the trained model and tokenizer at startup
intent_model = AutoModelForSequenceClassification.from_pretrained('./bert_model/fine-tuned-bert')
tokenizer = AutoTokenizer.from_pretrained('./bert_model/fine-tuned-bert')

# Load the label encoder
label_encoder = joblib.load('./bert_model/label_encoder.joblib')

# Ensure model is in evaluation mode
intent_model.eval()



# Sample data
accounts = {
    "totalAmount": 985.0,
    "assets": [
        {
            "id": 1,
            "title": "Accessible Earnings",
            "amount": 280.0,
            "assetType": 1,
            "imageURL": "AccessibleEarnings",
            "instrumentRemoteReferenceID": "0",
            "instrumentType": 6,
            "instrumentSubType": 0,
            "canFetchBalance": False,
            "cardDesign": "",
            "cardColorCode": "",
            "reconnectAccount": False,
            "cardID": 0,
            "productNotReady": False,
            "referenceCardDesignID": 0,
            "bankType": 0,
            "cardStatus": 0,
            "isBankLinkedWithAccessPlus": False,
            "disablePayAFriend": False,
            "disablePayBill": False,
            "disableAddFunds": False,
            "isCardActivatedAfterApproval": False,
            "directCardApprovalStatus": 0,
            "manualBankStatus": 0,
            "description": None,
            "status": 2,
            "isPlaidBank": False,
            "productsNotSupported": False
        },
        {
            "id": 2,
            "title": "Payactiv Rewards",
            "amount": 0.0,
            "assetType": 1,
            "imageURL": "Reward",
            "instrumentRemoteReferenceID": "0",
            "instrumentType": 0,
            "instrumentSubType": 0,
            "canFetchBalance": False,
            "cardDesign": "",
            "cardColorCode": "",
            "reconnectAccount": False,
            "cardID": 0,
            "productNotReady": False,
            "referenceCardDesignID": 0,
            "bankType": 0,
            "cardStatus": 0,
            "isBankLinkedWithAccessPlus": False,
            "disablePayAFriend": False,
            "disablePayBill": False,
            "disableAddFunds": False,
            "isCardActivatedAfterApproval": False,
            "directCardApprovalStatus": 0,
            "manualBankStatus": 0,
            "description": "",
            "status": 2,
            "isPlaidBank": False,
            "productsNotSupported": False
        },
        {
            "id": 12835,
            "title": "Payactiv Card 8899",
            "amount": 5.0,
            "assetType": 2,
            "imageURL": "PayActivCard",
            "instrumentRemoteReferenceID": "13189",
            "instrumentType": 2,
            "instrumentSubType": 1,
            "canFetchBalance": True,
            "cardDesign": "White",
            "cardColorCode": "FFFFFF",
            "reconnectAccount": False,
            "cardID": 5939,
            "productNotReady": False,
            "referenceCardDesignID": 1012,
            "bankType": 0,
            "cardStatus": 1,
            "isBankLinkedWithAccessPlus": False,
            "disablePayAFriend": False,
            "disablePayBill": False,
            "disableAddFunds": True,
            "isCardActivatedAfterApproval": True,
            "directCardApprovalStatus": 0,
            "manualBankStatus": 0,
            "description": "Last transaction: $0.00",
            "status": 2,
            "isPlaidBank": False,
            "productsNotSupported": False
        },
        {
            "id": 31503,
            "title": "Bank of America - 1111",
            "amount": 200.0,
            "assetType": 2,
            "imageURL": "BankAccount",
            "instrumentRemoteReferenceID": "81972",
            "instrumentType": 1,
            "instrumentSubType": 0,
            "canFetchBalance": True,
            "cardDesign": None,
            "cardColorCode": None,
            "reconnectAccount": False,
            "cardID": 0,
            "productNotReady": False,
            "referenceCardDesignID": 0,
            "bankType": 5,
            "cardStatus": 0,
            "isBankLinkedWithAccessPlus": False,
            "disablePayAFriend": False,
            "disablePayBill": False,
            "disableAddFunds": True,
            "isCardActivatedAfterApproval": False,
            "directCardApprovalStatus": 0,
            "manualBankStatus": 0,
            "description": "Last transaction: $25.00",
            "status": 2,
            "isPlaidBank": True,
            "productsNotSupported": False
        },
        {
            "id": 31737,
            "title": "Chase - 1111",
            "amount": 200.0,
            "assetType": 2,
            "imageURL": "BankAccount",
            "instrumentRemoteReferenceID": "81988",
            "instrumentType": 1,
            "instrumentSubType": 0,
            "canFetchBalance": True,
            "cardDesign": None,
            "cardColorCode": None,
            "reconnectAccount": True,
            "cardID": 0,
            "productNotReady": False,
            "referenceCardDesignID": 0,
            "bankType": 1,
            "cardStatus": 0,
            "isBankLinkedWithAccessPlus": False,
            "disablePayAFriend": False,
            "disablePayBill": False,
            "disableAddFunds": True,
            "isCardActivatedAfterApproval": False,
            "directCardApprovalStatus": 0,
            "manualBankStatus": 0,
            "description": "Last transaction: $0.00",
            "status": 2,
            "isPlaidBank": True,
            "productsNotSupported": False
        },
        {
            "id": 40772,
            "title": "Chase  - 1111",
            "amount": 200.0,
            "assetType": 2,
            "imageURL": "BankAccount",
            "instrumentRemoteReferenceID": "84735",
            "instrumentType": 1,
            "instrumentSubType": 0,
            "canFetchBalance": True,
            "cardDesign": None,
            "cardColorCode": None,
            "reconnectAccount": True,
            "cardID": 0,
            "productNotReady": False,
            "referenceCardDesignID": 0,
            "bankType": 1,
            "cardStatus": 0,
            "isBankLinkedWithAccessPlus": False,
            "disablePayAFriend": False,
            "disablePayBill": False,
            "disableAddFunds": True,
            "isCardActivatedAfterApproval": False,
            "directCardApprovalStatus": 0,
            "manualBankStatus": 0,
            "description": "Last transaction: $0.00",
            "status": 2,
            "isPlaidBank": True,
            "productsNotSupported": False
        },
        {
            "id": 44422,
            "title": "Chase  - 0000",
            "amount": 100.0,
            "assetType": 2,
            "imageURL": "BankAccount",
            "instrumentRemoteReferenceID": "86618",
            "instrumentType": 1,
            "instrumentSubType": 0,
            "canFetchBalance": True,
            "cardDesign": None,
            "cardColorCode": None,
            "reconnectAccount": False,
            "cardID": 0,
            "productNotReady": False,
            "referenceCardDesignID": 0,
            "bankType": 1,
            "cardStatus": 0,
            "isBankLinkedWithAccessPlus": False,
            "disablePayAFriend": False,
            "disablePayBill": False,
            "disableAddFunds": True,
            "isCardActivatedAfterApproval": False,
            "directCardApprovalStatus": 0,
            "manualBankStatus": 0,
            "description": "Last transaction: $89.40",
            "status": 2,
            "isPlaidBank": True,
            "productsNotSupported": False
        }
    ],
    "availableOptions": [
        {
            "optionName": "Saving",
            "isAvailable": True,
            "title": "Start saving today",
            "description": "Create a goal!",
            "imageName": "Saving-Default",
            "availableOptionsType": 12,
            "displayOrder": 3
        }
    ]
}

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api')
def home():
    return render_template('index.html', assets=accounts['assets'])

# API to get all user accounts and balances
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    return jsonify(accounts)

@app.route('/api/transfer', methods=['POST'])
def transfer_money():
    data = request.json
    from_id = data['from']
    to_id = data['to']
    amount = data['amount']
    
    from_account = next((a for a in accounts['assets'] if a['id'] == from_id), None)
    to_account = next((a for a in accounts['assets'] if a['id'] == to_id), None)
    
    if not from_account or not to_account:
        return jsonify({"message": "Invalid account"}), 400
    
    if from_account['amount'] < amount:
        return jsonify({"message": "Insufficient funds"}), 400

    from_account['amount'] -= amount
    to_account['amount'] += amount

    return jsonify({"message": "$" + str(amount) + " Successfully Transferred from " + from_account['title'] + " to " + to_account['title']})

@app.route('/api/weather', methods=['POST'])
def weather():
    # http://api.weatherapi.com/v1/current.json?key=<YOUR_API_KEY>&q=London
    return jsonify({"message": "It is currently 80 F in milpitas"})

@app.route('/api/semantic_search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    if query:
        results = semantic_search(query)
        # Convert results to JSON serializable format
        return jsonify(results)
    else:
        return jsonify({"error": "No query provided"}), 400

def semantic_search(query):
    # df = pd.read_csv('embeddings.csv')
    # embedding = model.encode(query)
    # sim_arr = []
    # for index, row in df.iterrows():
    #     sim_arr.append({
    #         "similarity": cos_sim(embedding, eval(row['Embedding'])),
    #         "text": row['Text']
    #     })
    # sim_arr = sorted(sim_arr, key=lambda x: x['similarity'], reverse=True)
    # return sim_arr[0]["text"] + '\n' + sim_arr[1]["text"]
    index = pc.Index(hybrid_index)
    embedding = model.encode(query).tolist()
    sparse_vec = bm25.encode_queries(query)
    result = index.query(namespace="", vector=embedding, sparse_vector=sparse_vec, top_k=2, include_metadata=True)

    matches = result['matches']
    output = []
    for match in matches:
        output.append(match['metadata']['text'])

    return '\n'.join(output)

@app.route('/api/dynamic_answer', methods=['POST'])
def dynamic_answer():
    data = request.json
    query = data.get('query')
    if query:
        embedding = model.encode(query).tolist()
        index = pc.Index(chat_index)
        result = index.query(namespace="dynamic-qa", vector=embedding, top_k=1, include_metadata=True)
        arr = result['matches']
        if len(arr) == 0:
            return jsonify({"error": "error fetching dynamic answers"}), 400

        output = 'Other'
        if arr[0]['score'] > 0.7:
            output = arr[0]['metadata']['class']
        # Convert results to JSON serializable format
        return jsonify(output), 200
    else:
        return jsonify({"error": "No query provided"}), 400

@app.route('/api/fetch_intent', methods=['POST'])
def fetch_intent():
    data = request.json
    print(data)
    query = data.get('query')
    if query:
        # result = nlu.get_intent(query)
        result = predict_intent(query)
        return jsonify(result)
    else: 
        return jsonify({"error": "No query provided"}), 400
    
def predict_intent(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {key: value.to(intent_model.device) for key, value in inputs.items()}
    
    with torch.no_grad():
        outputs = intent_model(**inputs)
    
    logits = outputs.logits
    prediction = torch.argmax(logits, dim=-1)
    predicted_label = label_encoder.inverse_transform(prediction.cpu().numpy())[0]
    
    return predicted_label
    
def convert_m4a_to_wav(file_path):
    try:
        audio_segment = AudioSegment.from_file(file_path, format="m4a")
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        return wav_io
    except Exception as e:
        print(f'FFmpeg conversion failed: {e}')
        return None

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_audio_file:
            file.save(temp_audio_file.name)
            temp_audio_file_path = temp_audio_file.name

        # Convert using pydub and ffmpeg
        audio_segment = AudioSegment.from_file(temp_audio_file_path)
        
        temp_dir = os.path.join(tempfile.gettempdir(), "tmp")
        os.makedirs(temp_dir, exist_ok=True)
        wav_file_path = os.path.join(temp_dir, 'temp.wav')
        
        audio_segment.export(wav_file_path, format="wav")

        voice = True
        if voice:
            with sr.AudioFile(wav_file_path) as source:
                audio_data = recognizer.listen(source)
            recognizer.recognize_google(audio_data) # Google recognition helps prevent ghost text from being detected by trhowing UnknownValueError
            text = recognizer.recognize_whisper_api(audio_data, api_key=openai_key)
            response = jsonify({'text': text})
        else:
            response = jsonify({'error': 'No voice detected'}), 201

        # Clean up the temporary files
        os.remove(temp_audio_file_path)
        os.remove(wav_file_path)

        return response

    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand the audio'}), 201
    except sr.RequestError as e:
        return jsonify({'error': f'Speech recognition error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
@app.route('/api/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('input')
    
    if not text:
        return jsonify({"error": "Text is required"}), 400

    openai_request_body = {
        'model': 'tts-1',
        'input': text,
        'voice': "nova",
    }

    try:
        openai_response = requests.post(
            'https://api.openai.com/v1/audio/speech',
            headers={
                'Authorization': f'Bearer {openai_key}',
                'Content-Type': 'application/json',
            },
            json=openai_request_body
        )

        if openai_response.status_code != 200:
            return jsonify({"error": f"OpenAI API error: {openai_response.status_text}"}), openai_response.status_code

        return Response(openai_response.content, mimetype='audio/wav')

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# def tts2():
#     device = "cuda" if torch.cuda.is_available() else "cpu"

#     # List available 🐸TTS models
#     print(TTS().list_models())

#     # Init TTS
#     tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

#     # Run TTS
#     # ❗ Since this model is multi-lingual voice cloning model, we must set the target speaker_wav and language
#     # Text to speech list of amplitude values as output
#     wav = tts.tts(text="Hello world!", speaker_wav="my/cloning/audio.wav", language="en")
#     # Text to speech to a file
#     tts.tts_to_file(text="Hello world!", speaker_wav="my/cloning/audio.wav", language="en", file_path="output.wav")
        
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get("messages")

    tools = [
          {
            "type": "function",
            "function": {
                "name": "transfer_money",
                "description": "Transfer money between two accounts. Accounts can have any balance including $0",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_from_id": {
                            "type": "integer",
                            "description": "The description of the account to transfer amount from must be explicitly mentioned by use.",
                        },
                        "account_to_id": {
                            "type": "integer",
                            "description": "The description of the account to transfer amount to must be explicitly mentioned by user.",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Amount of money to transfer",
                        }
                    },
                    "required": ["account_from_id", "account_to_id", "amount"],
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        tools=tools,
        messages=messages,
        max_tokens=1000,
        n=1,
        temperature=0,
        parallel_tool_calls=False
    )    
    data = response.model_dump_json()
    
    return jsonify(data), 200

@app.route('/api/save-data', methods=['POST'])
def save_data():
    try:
        # Get the JSON data from the request
        data = json.loads(request.data)
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Define the path to the JSON file
        file_path = 'database/saved_data.json'

        # Load existing data if the file exists
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                existing_data = json.load(json_file)
        else:
            existing_data = []

        # Append the new data to the existing data
        existing_data.append(data)
        # Write the updated data to the JSON file
        with open(file_path, 'w') as json_file:
            json.dump(existing_data, json_file, indent=4)
        return jsonify({"message": "Data saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)