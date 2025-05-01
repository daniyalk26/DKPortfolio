import pickle

from tensorflow.keras.models import load_model, model_from_json
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences
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


with open('utils/classesv2.pkl','rb') as file:
  classes = pickle.load(file)

with open('utils/tokenizerv2.pkl','rb') as file:
  tokenizer = pickle.load(file)

with open('utils/label_encoderv2.pkl','rb') as file:
  label_encoder = pickle.load(file)

# Load model architecture
with open('models/modelv2_architecture.json', 'r') as json_file:
    model_json = json_file.read()
intent_model = model_from_json(model_json)

# Load model weights
intent_model.load_weights('models/modelv2.weights.h5')

# Compile the model (necessary to load weights properly)
intent_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['acc'])

nlu = IntentClassifier(classes,intent_model,tokenizer,label_encoder)

test_queries = ["How much is in BOA", 
                "Can you tell me more about ewa", 
                "How do I withdraw cash from my earned wages", 
                "What does payactiv do?",
                "Can you help me with transfering money"
                "How much is in my account with id 5",
                "What was the last transaction in my Chase account",
                "How do I report my card as lost",
                "How do I get a new payactiv card",
                "I want to open a ticket",
                "Can I talk to customer service",
                "How is the weather outside",
                "What's my credit score looking like"]

for text in test_queries:
   print(text)
   print(nlu.get_intent(text))
   print("\n")
