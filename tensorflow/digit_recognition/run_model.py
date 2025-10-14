import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt

# 1. CARICA IL MODELLO PRE-ALLENATO
print("Caricamento del modello...")
loaded_model = tf.keras.models.load_model('modello_cifre.keras')
print("Modello caricato con successo.")

# 2. PREPARA I DATI PER IL TEST
# Dobbiamo caricare il dataset solo per avere delle immagini da testare
mnist = tf.keras.datasets.mnist
(_, _), (test_images, test_labels) = mnist.load_data()
test_images = test_images / 255.0

# 3. ESEGUI LA PREDIZIONE
# Scegli un'immagine a caso dal test set
immagine_test = np.random.randint(0, test_images.shape[0])
img = test_images[immagine_test]
label_reale = test_labels[immagine_test]

# Prepara l'immagine per il modello (aggiungi la dimensione del batch)
img_batch = np.expand_dims(img, 0)

# Fai la predizione usando il modello caricato
predictions = loaded_model.predict(img_batch)
predicted_label = np.argmax(predictions[0])
confidence = np.max(predictions[0])

# 4. MOSTRA IL RISULTATO
plt.imshow(img, cmap=plt.cm.binary)
plt.title(f"Predizione: {predicted_label} ({confidence:.2%} di confidenza)\nReale: {label_reale}")
plt.axis('off')
plt.show()