# model.py
import os
import math
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, mixed_precision
from tensorflow.keras.optimizers import AdamW
from tensorflow.keras.optimizers.schedules import CosineDecay
from tensorflow.keras.applications import EfficientNetB3
from tensorflow.keras.applications.efficientnet import preprocess_input

# ── GLOBAL SETTINGS ────────────────────────────────────────────────────────────
mixed_precision.set_global_policy("mixed_float16")  # GPU speed‑up

IMG_SIZE        = (300, 300)
BATCH_SIZE      = 32
PHASE1_EPOCHS   = 10
PHASE2_EPOCHS   = 20
BASE_LR         = 1e-3
WEIGHT_DECAY    = 1e-5
LABEL_SMOOTHING = 0.1
FINE_TUNE_AT    = 250

DATA_ROOT   = "data_processed"
TRAIN_DIR   = os.path.join(DATA_ROOT, "train")
VAL_DIR     = os.path.join(DATA_ROOT, "val")
TEST_DIR    = os.path.join(DATA_ROOT, "test")

# ── COUNT SAMPLES & COMPUTE STEPS ──────────────────────────────────────────────
num_train        = sum(len(files) for _, _, files in os.walk(TRAIN_DIR))
num_val          = sum(len(files) for _, _, files in os.walk(VAL_DIR))
steps_per_epoch  = math.ceil(num_train / BATCH_SIZE)
validation_steps = math.ceil(num_val   / BATCH_SIZE)

# ── DATASET BUILDER ────────────────────────────────────────────────────────────
def make_ds(path, training=False):
    ds = tf.keras.utils.image_dataset_from_directory(
        path,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical",
        shuffle=training,
        seed=42,
    )
    if training:
        # shuffle + repeat only for the training split
        ds = ds.cache().shuffle(1000).repeat()
    else:
        ds = ds.cache()
    # drop any corrupt/empty images
    ds = ds.ignore_errors()
    return ds.prefetch(tf.data.AUTOTUNE)

train_ds = make_ds(TRAIN_DIR, training=True)
val_ds   = make_ds(VAL_DIR,   training=False)
test_ds  = make_ds(TEST_DIR,  training=False)

# ── MODEL DEFINITION ──────────────────────────────────────────────────────────
augment = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
    layers.RandomContrast(0.1),
], name="augment")

inputs = layers.Input(shape=(*IMG_SIZE, 3), dtype="float32")
x      = augment(inputs)
x      = preprocess_input(x)

base = EfficientNetB3(
    include_top=False,
    weights="imagenet",
    input_tensor=x
)
base.trainable = False

x       = layers.GlobalAveragePooling2D()(base.output)
x       = layers.Dropout(0.4)(x)
outputs = layers.Dense(
    train_ds.element_spec[1].shape[-1],
    activation="softmax",
    dtype="float32",  # cast back from float16
)(x)

model = models.Model(inputs, outputs, name="EffNetB3_DogAge")

# ── PHASE 1: TRAIN TOP LAYERS ───────────────────────────────────────────────────
lr_schedule = CosineDecay(
    initial_learning_rate=BASE_LR,
    decay_steps=steps_per_epoch * PHASE1_EPOCHS
)

model.compile(
    optimizer=AdamW(learning_rate=lr_schedule, weight_decay=WEIGHT_DECAY),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=LABEL_SMOOTHING),
    metrics=["accuracy"],
)

phase1_callbacks = [
    callbacks.ModelCheckpoint(
        "phase1_best.keras",
        monitor="val_accuracy",
        save_best_only=True
    ),
    callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=3,
        restore_best_weights=True
    ),
    callbacks.BackupAndRestore(backup_dir="backup_phase1"),
    callbacks.TensorBoard(log_dir="logs/phase1"),
]

model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=PHASE1_EPOCHS,
    steps_per_epoch=steps_per_epoch,
    validation_steps=validation_steps,
    callbacks=phase1_callbacks,
    verbose=1,
)

# ── PHASE 2: FINE‑TUNE UPPER LAYERS ────────────────────────────────────────────
base.trainable = True
for layer in base.layers[:FINE_TUNE_AT]:
    layer.trainable = False

model.compile(
    optimizer=AdamW(learning_rate=BASE_LR / 10, weight_decay=WEIGHT_DECAY),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=LABEL_SMOOTHING),
    metrics=["accuracy"],
)

phase2_callbacks = [
    callbacks.ModelCheckpoint(
        "phase2_best.keras",
        monitor="val_accuracy",
        save_best_only=True
    ),
    callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=5,
        restore_best_weights=True
    ),
    callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2
    ),
    callbacks.TensorBoard(log_dir="logs/phase2"),
]

model.fit(
    train_ds,
    validation_data=val_ds,
    initial_epoch=PHASE1_EPOCHS,
    epochs=PHASE1_EPOCHS + PHASE2_EPOCHS,
    steps_per_epoch=steps_per_epoch,
    validation_steps=validation_steps,
    callbacks=phase2_callbacks,
    verbose=1,
)

# ── EVALUATION & SAVE ──────────────────────────────────────────────────────────
loss, acc = model.evaluate(test_ds)
print(f"\n✅  Test accuracy: {acc:.4f}")

model.save("final_new_model.keras")
