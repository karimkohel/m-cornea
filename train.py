import tensorflow as tf
from sklearn.model_selection import train_test_split
import numpy as np


data = np.load('data/trial3.npy')

x = data[:, :33]
y = data[:, 33:]
xTrain, xTest, yTrain, yTest = train_test_split(x, y, test_size=0.3, random_state=30)

model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(40, activation='relu', input_dim=33),
    tf.keras.layers.Dense(60),
    tf.keras.layers.Dense(2, activation='relu')
])

model.summary()

model.compile(loss='mae', optimizer='adam', metrics='accuracy')
history = model.fit(xTrain, yTrain, epochs=25, validation_split=0.2, verbose=1)
model.save("trial1Model.h5")