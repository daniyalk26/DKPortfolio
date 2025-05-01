import os
import tensorflow as tf
import pandas as pd
from sklearn.model_selection import train_test_split

# Paths and parameters
CSV_PATH = 'backend/emotion/labels.csv'
IMG_DIR   = 'backend/emotion'
BATCH_SIZE = 32
IMG_SIZE = (300, 300)  # EfficientNetB3 input size
CLASS_NAMES = ['angry', 'happy', 'relaxed', 'sad']


df = pd.read_csv(CSV_PATH)
label2idx = {name: idx for idx, name in enumerate(CLASS_NAMES)}
df['label_idx'] = df['label'].map(label2idx)

# 2. Build the full filepath—including the subfolder named by the label
df['filepath'] = df.apply(
    lambda row: os.path.join(IMG_DIR, row['label'], row['filename']),
    axis=1
)


# 2. Split into train, validation, and test sets (70/15/15 stratified)
train_df, temp_df = train_test_split(df, test_size=0.3, stratify=df['label'], random_state=42)
val_df, test_df  = train_test_split(temp_df, test_size=0.5, stratify=temp_df['label'], random_state=42)

# 3. Preprocessing function
def preprocess_image(path, label):
    img = tf.io.read_file(path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, IMG_SIZE)
    img = tf.keras.applications.efficientnet.preprocess_input(img)
    return img, tf.one_hot(label, depth=len(CLASS_NAMES))

# 4. Convert DataFrame to tf.data.Dataset
def df_to_dataset(dataframe, shuffle=True):
    filepaths = dataframe['filepath'].values
    labels = dataframe['label_idx'].values
    ds = tf.data.Dataset.from_tensor_slices((filepaths, labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(filepaths))
    ds = ds.map(preprocess_image, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    return ds

# Create datasets
train_ds = df_to_dataset(train_df, shuffle=True)
val_ds   = df_to_dataset(val_df, shuffle=False)
test_ds  = df_to_dataset(test_df, shuffle=False)

# Inspect a batch
for images, labels in train_ds.take(1):
    print(images.shape, labels.shape)
