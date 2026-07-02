import io
import os
import numpy as np
from tensorflow import keras
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from PIL import Image
import tensorflow as tf


class Model:

    def __init__(self):
        self.IMAGE_SIZE = (28, 28)
        self.IMAGE_SHAPE = (28, 28, 1)
        self.MODEL_FILENAME = "model.h5"
        self.CATEGORIES = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.FOLDERS = ["Numbers", "English"]
        self.DATA_DIR = "content/DataForModel/DataForModel"  # was my google collab path..
        self.VALIDATION_SPLIT = 0.2
        self.RANDOM_STATE = 42
        self.EPOCHS = 40

        self.CONV1_FILTERS = 32
        self.CONV2_FILTERS = 64
        self.KERNEL_SIZE = (3, 3)
        self.POOL_SIZE = (2, 2)
        self.DENSE_UNITS = 128

        self.model = None
        self.MODEL_PATH = os.path.join(os.getcwd(), self.MODEL_FILENAME)
        self.data = []
        self.labels = []
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None

    # def load_files(self):
    #     for folder in self.FOLDERS:
    #         folder_path = os.path.join(self.DATA_DIR, folder)
    #         for category in sorted(os.listdir(folder_path)):
    #             category_path = os.path.join(folder_path, category)
    #             label = self.CATEGORIES.index(category)
    #             for img_name in os.listdir(category_path):
    #                 img_path = os.path.join(category_path, img_name)
    #                 img = Image.open(img_path).convert("L")
    #                 img = img.resize(self.IMAGE_SIZE)
    #                 img = np.array(img)
    #                 self.data.append(img)
    #                 self.labels.append(label)

    def reshaping_data(self):
        self.data = np.array(self.data).reshape(-1, *self.IMAGE_SHAPE)
        self.labels = np.array(self.labels)

    def separating_train_and_test(self):
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.data, self.labels,
            test_size=self.VALIDATION_SPLIT,
            random_state=self.RANDOM_STATE
        )
        num_categories = len(self.CATEGORIES)
        self.y_train = keras.utils.to_categorical(self.y_train, num_categories)
        self.y_test = keras.utils.to_categorical(self.y_test, num_categories)

    def model_cnn_creating(self):
        self.model = keras.Sequential([
            keras.layers.Conv2D(
                self.CONV1_FILTERS,
                self.KERNEL_SIZE,
                activation='relu',
                input_shape=self.IMAGE_SHAPE
            ),
            keras.layers.MaxPooling2D(self.POOL_SIZE),

            keras.layers.Conv2D(self.CONV2_FILTERS, self.KERNEL_SIZE, activation='relu'),
            keras.layers.MaxPooling2D(self.POOL_SIZE),

            keras.layers.Flatten(),
            keras.layers.Dense(self.DENSE_UNITS, activation='relu'),
            keras.layers.Dense(len(self.CATEGORIES), activation='softmax')
        ])

    def train_and_compile(self):
        self.model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        history = self.model.fit(
            self.X_train, self.y_train,
            epochs=self.EPOCHS,
            validation_data=(self.X_test, self.y_test)
        )
        plt.plot(history.history['accuracy'], label='Train Accuracy')
        plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
        plt.legend()
        plt.show()
        self.model.save(self.MODEL_PATH)

    def total_creating_model(self):
        self.reshaping_data()
        self.separating_train_and_test()
        self.model_cnn_creating()
        self.train_and_compile()

    def process_image(self, image_bytes):
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("L")
        image = Image.eval(image, lambda x: 255 - x)
        image = image.resize(self.IMAGE_SIZE, Image.Resampling.LANCZOS)
        image = np.array(image)
        image = image / 255.0
        image = np.expand_dims(image, axis=-1)
        image = np.expand_dims(image, axis=0)
        return image

    def use_model(self, image_bytes):
        img = self.process_image(image_bytes)
        self.model = tf.keras.models.load_model(self.MODEL_PATH)
        prediction = self.model.predict(img)
        predicted_label = np.argmax(prediction)
        predicted_character = self.CATEGORIES[predicted_label]
        print(predicted_label)
        return predicted_character
