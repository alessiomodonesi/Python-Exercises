import tensorflow as tf
from tensorflow import keras
import numpy as np
import matplotlib.pyplot as plt

# 1. CARICAMENTO E PREPARAZIONE DEI DATI
# Il dataset MNIST è incluso in Keras. Contiene 60.000 immagini per l'allenamento
# e 10.000 per il test.
mnist = keras.datasets.mnist
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()

# Normalizzazione dei dati: i pixel delle immagini vanno da 0 a 255.
# Li portiamo in un range da 0 a 1 per aiutare la rete a imparare più velocemente.
train_images = train_images / 255.0
test_images = test_images / 255.0

# 2. COSTRUZIONE DEL MODELLO (LA RETE NEURALE)
# Usiamo un modello Sequenziale, dove i livelli sono impilati uno dopo l'altro.
model = keras.Sequential([
    # Primo livello: "appiattisce" l'immagine da una matrice 28x28 a un vettore di 784 pixel.
    keras.layers.Flatten(input_shape=(28, 28)),
    
    # Secondo livello: un livello "denso" (fully-connected) con 128 neuroni.
    # L'activation function 'relu' è uno standard che funziona molto bene.
    keras.layers.Dense(128, activation='relu'),
    
    # Terzo livello (opzionale ma utile): Dropout. "Spegne" casualmente il 20% dei neuroni
    # durante l'allenamento per evitare che la rete "impari a memoria" (overfitting).
    keras.layers.Dropout(0.2),
    
    # Livello di uscita: ha 10 neuroni, uno per ogni cifra (0-9).
    # 'softmax' converte i risultati in un array di probabilità, la cui somma è 1.
    keras.layers.Dense(10, activation='softmax')
])

# 3. COMPILAZIONE DEL MODELLO
# Qui definiamo come il modello dovrà imparare.
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# 4. ALLENAMENTO DEL MODELLO
# Diamo in pasto alla rete i dati di allenamento.
# 'epochs=5' significa che la rete vedrà l'intero dataset per 5 volte.
print("Inizio allenamento del modello...")
model.fit(train_images, train_labels, epochs=5, validation_data=(test_images, test_labels))
print("Allenamento completato.")

# 5. VALUTAZIONE DEL MODELLO
# Verifichiamo le performance del modello sul set di test, che non ha mai visto.
test_loss, test_acc = model.evaluate(test_images, test_labels, verbose=2)
print(f'\nAccuratezza sul test set: {test_acc:.4f}')

# 6. SALVA IL MODELLO ALLENATO
print("Salvataggio del modello in corso...")
model.save('model.keras')
print("Modello salvato come 'model.keras'")

# 7. FARE UNA PREDIZIONE E VISUALIZZARLA
# Scegliamo un'immagine a caso dal test set per vedere come si comporta il modello.
immagine_test = np.random.randint(0, test_images.shape[0])
img = test_images[immagine_test]
label_reale = test_labels[immagine_test]

# Keras si aspetta un "batch" di immagini, quindi aggiungiamo una dimensione.
img_batch = np.expand_dims(img, 0)

# Otteniamo le previsioni (un array di 10 probabilità)
predictions = model.predict(img_batch)

# Troviamo la cifra con la probabilità più alta
predicted_label = np.argmax(predictions[0])
confidence = np.max(predictions[0])

# Mostriamo il risultato
plt.imshow(img, cmap=plt.cm.binary)
plt.title(f"Predizione: {predicted_label} ({confidence:.2%} di confidenza)\nReale: {label_reale}")
plt.axis('off')
plt.show()