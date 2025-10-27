# Importa la libreria principale di TensorFlow e le assegna l'alias 'tf' per comodità.
import tensorflow as tf

# 1. CARICAMENTO DEL DATASET CIFAR-100
# ------------------------------------
# Accede al dataset CIFAR-100, che è una raccolta di immagini già inclusa in TensorFlow.
# Questo dataset contiene 60.000 immagini a colori di 32x32 pixel, divise in 100 categorie
# (es. "mela", "acquario", "castello", "dinosauro", ecc.).
cifar = tf.keras.datasets.cifar100

# Scarica i dati e li suddivide automaticamente in due set:
# - (x_train, y_train): 50.000 immagini e le loro etichette corrette, usate per allenare il modello.
# - (x_test, y_test): 10.000 immagini e le loro etichette, usate per testare le performance del modello.
(x_train, y_train), (x_test, y_test) = cifar.load_data()


# 2. CREAZIONE DEL MODELLO RESNET50
# ---------------------------------
# Qui creiamo il nostro modello di rete neurale. Invece di costruirlo da zero,
# usiamo "ResNet50", un'architettura predefinita e molto potente, famosa per la sua efficacia
# nella classificazione di immagini.
model = tf.keras.applications.ResNet50(
    # include_top=True: Significa che vogliamo includere anche la parte finale della rete,
    # quella che si occupa della classificazione vera e propria.
    include_top=True,

    # weights=None: FONDAMENTALE. Stiamo dicendo a TensorFlow di NON caricare i pesi
    # pre-allenati sul dataset ImageNet. Il modello viene creato con una "mente vuota"
    # (pesi casuali) e dovrà imparare tutto da zero usando solo le nostre immagini CIFAR-100.
    weights=None,

    # input_shape=(32, 32, 3): Definiamo la dimensione delle nostre immagini in input:
    # 32 pixel di altezza, 32 di larghezza e 3 canali di colore (Rosso, Verde, Blu).
    input_shape=(32, 32, 3),

    # classes=100: Specifichiamo che il livello finale della rete deve avere 100 neuroni,
    # uno per ogni categoria del nostro dataset CIFAR-100.
    classes=100,
)


# 3. COMPILAZIONE DEL MODELLO
# -----------------------------
# Prima di poter allenare il modello, dobbiamo configurare il suo processo di apprendimento.

# Definiamo la "funzione di perdita" (loss function). Questa funzione misura quanto
# le predizioni del modello siano sbagliate rispetto alla realtà.
# 'SparseCategoricalCrossentropy' è la scelta standard per problemi di classificazione
# con più di due categorie, dove le etichette sono numeri interi (es. 0, 1, 2...).
loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False)

# Usiamo il metodo .compile() per assemblare il tutto.
model.compile(
    # optimizer="adam": L'algoritmo che il modello userà per "correggersi" e minimizzare
    # l'errore (la loss). "adam" è un ottimizzatore molto robusto ed efficiente.
    optimizer="adam",
    
    # loss=loss_fn: Diciamo al modello quale funzione di errore usare.
    loss=loss_fn,
    
    # metrics=["accuracy"]: Chiediamo al modello di monitorare e riportare l'accuratezza
    # (la percentuale di immagini classificate correttamente) durante l'allenamento.
    metrics=["accuracy"]
)


# 4. ALLENAMENTO DEL MODELLO
# --------------------------
# Questo è il comando che avvia l'allenamento vero e proprio.
model.fit(
    # Diamo in pasto al modello le immagini di allenamento (x_train) e le loro etichette (y_train).
    x_train, y_train,
    
    # epochs=5: Il modello esaminerà l'intero dataset di allenamento per 5 volte.
    # Ad ogni "epoca", le sue performance dovrebbero migliorare.
    epochs=5,
    
    # batch_size=64: Il modello non guarderà tutte le 50.000 immagini in una volta,
    # ma le elaborerà in piccoli "lotti" (batch) da 64 immagini. Dopo ogni lotto,
    # aggiornerà i suoi pesi interni. Questo rende l'allenamento più efficiente.
    batch_size=64
)