# Riconoscimento di Cifre Scritte a Mano con TensorFlow

Questo progetto è un'introduzione al mondo del deep learning e delle reti neurali. Il programma utilizza la libreria TensorFlow per costruire, allenare e valutare un modello capace di riconoscere cifre scritte a mano (da 0 a 9) con un'alta accuratezza.

Il dataset utilizzato è **MNIST**, un classico nel campo del machine learning, composto da 70.000 immagini in scala di grigi di 28x28 pixel.

---

## 🎯 Obiettivo del Progetto

L'obiettivo è creare un classificatore di immagini. Il programma allena una rete neurale su 60.000 immagini di cifre e poi testa la sua accuratezza su un set di 10.000 immagini che non ha mai visto prima. Infine, effettua una predizione su un'immagine casuale per mostrare un esempio pratico del suo funzionamento.

---

## 🛠️ Prerequisiti

Prima di iniziare, assicurati di avere a disposizione l'ambiente virtuale corretto, creato con lo script di installazione.

* **Python**: Versione **3.11.x**.
* **Ambiente Virtuale**: Il venv `tensorflow_venv` deve essere stato creato e deve contenere tutti i pacchetti necessari (`tensorflow==2.17.1`, `tensorflow-metal==1.1.0`, `tf-keras==2.17.0`, `numpy`, `matplotlib`).

---

## 🚀 Istruzioni per l'Esecuzione

Per far funzionare il programma, segui questi semplici passaggi dal tuo terminale.

### 1. Attiva l'Ambiente Virtuale

Assicurati di trovarti nella cartella che contiene la cartella del venv (`tensorflow`). Se hai seguito lo script precedente, il venv si troverà nella directory superiore.

```bash
# Attiva l'ambiente 'tensorflow_venv'
source ../tensorflow/bin/activate
```

Il tuo prompt del terminale dovrebbe ora mostrare `(tensorflow)` all'inizio della riga, indicando che l'ambiente è attivo.

### 2. Esegui lo Script Python

Una volta attivato l'ambiente, esegui lo script.

```bash
# Esegui il programma
python riconoscimento_cifre.py
```

### 3. Osserva l'Output

* Nel terminale, vedrai l'avanzamento dell'allenamento del modello per 5 "epoche". Mostrerà la perdita (`loss`) e l'accuratezza (`accuracy`) diminuire e aumentare rispettivamente.
* Alla fine, verrà stampata l'accuratezza finale calcolata sul set di test.
* Si aprirà una finestra grafica che mostrerà un'immagine di una cifra presa a caso, con la predizione del modello e il suo livello di confidenza.

---

## 📖 Spiegazione del Codice

Il codice è suddiviso in 6 passaggi logici.

### 1. Caricamento e Preparazione dei Dati

Il dataset MNIST è pre-caricato in `tensorflow.keras.datasets`.

* **`mnist.load_data()`**: Scarica e suddivide i dati in set di allenamento (`train_images`, `train_labels`) e di test (`test_images`, `test_labels`).
* **Normalizzazione**: Le immagini hanno valori di pixel da 0 (nero) a 255 (bianco). Dividendo tutti i pixel per 255.0, li trasformiamo in un intervallo tra 0 e 1. Questo semplice passaggio aiuta la rete neurale ad apprendere in modo più stabile ed efficiente.

### 2. Costruzione del Modello (La Rete Neurale)

La nostra rete è un modello `keras.Sequential`, ovvero una semplice pila di livelli.

* **`Flatten(input_shape=(28, 28))`**: Questo livello non impara nulla; si limita a trasformare ogni immagine da una griglia 2D (28x28 pixel) a un singolo array 1D (784 pixel).
* **`Dense(128, activation='relu')`**: Questo è un livello "denso" o "completamente connesso" con 128 neuroni. È il cervello del nostro modello, dove avviene l'apprendimento dei pattern. La funzione di attivazione `relu` è una scelta standard ed efficace.
* **`Dropout(0.2)`**: Una tecnica di regolarizzazione per prevenire l'overfitting (quando un modello impara "a memoria" i dati di training ma non generalizza bene). Durante l'allenamento, "spegne" casualmente il 20% dei neuroni, costringendo la rete a imparare caratteristiche più robuste.
* **`Dense(10, activation='softmax')`**: Il livello di output finale. Ha 10 neuroni, uno per ogni possibile cifra (0-9). La funzione `softmax` calcola la probabilità per ciascuna delle 10 classi. La cifra corrispondente al neurone con la probabilità più alta sarà la predizione del modello.

### 3. Compilazione del Modello

Il metodo `.compile()` configura il processo di apprendimento.

* **`optimizer='adam'`**: L'algoritmo utilizzato per aggiornare la rete in base ai dati e alla funzione di perdita. `adam` è un ottimizzatore robusto ed efficiente.
* **`loss='sparse_categorical_crossentropy'`**: La funzione matematica che misura quanto le predizioni del modello siano lontane dalla verità. L'obiettivo dell'allenamento è minimizzare questo valore.
* **`metrics=['accuracy']`**: La metrica che monitoriamo per giudicare le prestazioni del modello.

### 4. Allenamento del Modello

Il comando `model.fit()` avvia il ciclo di allenamento.

* **`epochs=5`**: Specifica che il modello esaminerà l'intero dataset di allenamento per 5 volte. Ad ogni epoca, il modello dovrebbe diventare progressivamente più accurato.
* **`validation_data`**: Al termine di ogni epoca, il modello viene testato su un set di dati di validazione (in questo caso, il test set) per monitorare le sue prestazioni su dati che non sta utilizzando per l'apprendimento.

### 5. Valutazione del Modello

Dopo l'allenamento, `model.evaluate()` calcola la perdita e l'accuratezza finali sul set di test, fornendo una valutazione imparziale delle prestazioni del modello.

### 6. Predizione e Visualizzazione

Questa è la fase finale in cui usiamo il modello allenato per fare una previsione su un singolo dato mai visto prima e usiamo `matplotlib` per visualizzare l'immagine, la sua etichetta reale e la predizione del modello.
