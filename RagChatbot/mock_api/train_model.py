import numpy as np
import json
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, LSTM, Bidirectional, Embedding
import os
import pickle

# Ensure directories exist
os.makedirs('models', exist_ok=True)
os.makedirs('utils', exist_ok=True)


# Load synthetic dataset
with open('new_synthetic_data.json') as file:
    data = json.loads(file.read())

# Loading out-of-scope intent data
val_oos = np.array(data['oos_val'])
train_oos = np.array(data['oos_train'])
test_oos = np.array(data['oos_test'])

# Loading other intents data
val_others = np.array(data['val'])
train_others = np.array(data['train'])
test_others = np.array(data['test'])

# Merging out-of-scope and other intent data
val = np.concatenate([val_oos, val_others])
train = np.concatenate([train_oos, train_others])
test = np.concatenate([test_oos, test_others])
all_data = np.concatenate([train, test, val])

# Split data into text and labels
text = all_data[:, 0]
labels = all_data[:, 1]

# Split data into training and test sets
train_txt, test_txt, train_label, test_labels = train_test_split(text, labels, test_size=0.3)
max_num_words = 40000
classes = np.unique(labels)

tokenizer = Tokenizer(num_words=max_num_words)
tokenizer.fit_on_texts(train_txt)
word_index = tokenizer.word_index

ls = [len(c.split()) for c in train_txt]
maxLen = int(np.percentile(ls, 98))
train_sequences = tokenizer.texts_to_sequences(train_txt)
train_sequences = pad_sequences(train_sequences, maxlen=maxLen, padding='post')
test_sequences = tokenizer.texts_to_sequences(test_txt)
test_sequences = pad_sequences(test_sequences, maxlen=maxLen, padding='post')

# Assign integers to each class
label_encoder = LabelEncoder()
integer_encoded = label_encoder.fit_transform(classes)

onehot_encoder = OneHotEncoder(sparse_output=False)  # Ensure the output is dense
integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
onehot_encoder.fit(integer_encoded)
train_label_encoded = label_encoder.transform(train_label)
train_label_encoded = train_label_encoded.reshape(len(train_label_encoded), 1)
train_label = onehot_encoder.transform(train_label_encoded)
test_labels_encoded = label_encoder.transform(test_labels)
test_labels_encoded = test_labels_encoded.reshape(len(test_labels_encoded), 1)
test_labels = onehot_encoder.transform(test_labels_encoded)


embeddings_index = {}
with open('glove.6B.100d.txt', encoding='utf8') as f:
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs

all_embs = np.stack(list(embeddings_index.values()))
emb_mean, emb_std = all_embs.mean(), all_embs.std()
num_words = min(max_num_words, len(word_index)) + 1
embedding_dim = len(embeddings_index['the'])
embedding_matrix = np.random.normal(emb_mean, emb_std, (num_words, embedding_dim))
for word, i in word_index.items():
    if i >= max_num_words:
        break
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector

model = Sequential()
model.add(Embedding(num_words, 100, trainable=False, input_length=train_sequences.shape[1], weights=[embedding_matrix]))
model.add(Bidirectional(LSTM(256, return_sequences=True, recurrent_dropout=0.1, dropout=0.1)))
model.add(Dropout(0.3))
model.add(LSTM(256, return_sequences=False, recurrent_dropout=0.1, dropout=0.1))
model.add(Dropout(0.3))
model.add(Dense(50, activation='relu'))
model.add(Dropout(0.3))
model.add(Dense(classes.shape[0], activation='softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['acc'])

history = model.fit(train_sequences, train_label, epochs=50, batch_size=64, shuffle=True, validation_data=(test_sequences, test_labels))

# Save model architecture and weights separately
model_json = model.to_json()
with open('models/modelv2_architecture.json', 'w') as json_file:
    json_file.write(model_json)
model.save_weights('models/modelv2.weights.h5')

with open('utils/classesv2.pkl', 'wb') as file:
    pickle.dump(classes, file)

with open('utils/tokenizerv2.pkl', 'wb') as file:
    pickle.dump(tokenizer, file)

with open('utils/label_encoderv2.pkl', 'wb') as file:
    pickle.dump(label_encoder, file)