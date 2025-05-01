import os
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.optimizers import AdamW
from tensorflow.keras.losses import CategoricalCrossentropy

# ---------------------------------------------------
# Parameters & Paths
# ---------------------------------------------------
IMG_DIR          = "backend/emotion"   # subfolders: angry/, happy/, relaxed/, sad/
IMG_SIZE         = (300, 300)          # EfficientNetB3 native input size
BATCH_SIZE       = 32
VALIDATION_SPLIT = 0.3
SEED             = 42
INITIAL_EPOCHS   = 10
FINE_TUNE_EPOCHS = 30
CLASS_NAMES      = ['angry', 'happy', 'relaxed', 'sad']
NUM_CLASSES      = len(CLASS_NAMES)

# ---------------------------------------------------
# 1) Load + split dataset
# ---------------------------------------------------
train_ds_raw = tf.keras.preprocessing.image_dataset_from_directory(
    IMG_DIR,
    validation_split=VALIDATION_SPLIT,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='categorical',
    shuffle=True,
    class_names=CLASS_NAMES
)
val_ds_raw = tf.keras.preprocessing.image_dataset_from_directory(
    IMG_DIR,
    validation_split=VALIDATION_SPLIT,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='categorical',
    shuffle=False,
    class_names=CLASS_NAMES
)

# ---------------------------------------------------
# 2) Data Augmentation & Preprocessing
# ---------------------------------------------------
data_augmentation = models.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
    layers.RandomContrast(0.1),
    layers.RandomTranslation(0.1, 0.1),
    layers.RandomBrightness(0.1),
], name="data_augmentation")

def prepare(ds, shuffle=False, augment=False):
    if shuffle:
        ds = ds.shuffle(1000, seed=SEED)
    if augment:
        ds = ds.map(
            lambda x, y: (data_augmentation(x, training=True), y),
            num_parallel_calls=tf.data.AUTOTUNE
        )
    ds = ds.map(
        lambda x, y: (tf.keras.applications.efficientnet.preprocess_input(x), y),
        num_parallel_calls=tf.data.AUTOTUNE
    )
    return ds.cache().prefetch(tf.data.AUTOTUNE)

train_ds = prepare(train_ds_raw, shuffle=True, augment=True)
val_ds   = prepare(val_ds_raw, shuffle=False, augment=False)

# ---------------------------------------------------
# 3) Build EfficientNetB3 (Phase 1: frozen base)
# ---------------------------------------------------
base_model = tf.keras.applications.EfficientNetB3(
    include_top=False,
    weights="imagenet",
    input_shape=IMG_SIZE + (3,)
)
base_model.trainable = False

inputs = layers.Input(shape=IMG_SIZE + (3,), name="input")
x = data_augmentation(inputs)                         # on‑the‑fly augmentation
x = tf.keras.applications.efficientnet.preprocess_input(x)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D(name="gap")(x)
x = layers.Dropout(0.5, name="dropout")(x)
outputs = layers.Dense(NUM_CLASSES, activation="softmax", name="predictions")(x)

model = models.Model(inputs, outputs, name="EffNetB3_phase1")

# Cosine‑decay LR schedule for Phase 1
steps_per_epoch = tf.data.experimental.cardinality(train_ds).numpy()
decay_steps     = steps_per_epoch * INITIAL_EPOCHS
lr_schedule     = tf.keras.optimizers.schedules.CosineDecay(
    initial_learning_rate=1e-3,
    decay_steps=decay_steps,
    alpha=0.0
)

model.compile(
    optimizer=AdamW(learning_rate=lr_schedule, weight_decay=1e-5),
    loss=CategoricalCrossentropy(label_smoothing=0.1),
    metrics=["accuracy"]
)

model.summary()

# ---------------------------------------------------
# 4) Phase 1 Callbacks & Training
# ---------------------------------------------------
ckpt1 = callbacks.ModelCheckpoint(
    "best_b3_phase1.keras", monitor="val_accuracy", save_best_only=True, verbose=1
)
es1 = callbacks.EarlyStopping(
    monitor="val_accuracy", patience=5, restore_best_weights=True, verbose=1
)

print("\n=== Phase 1: Training Top Layers (EfficientNetB3 frozen) ===")
history1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=INITIAL_EPOCHS,
    callbacks=[ckpt1, es1]
)
model.save("model_b3_phase1.keras")

# ---------------------------------------------------
# 5) Phase 2: Unfreeze & Fine‑tune Deeper Layers
# ---------------------------------------------------
fine_tune_at = 300  # experiment: unfreeze from this layer onward
base_model.trainable = True
for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False

model.compile(
    optimizer=AdamW(learning_rate=1e-5, weight_decay=1e-5),
    loss=CategoricalCrossentropy(label_smoothing=0.1),
    metrics=["accuracy"]
)
model.summary()

ckpt2 = callbacks.ModelCheckpoint(
    "best_b3_phase2.keras", monitor="val_accuracy", save_best_only=True, verbose=1
)
es2 = callbacks.EarlyStopping(
    monitor="val_accuracy", patience=8, restore_best_weights=True, verbose=1
)
rlr = callbacks.ReduceLROnPlateau(
    monitor="val_loss", factor=0.1, patience=3, verbose=1
)

print("\n=== Phase 2: Fine‑tuning Deeper Layers ===")
history2 = model.fit(
    train_ds,
    validation_data=val_ds,
    initial_epoch=history1.epoch[-1] + 1,
    epochs=INITIAL_EPOCHS + FINE_TUNE_EPOCHS,
    callbacks=[ckpt2, es2, rlr]
)
model.save("final_b3_model.keras")

# ---------------------------------------------------
# 6) Evaluate on Validation Set
# ---------------------------------------------------
val_loss, val_acc = model.evaluate(val_ds)
print(f"\nFinal B3 validation accuracy: {val_acc:.3f}")
