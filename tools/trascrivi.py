import whisper
import torch
import sys  # Importa il modulo 'sys' per accedere agli argomenti

# --- Controllo Argomenti ---
# sys.argv è una lista che contiene gli argomenti passati da terminale.
# sys.argv[0] è il nome dello script stesso (es. "trascrivi.py")
# sys.argv[1] è il primo argomento (il nostro nome file)
if len(sys.argv) < 2:
    print("Errore: Devi specificare il nome del file audio.")
    print("Uso: python trascrivi.py <nome_file.mp3>")
    sys.exit(1) # Esce dallo script con un codice di errore

# Salva il nome del file (primo argomento) in una variabile
file_audio = sys.argv[1]
print(f"File audio da trascrivere: {file_audio}")
# ---------------------------


# 1. Determina il dispositivo da usare
# Controlla se MPS è disponibile, altrimenti ripiega sulla CPU
if torch.backends.mps.is_available():
    device = "mps"
    print("Sto usando il dispositivo MPS (Apple Silicon GPU).")
else:
    device = "cpu"
    print("Sto usando il dispositivo CPU.")

# 2. Carica il modello Whisper specificando il dispositivo
# Puoi sostituire "base" con "small", "medium", "large", ecc.
try:
    model = whisper.load_model("small", device=device)
    print("Modello caricato con successo sul dispositivo.")

    # 3. Esegui la trascrizione
    # Usa la variabile 'file_audio' che contiene l'argomento
    print(f"Avvio trascrizione per {file_audio}...")
    result = model.transcribe(file_audio, fp16=False
)
    print("\n--- INIZIO TRASCRIZIONE ---")
    print(result["text"])
    print("--- FINE TRASCRIZIONE ---")

except FileNotFoundError:
    print(f"Errore: File non trovato. Verifica che '{file_audio}' esista.")
except Exception as e:
    print(f"Si è verificato un errore: {e}")
    print("Assicurati che 'openai-whisper' sia installato (pip install openai-whisper) e che ffmpeg sia installato.")
