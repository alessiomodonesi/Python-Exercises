import re
import sys


def rimuovi_citazioni(file_input, file_output=None):
    """Rimuove i tag di citazione e da un file Markdown."""
    # Se non viene specificato un file di output, sovrascrive quello di input
    if file_output is None:
        file_output = file_input

    # Espressione regolare:
    # \[cite           -> Trova l'apertura della quadra e la parola "cite"
    # (?:_start|:\s*[\d\s,]+) -> Trova "_start" OPPURE ":" seguito da numeri, spazi o virgole
    # \]               -> Trova la chiusura della quadra
    pattern = r"\[cite(?:_start|:\s*[\d\s,]+)\]"

    try:
        # Legge il contenuto del file originale
        with open(file_input, "r", encoding="utf-8") as f:
            contenuto = f.read()

        # Sostituisce i match della regex con una stringa vuota
        contenuto_pulito = re.sub(pattern, "", contenuto)

        # Rimuove eventuali spazi doppi rimasti dopo la cancellazione dei tag
        contenuto_pulito = re.sub(r" +", " ", contenuto_pulito)

        # Salva il risultato nel file di destinazione
        with open(file_output, "w", encoding="utf-8") as f:
            f.write(contenuto_pulito)

        print(f"Successo! Il file pulito è stato salvato in: {file_output}")

    except FileNotFoundError:
        print(f"Errore: Il file '{file_input}' non esiste.")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")


# Esempio di utilizzo dello script
if __name__ == "__main__":
    # Sostituisci con i percorsi dei tuoi file
    file_da_pulire = "il_tuo_file.md"
    file_risultato = "il_tuo_file_pulito.md"

    rimuovi_citazioni(file_da_pulire, file_risultato)
