#!/bin/bash
#
# Script per installare pacchetti Python in due ambienti virtuali separati:
# 1. master: per tutti i tool di data science, escluso TensorFlow.
# 2. tensorflow: dedicato a TensorFlow con accelerazione Metal, usando una
#    combinazione di versioni testata e funzionante.
# I venv verranno creati nella directory genitore (../).

# ---- PARTE 1: CREAZIONE E SETUP DELL'AMBIENTE MASTER ----

echo " PARTE 1: Configurazione di 'master'"
echo "========================================"

# 1. Crea il primo ambiente virtuale nella cartella superiore
echo "Creazione di ../master..."
python3 -m venv ../master

# 2. Attiva l'ambiente virtuale
echo "Attivazione di ../master..."
source ../master/bin/activate

# 3. Installa tutti i pacchetti necessari in un unico comando
echo "Installazione dei pacchetti di data science..."
pip install control jupyter matplotlib numpy pandas Pillow python-dotenv requests scikit-learn scipy seaborn sympy

# 4. Verifica l'installazione
echo "Pacchetti installati in master:"
pip list
echo "---------------------------------"

# 5. Disattiva il primo ambiente
echo "Installazioni in master completate. Disattivazione..."
deactivate
echo ""
echo ""


# ---- PARTE 2: CREAZIONE E SETUP DELL'AMBIENTE TENSORFLOW ----

echo " PARTE 2: Configurazione di 'tensorflow_venv'"
echo "==========================================="

# 1. Crea il secondo ambiente virtuale nella cartella superiore
echo "Creazione di ../tensorflow_venv..."
python3 -m venv ../tensorflow_venv

# 2. Attiva il secondo ambiente virtuale
echo "Attivazione di ../tensorflow_venv..."
source ../tensorflow_venv/bin/activate

# 3. Installa la combinazione specifica e testata di TF, Metal e Keras
echo "Installazione di tensorflow==2.17.1, tensorflow-metal==1.1.0, tf-keras==2.17.0..."
pip install tensorflow==2.17.1 tensorflow-metal==1.1.0 tf-keras==2.17.0

# 4. Verifica che la GPU sia riconosciuta
echo "Verifica del setup di TensorFlow..."
python -c "
import tensorflow as tf;
print(f'Versione di TensorFlow installata: {tf.__version__}');
gpu_devices = tf.config.list_physical_devices('GPU');
if gpu_devices:
    print('Successo! GPU Metal trovata:', gpu_devices);
else:
    print('Attenzione: Nessuna GPU Metal trovata. TensorFlow userà la CPU.');
"
echo "---------------------------------"

# 5. Disattiva il secondo ambiente
echo "Installazione in tensorflow_venv completata. Disattivazione..."
deactivate

echo ""
echo "Processo completato. Creati e configurati due ambienti virtuali ('master' e 'tensorflow_venv') nella cartella superiore."
