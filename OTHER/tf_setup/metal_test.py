import tensorflow as tf
print(f'Versione di TensorFlow installata: {tf.__version__}')
gpu_devices = tf.config.list_physical_devices('GPU')
if gpu_devices:
    print('Successo! GPU Metal trovata:', gpu_devices)
else:
    print('Attenzione: Nessuna GPU Metal trovata. TensorFlow userà la CPU.')