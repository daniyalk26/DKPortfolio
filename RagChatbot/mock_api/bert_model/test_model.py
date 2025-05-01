import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.preprocessing import LabelEncoder
import joblib

# Load the trained model and tokenizer
model = AutoModelForSequenceClassification.from_pretrained('fine-tuned-bert')
tokenizer = AutoTokenizer.from_pretrained('fine-tuned-bert')

# Load the label encoder
label_encoder = joblib.load('label_encoder.joblib')

# Function to make predictions
def predict_intent(texts):
    # Tokenize input texts
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True)
    
    # Ensure model is in evaluation mode
    model.eval()
    
    # Move inputs to the same device as the model
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    
    # Make predictions
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get the predicted label indices
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=-1)
    
    # Decode the predicted label indices to intent labels
    predicted_labels = label_encoder.inverse_transform(predictions.cpu().numpy())
    
    return predicted_labels

# Example usage
if __name__ == "__main__":
    sample_texts = ["How much is in BOA", 
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

    predicted_intents = predict_intent(sample_texts)
    for text, intent in zip(sample_texts, predicted_intents):
        print(f"Text: {text}\nPredicted Intent: {intent}\n")
