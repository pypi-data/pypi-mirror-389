def five():
    
    print("""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import skipgrams
from tensorflow.keras.utils import to_categorical

# Sample corpus
corpus = [
    "the cat sits on the mat",
    "the dog barks at the mailman",
    "dogs and cats are friends"
]

# Tokenize words
tokenizer = Tokenizer()
tokenizer.fit_on_texts(corpus)
word2idx = tokenizer.word_index
idx2word = {v: k for k, v in word2idx.items()}

vocab_size = len(word2idx) + 1
print("✅ Vocabulary:", word2idx)
print("✅ Vocab size:", vocab_size)

# Convert text to sequences of integers
sequences = tokenizer.texts_to_sequences(corpus)
window_size = 2
X = []  # context words
y = []  # target word

for sentence in sequences:
    for i in range(window_size, len(sentence) - window_size):
        context = []
        for j in range(-window_size, window_size + 1):
            if j != 0:
                context.append(sentence[i + j])
        target = sentence[i]
        X.append(context)
        y.append(target)

X = np.array(X)
y = np.array(y)

print("✅ Sample context-target pairs:")
for i in range(5):
    print([idx2word[w] for w in X[i]], "→", idx2word[y[i]])

embedding_dim = 10  # dimension of word embeddings

inputs = keras.Input(shape=(window_size * 2,))
embedding = layers.Embedding(input_dim=vocab_size, output_dim=embedding_dim)(inputs)
x = layers.Lambda(lambda x: tf.reduce_mean(x, axis=1))(embedding)
output = layers.Dense(vocab_size, activation='softmax')(x)

cbow_model = keras.Model(inputs=inputs, outputs=output)
cbow_model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

cbow_model.summary()

history = cbow_model.fit(X, y, epochs=100, verbose=0)
print("✅ Training complete!")

# Extract embeddings
embeddings = cbow_model.get_layer('embedding_1').get_weights()[0]

# Function to find similar words
def most_similar(word, top_n=5):
    if word not in word2idx:
        print("Word not in vocabulary!")
        return
    idx = word2idx[word]
    target_vec = embeddings[idx]
    similarities = np.dot(embeddings, target_vec)
    similar_indices = similarities.argsort()[::-1][1:top_n+1]
    for i in similar_indices:
        print(f"{idx2word[i]} → similarity: {similarities[i]:.3f}")

print("\n🔍 Most similar words to 'dog':")
most_similar("dog")

print("\n🔍 Most similar words to 'cat':")
most_similar("cat")
"""
    )

def two():
    print(
        """
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt

(x_train,y_train),(x_test,y_test) = keras.datasets.mnist.load_data()

x_train = x_train.astype('float32')/255.0
x_test = x_test.astype('float32')/255.0

x_train = x_train.reshape((x_train.shape[0],28*28))
x_test = x_test.reshape((x_test.shape[0],28*28))

y_train = keras.utils.to_categorical(y_train,10)
y_test = keras.utils.to_categorical(y_test,10)

model=keras.Sequential([
    keras.Input(shape=(784,)),
    layers.Dense(128,activation='relu'),
    layers.Dense(64,activation='relu'),
    layers.Dense(10,activation='softmax')
])



model.compile(
    optimizer = 'sgd',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

history = model.fit(
    x_train,y_train,
    epochs=10,
    batch_size=64,
    validation_data=(x_test,y_test),
    verbose=1
)

print(y_train.shape)
print(y_test.shape)

test_loss,test_acc = model.evaluate(x_test,y_test,verbose=0)

print(f"Test Accuracy:{test_acc*100:.2f}%")
print(f"Test Loss:{test_loss:.4f}")

plt.figure(figsize=(12, 5))

# Plot training & validation accuracy
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

# Plot training & validation loss
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.show()

import seaborn as sns

sns.lineplot(model.history.history)
"""
    )

def six():
    print(
        """from tensorflow.keras.preprocessing.image import ImageDataGenerator
train_dir = 'dataset/mnist-jpg/mnist-jpg/train/'
test_dir = 'dataset/mnist-jpg/mnist-jpg/test/'
img_gen = ImageDataGenerator(rescale=1.0/255)
data_gen = img_gen.flow_from_directory(
 train_dir,
 target_size=(32,32),
 batch_size=5000,
 shuffle=True,
 class_mode='categorical'
)
x_train, y_train = data_gen[0]
x_test, y_test = data_gen[2]
from tensorflow.keras.applications import VGG16
path = 'dataset/vgg16_weights_tf_dim_ordering_tf_kernels_notop.h5'
vgg_model = VGG16(weights=path,include_top=False, input_shape=(32,32,3))
for layer in vgg_model.layers:
 layer.trainabler=False
from tensorflow import keras
from tensorflow.keras.layers import Dense, Flatten, Dropout
custom_classifier = keras.Sequential([
 Flatten(input_shape=(1,1,512)),
 Dense(100, activation='relu'),
 Dropout(0.2),
 Dense(100, activation='relu'),
 Dropout(0.2),
 Dense(10, activation='softmax')

])
model = keras.Sequential([
 vgg_model,
 custom_classifier
])
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accur
model.fit(x_train, y_train, batch_size=100, epochs=1, validation_data=(x_test,y_
for layer in vgg_model.layers[:-4]:
 layer.trainable = True

loss, acc = model.evaluate(x_test, y_test)
print(loss, " ", acc)
pred = model.predict(x_test)
labels = list(data_gen.class_indices.keys())
import matplotlib.pyplot as plt
import numpy as np
plt.imshow(x_test[10])
plt.title(str(labels[np.argmax(pred[10])]))
print(str(labels[np.argmax(y_test[10])]))
y_test[10]"""
    )

def three():
    print(
        """
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import matplotlib.pyplot as plt

(x_train,y_train),(x_test,y_test) = keras.datasets.mnist.load_data()

x_train = x_train.astype('float32')/255.0
x_test=x_test.astype('float32')/255.0

print(x_train.shape)

print(y_train.shape)

plt.imshow(x_train[25])

print(y_train[25])

print(np.unique(y_train))

model = keras.Sequential([
    keras.Input(shape=(28,28)),
    layers.Flatten(),
    layers.Dense(50,activation='relu',name='L1'),
    layers.Dense(50,activation='relu',name='L2'),
    layers.Dense(10,activation='softmax',name='L3')
])

model.compile(
    optimizer='sgd',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

from IPython.core import history
history = model.fit(
    x_train,y_train,
    epochs=10,
    batch_size=30,
    validation_data=(x_test,y_test),
    verbose=1
)

import seaborn as sns
sns.lineplot(model.history.history)

plt.figure(figsize=(12,5))


plt.subplot(1,2,1)
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

plt.subplot(1,2,2)
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.show()

test_loss,test_acc=model.evaluate(x_test,y_test)

print(f"Total Loss:{test_loss:.4f}")
print(f"Total Accuracy:{test_acc*100:.2f}%")

predicted_val = model.predict(x_test)
plt.imshow(x_test[15])
plt.show()

print(np.argmax(predicted_val[15], axis=0))
""")