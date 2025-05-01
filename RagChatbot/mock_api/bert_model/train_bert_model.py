import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments, DataCollatorWithPadding, AutoTokenizer
import joblib

# Load the dataset
df = pd.read_csv('mock_data.csv')

# Combine text into one column and create intent column from titles
df_melted = df.melt(var_name="intent", value_name="text").dropna()
texts = df_melted["text"].tolist()
intents = df_melted['intent'].tolist()

# Encode intents
label_encoder = LabelEncoder()
df_melted['label'] = label_encoder.fit_transform(df_melted['intent'])

# Save the label encoder
joblib.dump(label_encoder, 'label_encoder.joblib')

# Split data into train and test
train_df, test_df = train_test_split(df_melted, test_size=0.2)

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

# Tokenize data
def tokenize_data(examples):
    return tokenizer(examples["text"], truncation=True, padding=True)

# Convert to Dataset object and tokenize
train_dataset = Dataset.from_pandas(train_df)
test_dataset = Dataset.from_pandas(test_df)

tokenized_train = train_dataset.map(tokenize_data, batched=True)
tokenized_test = test_dataset.map(tokenize_data, batched=True)

# Remove unnecessary columns
tokenized_train = tokenized_train.remove_columns(['text', 'intent'])
tokenized_test = tokenized_test.remove_columns(['text', 'intent'])

# Set the format for PyTorch tensors
tokenized_train.set_format("torch")
tokenized_test.set_format("torch")

# Load pre-trained DistilBERT model for sequence classification
num_labels = len(label_encoder.classes_)
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=num_labels)

# Prepare data collator for padding sequences
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=2e-4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=10,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    logging_strategy="epoch"
)

# Define Trainer object for training the model
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_test,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

# Train the model
trainer.train()

# Save the trained model
trainer.save_model('fine-tuned-bert')
