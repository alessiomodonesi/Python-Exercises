#!/usr/bin/env python3
"""
Converte tutte le pagine di uno o più PDF in immagini JPEG/PNG.
Salva le immagini in cartelle con il nome del file PDF (senza caratteri speciali).
"""

import argparse
import re
import sys
import shutil
import signal
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError
from alive_progress import alive_bar

# Variabile globale per gestire l'interruzione
interrupted = False

# Flag per verbose logging
VERBOSE = False

# Flag per verificare disponibilità PyMuPDF
PYMUPDF_AVAILABLE = False
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    pass


def vprint(*args, **kwargs):
    """Print solo se verbose è attivo."""
    if VERBOSE:
        print(*args, **kwargs)


def signal_handler(signum, frame):
    """
    Gestisce il segnale di interruzione (Ctrl+C).
    
    Args:
        signum: Numero del segnale
        frame: Frame corrente
    """
    global interrupted
    interrupted = True
    print("\n\n[INTERRUZIONE] Ricevuto segnale di terminazione (Ctrl+C)")
    print("[INFO] Completamento operazioni in corso...")
    print("[INFO] Premere Ctrl+C nuovamente per terminare immediatamente\n")


def check_poppler():
    """
    Verifica che poppler sia installato nel sistema.
    
    Returns:
        True se poppler è installato, False altrimenti
    """
    vprint("[VERBOSE] Controllo disponibilità comando 'pdftoppm'...")
    # Controlla se pdftoppm è disponibile (parte di poppler)
    if shutil.which('pdftoppm') is None:
        vprint("[VERBOSE] 'pdftoppm' non trovato nel PATH")
        return False
    vprint("[VERBOSE] 'pdftoppm' trovato nel PATH")
    return True


def print_poppler_installation_guide():
    """Stampa le istruzioni per installare poppler."""
    print("\n" + "="*70)
    print("ERRORE: Poppler non è installato sul sistema!")
    print("="*70)
    print("\nPoppler è necessario per convertire PDF in immagini.")
    print("\nIstruzioni per l'installazione:\n")
    print("Linux (Ubuntu/Debian):")
    print("  sudo apt-get update")
    print("  sudo apt-get install poppler-utils\n")
    print("macOS (con Homebrew):")
    print("  brew install poppler\n")
    print("Windows:")
    print("  1. Scarica i binari da:")
    print("     https://github.com/oschwartz10612/poppler-windows/releases/")
    print("  2. Estrai l'archivio")
    print("  3. Aggiungi la cartella 'bin' al PATH di sistema\n")
    print("="*70 + "\n")


def print_pymupdf_info():
    """Stampa le istruzioni per installare PyMuPDF."""
    print("\n" + "="*70)
    print("AVVISO: PyMuPDF non è installato!")
    print("="*70)
    print("\nPer usare l'opzione --no-annotations è necessario PyMuPDF.")
    print("\nInstallazione:\n")
    print("  pip install PyMuPDF\n")
    print("Oppure:")
    print("  pip install pymupdf\n")
    print("Il programma continuerà usando pdf2image (con annotazioni).")
    print("="*70 + "\n")


def sanitize_filename(filename):
    """
    Rimuove caratteri non supportati dai nomi file/cartelle.
    
    Args:
        filename: Nome del file da sanitizzare
        
    Returns:
        Nome file sanitizzato
    """
    name = Path(filename).stem
    vprint(f"[VERBOSE] Sanitizzazione nome file: '{name}'")
    sanitized = re.sub(r'[^\w\s-]', '_', name)
    sanitized = re.sub(r'\s+', '_', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    # Fallback se il nome diventa vuoto dopo la sanitizzazione (es. file "!!!.pdf")
    if not sanitized:
        sanitized = "documento"
    vprint(f"[VERBOSE] Nome file sanitizzato: '{sanitized}'")
    return sanitized


def parse_pages(pages_str, total_pages=None):
    """
    Interpreta la stringa --pages e restituisce un set di numeri di pagina (1-based).
    
    Formati supportati:
      {1-20}       → range inclusivo da 1 a 20
      {1,3,6,7}    → pagine specifiche
      1-20         → range senza parentesi
      1,3,6,7      → lista senza parentesi
    
    Args:
        pages_str: Stringa con il filtro pagine
        total_pages: Numero totale di pagine del PDF (per validazione opzionale)
        
    Returns:
        Set di interi con i numeri di pagina selezionati, ordinati
        
    Raises:
        ValueError se la sintassi non è valida
    """
    # Rimuovi spazi e parentesi quadre opzionali
    s = pages_str.strip().lstrip('{').rstrip('}').strip()
    
    if not s:
        raise ValueError("Stringa --pages vuota")
    
    pages = set()
    duplicates = set()
    
    # Supporta sia range (1-20) sia liste (1,3,6,7) sia misti (1,3-7,10)
    for part in s.split(','):
        part = part.strip()
        if '-' in part:
            bounds = part.split('-')
            if len(bounds) != 2:
                raise ValueError(f"Range non valido: '{part}'")
            try:
                start, end = int(bounds[0].strip()), int(bounds[1].strip())
            except ValueError:
                raise ValueError(f"Range non valido: '{part}' (valori non interi)")
            if start < 1 or end < start:
                raise ValueError(f"Range non valido: '{part}' (start deve essere ≥1 e ≤ end)")
            for n in range(start, end + 1):
                if n in pages:
                    duplicates.add(n)
                pages.add(n)
        else:
            try:
                n = int(part)
            except ValueError:
                raise ValueError(f"Numero pagina non valido: '{part}'")
            if n < 1:
                raise ValueError(f"Numero pagina non valido: {n} (deve essere ≥1)")
            if n in pages:
                duplicates.add(n)
            pages.add(n)
    
    if duplicates:
        print(f"[AVVISO] Pagine duplicate rimosse dall'input: {sorted(duplicates)}")
    
    if total_pages is not None:
        invalid = {p for p in pages if p > total_pages}
        if invalid:
            print(f"[AVVISO] Le seguenti pagine superano il totale ({total_pages}) e verranno ignorate: "
                  f"{sorted(invalid)}")
            pages -= invalid
    
    return sorted(pages)


def convert_single_page(pdf_path, page_num, output_path, dpi, image_format):
    """
    Converte una singola pagina del PDF in immagine.
    
    Args:
        pdf_path: Percorso del file PDF
        page_num: Numero della pagina (1-based)
        output_path: Percorso dove salvare l'immagine
        dpi: Risoluzione
        image_format: Formato immagine (jpg, png)
        
    Returns:
        Numero della pagina se successo, None altrimenti
    """
    global interrupted
    
    if interrupted:
        return None
    
    try:
        vprint(f"[VERBOSE] Thread: Conversione pagina {page_num} da {pdf_path.name}")
        
        # Converti SOLO questa pagina
        pages = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            first_page=page_num,
            last_page=page_num,
            thread_count=1
        )
        
        if not pages:
            vprint(f"[VERBOSE] Thread: ERRORE - Nessuna pagina restituita per pagina {page_num}")
            return None
        
        page = pages[0]
        vprint(f"[VERBOSE] Thread: Pagina {page_num} caricata, dimensioni: {page.size}")
        
        # Determina il formato di salvataggio
        if image_format.lower() in ['jpg', 'jpeg']:
            save_format = 'JPEG'
            # Converti in RGB se necessario (JPEG non supporta alpha channel)
            if page.mode in ('RGBA', 'LA', 'P'):
                vprint(f"[VERBOSE] Thread: Conversione pagina {page_num} da {page.mode} a RGB")
                page = page.convert('RGB')
        else:
            save_format = 'PNG'
        
        vprint(f"[VERBOSE] Thread: Salvataggio pagina {page_num} come {save_format} in {output_path}")
        page.save(output_path, save_format)
        vprint(f"[VERBOSE] Thread: Pagina {page_num} salvata con successo")
        
        return page_num
        
    except Exception as e:
        vprint(f"[VERBOSE] Thread: ERRORE nella conversione pagina {page_num}: {e}")
        return None


def convert_pdf_with_pymupdf(pdf_path, output_dir, dpi=300, max_workers=8, 
                             image_format='jpg', no_annotations=False,
                             pages_to_convert=None):
    """
    Converte PDF in immagini usando PyMuPDF (con controllo annotazioni).
    
    Args:
        pdf_path: Percorso del file PDF
        output_dir: Directory dove salvare le immagini
        dpi: Risoluzione delle immagini
        max_workers: Numero massimo di thread
        image_format: Formato immagine (jpg, png)
        no_annotations: Se True, rimuove le annotazioni
        pages_to_convert: Lista di numeri di pagina (1-based) da convertire, o None per tutte
        
    Returns:
        True se la conversione è riuscita, False altrimenti
    """
    global interrupted
    
    if interrupted:
        return False
    
    # Normalizza il formato
    file_extension = image_format.lower()
    if file_extension == 'jpeg':
        file_extension = 'jpg'
    
    vprint(f"[VERBOSE] Apertura PDF con PyMuPDF: {pdf_path}")
    
    try:
        # Apri il PDF
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        vprint(f"[VERBOSE] PDF aperto, totale pagine: {total_pages}")
        
        if total_pages == 0:
            print("  [ERRORE] Nessuna pagina trovata nel PDF.")
            doc.close()
            return False
        
        # Calcola il fattore di zoom per ottenere il DPI desiderato
        # PyMuPDF usa 72 DPI di default
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        vprint(f"[VERBOSE] Fattore di zoom calcolato: {zoom} (per {dpi} DPI)")
        
        # Determina le pagine da convertire
        if pages_to_convert is not None:
            pages_list = [p for p in pages_to_convert if 1 <= p <= total_pages]
            out_of_range = [p for p in pages_to_convert if p < 1 or p > total_pages]
            if out_of_range:
                print(f"  [AVVISO] Pagine fuori range (1-{total_pages}) ignorate: {out_of_range}")
            vprint(f"[VERBOSE] PyMuPDF: Pagine da convertire: {pages_list}")
        else:
            pages_list = list(range(1, total_pages + 1))

        n_to_convert = len(pages_list)
        if n_to_convert == 0:
            print("  [ERRORE] Nessuna pagina valida da convertire.")
            doc.close()
            return False

        print(f"[SALVATAGGIO] {n_to_convert} pagine in corso (totale PDF: {total_pages})...")
        
        saved_pages = 0
        
        with alive_bar(n_to_convert, title='  Progresso', bar='smooth') as bar:
            for page_num_1based in pages_list:
                page_num = page_num_1based - 1  # PyMuPDF usa indici 0-based
                if interrupted:
                    print("\n[INTERRUZIONE] Salvataggio interrotto")
                    break
                
                try:
                    vprint(f"[VERBOSE] PyMuPDF: Processamento pagina {page_num + 1}/{total_pages}")
                    page = doc[page_num]
                    
                    # Se no_annotations è True, rimuovi le annotazioni prima del rendering
                    if no_annotations:
                        vprint(f"[VERBOSE] PyMuPDF: Rimozione annotazioni dalla pagina {page_num + 1}")
                        # Ottieni tutte le annotazioni della pagina
                        annot = page.first_annot
                        annot_count = 0
                        while annot:
                            next_annot = annot.next
                            page.delete_annot(annot)
                            annot = next_annot
                            annot_count += 1
                        if annot_count > 0:
                            vprint(f"[VERBOSE] PyMuPDF: Rimosse {annot_count} annotazioni dalla pagina {page_num + 1}")
                    
                    # Renderizza la pagina
                    vprint(f"[VERBOSE] PyMuPDF: Rendering pagina {page_num + 1}")
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    vprint(f"[VERBOSE] PyMuPDF: Pixmap creato, dimensioni: {pix.width}x{pix.height}")
                    
                    # Salva l'immagine
                    output_path = output_dir / f"page_{page_num + 1:04d}.{file_extension}"
                    
                    if file_extension == 'png':
                        vprint(f"[VERBOSE] PyMuPDF: Salvataggio come PNG: {output_path}")
                        pix.save(str(output_path))
                    else:  # jpg/jpeg
                        # Per JPG, converti in RGB se necessario
                        if pix.n > 3:  # CMYK o altro
                            vprint(f"[VERBOSE] PyMuPDF: Conversione colorspace da n={pix.n} a RGB")
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        vprint(f"[VERBOSE] PyMuPDF: Salvataggio come JPEG: {output_path}")
                        pix.save(str(output_path), output='jpeg')
                    
                    saved_pages += 1
                    bar()
                    
                except Exception as e:
                    print(f"\n  [ERRORE] Pagina {page_num_1based}: {e}")
                    vprint(f"[VERBOSE] PyMuPDF: Traceback completo: {e}")
                    bar()
        
        doc.close()
        vprint(f"[VERBOSE] PyMuPDF: Documento chiuso")
        
        if interrupted:
            print(f"[PARZIALE] {saved_pages}/{n_to_convert} pagine salvate prima dell'interruzione\n")
            return False
        
        print(f"[COMPLETATO] {saved_pages}/{n_to_convert} immagini salvate\n")
        return True
        
    except Exception as e:
        print(f"  [ERRORE] Errore durante la conversione con PyMuPDF: {e}")
        vprint(f"[VERBOSE] PyMuPDF: Traceback completo: {e}")
        # Tenta di chiudere il documento se è stato aperto
        try:
            doc.close()
            vprint(f"[VERBOSE] PyMuPDF: Documento chiuso nel gestore eccezioni")
        except Exception:
            pass
        return False


def get_pdf_page_count(pdf_path):
    """
    Ottiene il numero di pagine del PDF usando pdfinfo.
    
    Args:
        pdf_path: Percorso del file PDF
        
    Returns:
        Numero di pagine o None se errore
    """
    vprint(f"[VERBOSE] Ottenimento numero pagine con pdfinfo per: {pdf_path}")
    try:
        import subprocess
        result = subprocess.run(
            ['pdfinfo', str(pdf_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        vprint(f"[VERBOSE] Output pdfinfo ricevuto")
        
        for line in result.stdout.split('\n'):
            if line.startswith('Pages:'):
                try:
                    page_count = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    vprint(f"[VERBOSE] ERRORE: Impossibile convertire il valore Pages in intero: '{line}'")
                    return None
                vprint(f"[VERBOSE] Numero pagine rilevato: {page_count}")
                return page_count
        
        vprint(f"[VERBOSE] ERRORE: Campo 'Pages:' non trovato nell'output di pdfinfo")
        return None
        
    except subprocess.TimeoutExpired:
        vprint(f"[VERBOSE] ERRORE: Timeout durante l'esecuzione di pdfinfo")
        return None
    except subprocess.CalledProcessError as e:
        vprint(f"[VERBOSE] ERRORE: pdfinfo terminato con codice {e.returncode}")
        return None
    except Exception as e:
        vprint(f"[VERBOSE] ERRORE: Eccezione durante pdfinfo: {e}")
        return None


def convert_pdf_to_images(pdf_path, output_base_dir, dpi=300, max_workers=8, 
                          image_format='jpg', no_annotations=False,
                          pages_to_convert=None, override=False):
    """
    Converte tutte le pagine (o un sottoinsieme) di un PDF in immagini usando threading ottimizzato.
    
    Args:
        pdf_path: Percorso del file PDF
        output_base_dir: Directory base dove salvare le immagini
        dpi: Risoluzione delle immagini (default: 300)
        max_workers: Numero massimo di thread (default: 8)
        image_format: Formato immagine (jpg, jpeg, png) (default: jpg)
        no_annotations: Se True, rimuove le annotazioni (richiede PyMuPDF)
        pages_to_convert: Lista di numeri pagina (1-based) da convertire, None = tutte
        override: Se True, la cartella col nome del PDF viene eliminata e ricreata
        
    Returns:
        True se la conversione è riuscita, False altrimenti
    """
    global interrupted
    
    if interrupted:
        print(f"[SALTATO] File '{pdf_path.name}' - operazione interrotta\n")
        return False
    
    pdf_path = Path(pdf_path)
    
    vprint(f"[VERBOSE] Inizio conversione PDF: {pdf_path}")
    
    if not pdf_path.exists():
        print(f"  [ERRORE] Il file '{pdf_path}' non esiste.")
        return False
    
    if not pdf_path.is_file():
        print(f"  [ERRORE] '{pdf_path}' non è un file.")
        return False
    
    vprint(f"[VERBOSE] File PDF verificato e accessibile")
    
    # Crea il nome della cartella sanitizzato
    folder_name = sanitize_filename(pdf_path.name)
    output_dir = output_base_dir / folder_name

    if override:
        if output_dir.exists():
            vprint(f"[VERBOSE] --override: Eliminazione cartella esistente: {output_dir}")
            print(f"[OVERRIDE] Cartella esistente eliminata: {output_dir}")
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        vprint(f"[VERBOSE] --override: Cartella ricreata: {output_dir}")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        vprint(f"[VERBOSE] Directory di output creata: {output_dir}")
    
    # Normalizza il formato (jpg -> jpg, jpeg -> jpg per consistenza nel nome file)
    file_extension = image_format.lower()
    if file_extension == 'jpeg':
        file_extension = 'jpg'
    
    vprint(f"[VERBOSE] Estensione file normalizzata: {file_extension}")
    
    print(f"\n[FILE] {pdf_path.name}")
    print(f"[OUTPUT] {output_dir}")
    print(f"[DPI] {dpi}")
    print(f"[THREADS] {max_workers}")
    print(f"[FORMATO] {file_extension.upper()}")
    if no_annotations:
        print(f"[ANNOTAZIONI] Disabilitate (solo contenuto originale)")
    else:
        print(f"[ANNOTAZIONI] Abilitate (include note e markup)")
    
    # Se richiesto no_annotations e PyMuPDF è disponibile, usa PyMuPDF
    if no_annotations and PYMUPDF_AVAILABLE:
        vprint(f"[VERBOSE] Utilizzo PyMuPDF per conversione (no_annotations richiesto)")
        return convert_pdf_with_pymupdf(
            pdf_path, output_dir, dpi, max_workers, image_format, no_annotations,
            pages_to_convert=pages_to_convert
        )
    elif no_annotations and not PYMUPDF_AVAILABLE:
        print("  [AVVISO] PyMuPDF non disponibile, converto con annotazioni")
        print("  [INFO] Installa PyMuPDF per usare --no-annotations: pip install PyMuPDF\n")
    
    # Altrimenti usa pdf2image con threading ottimizzato
    vprint(f"[VERBOSE] Utilizzo pdf2image per conversione")
    
    # Aumenta il limite PIL per immagini grandi
    vprint(f"[VERBOSE] Rimozione limite PIL MAX_IMAGE_PIXELS")
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    
    # Ottieni il numero di pagine senza caricare il PDF
    vprint(f"[VERBOSE] Rilevamento numero pagine del PDF...")
    total_pages = get_pdf_page_count(pdf_path)
    
    if total_pages is None:
        print("  [ERRORE] Impossibile determinare il numero di pagine del PDF")
        return False
    
    if total_pages == 0:
        print("  [ERRORE] Nessuna pagina trovata nel PDF.")
        return False
    
    # Determina le pagine effettive da convertire
    if pages_to_convert is not None:
        pages_list = [p for p in pages_to_convert if p <= total_pages]
        out_of_range = [p for p in pages_to_convert if p > total_pages]
        if out_of_range:
            print(f"  [AVVISO] Pagine fuori range ignorate: {out_of_range}")
        if not pages_list:
            print(f"  [ERRORE] Nessuna pagina valida da convertire.")
            return False
        print(f"  [PAGINE] Conversione pagine selezionate: {pages_list}")
    else:
        pages_list = list(range(1, total_pages + 1))
    
    pages_count = len(pages_list)
    
    print(f"[SALVATAGGIO] {pages_count} pagine in corso (threading ottimizzato)...")
    vprint(f"[VERBOSE] Creazione ThreadPoolExecutor con max_workers={max_workers}")
    
    saved_pages = 0
    failed_pages = []
    
    try:
        with alive_bar(pages_count, title='  Progresso', bar='smooth') as bar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                vprint(f"[VERBOSE] Invio {pages_count} task al pool di thread")
                
                # Crea un task per ogni pagina selezionata
                futures = {}
                for page_num in pages_list:
                    output_path = output_dir / f"page_{page_num:04d}.{file_extension}"
                    future = executor.submit(
                        convert_single_page,
                        pdf_path,
                        page_num,
                        output_path,
                        dpi,
                        image_format
                    )
                    futures[future] = page_num
                
                vprint(f"[VERBOSE] Tutti i task inviati, attesa completamento...")
                
                # Processa i risultati man mano che arrivano
                for future in as_completed(futures):
                    if interrupted:
                        vprint(f"[VERBOSE] Interruzione rilevata, cancellazione task rimanenti")
                        # Cancella tutti i task rimanenti
                        for f in futures:
                            f.cancel()
                        print("\n[INTERRUZIONE] Salvataggio interrotto")
                        break
                    
                    page_num = futures[future]
                    try:
                        result = future.result()
                        if result is not None:
                            saved_pages += 1
                            vprint(f"[VERBOSE] Pagina {page_num} completata con successo")
                        else:
                            failed_pages.append(page_num)
                            vprint(f"[VERBOSE] Pagina {page_num} FALLITA")
                        bar()
                    except Exception as e:
                        failed_pages.append(page_num)
                        print(f"\n  [ERRORE] Pagina {page_num}: {e}")
                        vprint(f"[VERBOSE] Eccezione durante il processing della pagina {page_num}: {e}")
                        bar()
                        
    except KeyboardInterrupt:
        print("\n[INTERRUZIONE] Conversione interrotta dall'utente")
        interrupted = True
        return False
    
    if interrupted:
        print(f"[PARZIALE] {saved_pages}/{pages_count} pagine salvate prima dell'interruzione\n")
        return False
    
    if failed_pages:
        print(f"[AVVISO] {len(failed_pages)} pagine non convertite: {failed_pages}")
    
    print(f"[COMPLETATO] {saved_pages}/{pages_count} immagini salvate\n")
    return saved_pages == pages_count


def find_pdf_files(pattern, use_regex=False):
    """
    Trova i file PDF che corrispondono al pattern.
    
    Args:
        pattern: Pattern per la ricerca (glob o regex)
        use_regex: Se True, usa regex invece di glob
        
    Returns:
        Lista di Path dei file PDF trovati
    """
    vprint(f"[VERBOSE] Ricerca file PDF con pattern: '{pattern}', regex={use_regex}")
    
    # Estrai il percorso della directory e il pattern del file
    pattern_path = Path(pattern)
    
    if pattern_path.is_absolute():
        base_dir = pattern_path.parent
        file_pattern = pattern_path.name
        vprint(f"[VERBOSE] Pattern assoluto - base_dir: {base_dir}, file_pattern: {file_pattern}")
    else:
        # Gestisce percorsi relativi
        if '/' in str(pattern) or '\\' in str(pattern):
            base_dir = Path.cwd() / pattern_path.parent
            file_pattern = pattern_path.name
            vprint(f"[VERBOSE] Pattern relativo con path - base_dir: {base_dir}, file_pattern: {file_pattern}")
        else:
            base_dir = Path.cwd()
            file_pattern = pattern
            vprint(f"[VERBOSE] Pattern semplice - base_dir: {base_dir}, file_pattern: {file_pattern}")
    
    # Verifica che la directory esista
    if not base_dir.exists():
        print(f"[ERRORE] La directory '{base_dir}' non esiste.")
        vprint(f"[VERBOSE] Directory non trovata: {base_dir}")
        return []
    
    vprint(f"[VERBOSE] Directory base verificata: {base_dir}")
    
    pdf_files = []
    
    if use_regex:
        # Usa regex per filtrare i file
        vprint(f"[VERBOSE] Utilizzo regex per pattern matching")
        try:
            regex_pattern = re.compile(file_pattern)
            vprint(f"[VERBOSE] Pattern regex compilato con successo")
        except re.error as e:
            print(f"[ERRORE] Pattern regex non valido: {e}")
            vprint(f"[VERBOSE] Errore compilazione regex: {e}")
            return []
        
        file_count = 0
        try:
            dir_iter = list(base_dir.iterdir())
        except PermissionError:
            print(f"[ERRORE] Permesso negato per accedere alla directory '{base_dir}'.")
            vprint(f"[VERBOSE] PermissionError su iterdir: {base_dir}")
            return []
        for file in dir_iter:
            file_count += 1
            if file.is_file() and file.suffix.lower() == '.pdf':
                if regex_pattern.search(file.name):
                    pdf_files.append(file)
                    vprint(f"[VERBOSE] Match regex: {file.name}")
        
        vprint(f"[VERBOSE] Scansionati {file_count} file nella directory")
    else:
        # Usa glob per filtrare i file
        vprint(f"[VERBOSE] Utilizzo glob per pattern matching")
        if '*' in file_pattern or '?' in file_pattern:
            pdf_files = list(base_dir.glob(file_pattern))
            vprint(f"[VERBOSE] Glob ha trovato {len(pdf_files)} match")
        else:
            # Se è un singolo file
            single_file = base_dir / file_pattern
            vprint(f"[VERBOSE] Pattern singolo file: {single_file}")
            if single_file.exists():
                pdf_files = [single_file]
                vprint(f"[VERBOSE] File singolo trovato")
            else:
                vprint(f"[VERBOSE] File singolo NON trovato")
    
    # Filtra solo i file PDF
    before_filter = len(pdf_files)
    pdf_files = [f for f in pdf_files if f.is_file() and f.suffix.lower() == '.pdf']
    vprint(f"[VERBOSE] Filtro PDF: {before_filter} -> {len(pdf_files)} file")
    
    sorted_files = sorted(pdf_files)
    vprint(f"[VERBOSE] File PDF ordinati alfabeticamente")
    
    return sorted_files


def main():
    global interrupted, VERBOSE
    
    # Registra il gestore del segnale per Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Descrizione dettagliata del programma
    description = """
PDF to Images Converter - Converte file PDF in immagini (JPG, JPEG, PNG)

Questo programma consente di convertire uno o più file PDF in immagini
ad alta risoluzione. Ogni PDF viene convertito in una serie di immagini
salvate in una cartella dedicata con il nome del file originale.

Il programma supporta:
  - Conversione di singoli file PDF
  - Batch processing con pattern glob (es. *.pdf)
  - Selezione tramite regex
  - Selezione di un range o lista di pagine (--pages)
  - Conversione multi-thread per prestazioni ottimali (una pagina per thread)
  - Configurazione personalizzata della risoluzione (DPI)
  - Formati di output: JPG, JPEG, PNG
  - Rimozione annotazioni/note (richiede PyMuPDF)
  - Modalità verbose per debugging dettagliato
"""

    # Epilogo con esempi dettagliati
    epilog = """
ESEMPI DI UTILIZZO:

  1. Convertire un singolo file PDF:
     %(prog)s documento.pdf

  2. Convertire tutti i PDF nella cartella corrente:
     %(prog)s "*.pdf"

  3. Convertire solo le pagine 1-20:
     %(prog)s documento.pdf --pages "{1-20}"

  4. Convertire solo le pagine 1, 3, 6 e 7:
     %(prog)s documento.pdf --pages "{1,3,6,7}"

  5. Selezione mista (range + singole):
     %(prog)s documento.pdf -p "{1,3,5-10,15}"

  6. Convertire PDF senza annotazioni/note:
     %(prog)s documento.pdf --no-annotations

  7. Convertire con risoluzione personalizzata (600 DPI):
     %(prog)s documento.pdf --dpi 600

  8. Modalità verbose per vedere tutti i dettagli:
     %(prog)s documento.pdf -v

  9. Usare regex per selezionare file (solo quelli che iniziano con numeri):
     %(prog)s "^[0-9].*\\.pdf$" --regex

  10. Salvare come PNG senza annotazioni:
     %(prog)s "*.pdf" --format png --no-annotations

  11. Combinare tutte le opzioni:
     %(prog)s "*.pdf" -v --format png --dpi 300 --threads 4 --output ./output --no-annotations --pages "{1-10}"

NOTE:
  - Formati supportati: jpg, jpeg, png
  - JPG: Più compresso, file più piccoli, ideale per documenti
  - PNG: Senza perdita, file più grandi, ideale per grafici e diagrammi
  - Le immagini vengono salvate come page_0001.jpg, page_0002.jpg, ecc.
  - Con --pages i nomi file rispecchiano il numero pagina originale del PDF
  - Output standard: Exported/DDMMYYYYHHMMSS/nome_file/
  - Con --output: percorso_output/DDMMYYYYHHMMSS/nome_file/
  - Con --override: Exported/nome_file/ (senza timestamp; elimina e ricrea se esiste)
  - Quando si usano pattern con *, racchiuderli tra virgolette
  - Il programma richiede poppler-utils installato nel sistema
  - DPI più alti producono immagini di qualità superiore ma più grandi
  - L'opzione --no-annotations richiede PyMuPDF (pip install PyMuPDF)
  - Threading ottimizzato: una pagina per thread, niente out-of-memory!

REQUISITI:
  pip install pdf2image alive-progress
  pip install PyMuPDF  # Opzionale, per --no-annotations
  
  Installazione di Poppler:
    - Linux: sudo apt-get install poppler-utils
    - macOS: brew install poppler
    - Windows: Scaricare da https://github.com/oschwartz10612/poppler-windows

VERSIONI TESTATE:
  Pacchetti Python:
    - pdf2image: 1.17.0
    - alive-progress: 3.3.0
    - PyMuPDF: 1.24.0+ (opzionale)
  
  Dipendenza di Sistema:
    - Python: 3.13.11
    - Poppler (pdftoppm): 26.01.0
"""

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='pdf_to_images'
    )
    
    parser.add_argument(
        'pattern',
        nargs='+',
        help='File PDF, pattern glob (es. "*.pdf"), o percorso con pattern. '
             'Supporta percorsi relativi come "cartella/*.pdf" o "../docs/file*.pdf". '
             'Può accettare anche multipli file o pattern'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        metavar='N',
        help='Risoluzione delle immagini in DPI (dots per inch). '
             'Valori comuni: 150 (bassa), 300 (standard), 600 (alta). '
             'Default: 300'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=8,
        metavar='N',
        help='Numero massimo di thread da utilizzare per la conversione parallela. '
             'Ogni thread processa una pagina alla volta (ottimizzato per memoria). '
             'Valori consigliati: 4-8 per la maggior parte dei sistemi. '
             'Range valido: 1-32. Default: 8'
    )
    
    parser.add_argument(
        '--regex',
        action='store_true',
        help='Usa regex invece di glob per la selezione dei file. '
             'Il pattern viene interpretato come espressione regolare. '
             'Esempio: "^report_.*\\.pdf$" seleziona file che iniziano con "report_"'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        metavar='PATH',
        help='Directory di output personalizzata (percorso assoluto o relativo). '
             'Se non specificato, usa "Exported" nella directory corrente. '
             'All\'interno verrà creata una sottocartella con timestamp DDMMYYYYHHMMSS'
    )
    
    parser.add_argument(
        '--format', '-f',
        type=str,
        default='jpg',
        choices=['jpg', 'jpeg', 'png'],
        metavar='FORMAT',
        help='Formato delle immagini di output: jpg, jpeg, o png. '
             'JPG/JPEG: compresso, file più piccoli. '
             'PNG: senza perdita, file più grandi. '
             'Default: jpg'
    )
    
    parser.add_argument(
        '--pages', '-p',
        type=str,
        default=None,
        metavar='SELEZIONE',
        help='Seleziona le pagine da convertire. '
             'Range: "{1-20}" (estremi inclusi). '
             'Lista: "{1,3,6,7}". '
             'Misto: "{1,3,5-10,15}". '
             'Le parentesi graffe sono opzionali. '
             'Se non specificato, converte tutte le pagine.'
    )
    
    parser.add_argument(
        '--no-annotations',
        action='store_true',
        help='Rimuove tutte le annotazioni, note e markup dal PDF prima della conversione. '
             'Esporta solo il contenuto originale del documento. '
             'RICHIEDE PyMuPDF: pip install PyMuPDF'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Abilita output verbose. Mostra informazioni dettagliate su ogni operazione '
             'e passaggio del programma per debugging e monitoraggio avanzato.'
    )
    
    parser.add_argument(
        '--override',
        action='store_true',
        help='Modalità override: salva le immagini direttamente in una cartella col nome del PDF '
             '(senza sottocartella timestamp). Se la cartella esiste già, viene eliminata e ricreata.'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 3.0'
    )
    
    args = parser.parse_args()
    
    # Imposta verbose globalmente
    VERBOSE = args.verbose
    
    if VERBOSE:
        print("[VERBOSE] === MODALITÀ VERBOSE ATTIVATA ===")
        print(f"[VERBOSE] Argomenti ricevuti: {vars(args)}")
    
    # Validazione argomenti
    vprint("[VERBOSE] Validazione argomenti...")
    
    if args.dpi <= 0:
        print("[ERRORE] DPI deve essere un valore positivo.")
        sys.exit(1)
    
    vprint(f"[VERBOSE] DPI validato: {args.dpi}")
    
    if args.threads <= 0 or args.threads > 32:
        print("[ERRORE] Il numero di thread deve essere tra 1 e 32.")
        sys.exit(1)
    
    vprint(f"[VERBOSE] Threads validati: {args.threads}")
    
    # Normalizza il formato immagine
    image_format = args.format.lower()
    if image_format not in ['jpg', 'jpeg', 'png']:
        print("[ERRORE] Formato non valido. Usa: jpg, jpeg, o png")
        sys.exit(1)
    
    vprint(f"[VERBOSE] Formato immagine validato: {image_format}")
    
    # Parsing del flag --pages (se specificato)
    pages_to_convert = None
    if args.pages is not None:
        vprint(f"[VERBOSE] Parsing --pages: {args.pages}")
        try:
            pages_to_convert = parse_pages(args.pages)
        except ValueError as e:
            print(f"[ERRORE] Valore non valido per --pages: {e}")
            print("[INFO] Esempi validi: {1-20}, {1,3,6,7}, {1,3-7,10}, 1-20, 1,3,6,7")
            sys.exit(1)
        vprint(f"[VERBOSE] Pagine da convertire: {pages_to_convert}")
        print(f"[PAGINE] Selezione specificata: {pages_to_convert}")
        print()
    
    # Verifica PyMuPDF se richiesto --no-annotations
    if args.no_annotations and not PYMUPDF_AVAILABLE:
        vprint("[VERBOSE] --no-annotations richiesto ma PyMuPDF non disponibile")
        print_pymupdf_info()
        print("[AVVISO] Continuazione con annotazioni abilitate...")
        print()
    elif args.no_annotations and PYMUPDF_AVAILABLE:
        vprint("[VERBOSE] --no-annotations richiesto e PyMuPDF disponibile")
    
    try:
        # Verifica che poppler sia installato
        print("[VERIFICA] Controllo installazione di Poppler...")
        if not check_poppler():
            print_poppler_installation_guide()
            sys.exit(1)
        print("[OK] Poppler installato correttamente")
        
        if PYMUPDF_AVAILABLE:
            print("[OK] PyMuPDF disponibile (supporto --no-annotations)")
            vprint(f"[VERBOSE] Versione PyMuPDF: {fitz.version}")
        else:
            print("[INFO] PyMuPDF non installato (opzionale per --no-annotations)")
        print()
        
        # Crea la directory di output
        if args.output:
            # Usa il percorso specificato dall'utente
            base_output = Path(args.output)
            vprint(f"[VERBOSE] Output personalizzato specificato: {args.output}")
            if not base_output.is_absolute():
                # Se è relativo, lo rende relativo alla directory corrente
                base_output = Path.cwd() / base_output
                vprint(f"[VERBOSE] Percorso relativo convertito in assoluto: {base_output}")
        else:
            # Usa la directory Exported di default
            base_output = Path.cwd() / "Exported"
            vprint(f"[VERBOSE] Utilizzo directory di output default: {base_output}")

        if args.override:
            # Modalità override: nessuna sottocartella timestamp, usa direttamente base_output
            # La directory per ogni PDF verrà creata (o ricreata) in convert_pdf_to_images
            vprint("[VERBOSE] Modalità --override attiva: nessuna sottocartella timestamp")
            base_output.mkdir(parents=True, exist_ok=True)
            output_dir = base_output
            print(f"[OUTPUT BASE] {output_dir}")
            print(f"[MODALITÀ OUTPUT] Override (cartella per nome PDF, senza timestamp)")
        else:
            # Comportamento standard: sottocartella con timestamp
            vprint("[VERBOSE] Creazione directory di output con timestamp...")
            current_time = datetime.now()
            timestamp = current_time.strftime("%d%m%Y%H%M%S")
            vprint(f"[VERBOSE] Timestamp generato: {timestamp}")

            # Crea la directory base se non esiste
            vprint(f"[VERBOSE] Creazione directory base: {base_output}")
            base_output.mkdir(parents=True, exist_ok=True)

            # Crea la sottocartella con timestamp
            output_dir = base_output / timestamp
            vprint(f"[VERBOSE] Creazione sottocartella con timestamp: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"[OUTPUT BASE] {output_dir}")
            print(f"[TIMESTAMP] {timestamp} ({current_time.strftime('%d/%m/%Y %H:%M:%S')})")
        print(f"[FORMATO IMMAGINI] {image_format.upper()}")
        if args.no_annotations:
            if PYMUPDF_AVAILABLE:
                print(f"[MODALITÀ] Senza annotazioni (PyMuPDF)")
            else:
                print(f"[MODALITÀ] Con annotazioni (PyMuPDF non disponibile)")
        else:
            print(f"[MODALITÀ] Con annotazioni")
        if pages_to_convert is not None:
            print(f"[PAGINE] Selezione: {pages_to_convert}")
        else:
            print(f"[PAGINE] Tutte")
        if VERBOSE:
            print(f"[MODALITÀ] VERBOSE ATTIVO - Logging dettagliato abilitato")
        print()
        
        # Raccogli tutti i file PDF da tutti i pattern forniti
        vprint("[VERBOSE] Inizio raccolta file PDF dai pattern...")
        all_pdf_files = []
        
        # Se c'è un solo pattern, usa la funzione esistente
        if len(args.pattern) == 1:
            print(f"[RICERCA] Pattern: {args.pattern[0]}")
            if args.regex:
                print("[MODALITÀ] Regex abilitata")
            
            vprint(f"[VERBOSE] Pattern singolo rilevato: {args.pattern[0]}")
            pdf_files = find_pdf_files(args.pattern[0], use_regex=args.regex)
            all_pdf_files.extend(pdf_files)
            vprint(f"[VERBOSE] Trovati {len(pdf_files)} file dal pattern")
        else:
            # Multipli argomenti: potrebbero essere file espansi dalla shell o pattern multipli
            print(f"[RICERCA] {len(args.pattern)} pattern/file specificati")
            vprint(f"[VERBOSE] Pattern multipli rilevati: {args.pattern}")
            
            for idx, pattern in enumerate(args.pattern, 1):
                vprint(f"[VERBOSE] Processing pattern {idx}/{len(args.pattern)}: {pattern}")
                # Controlla se è un file PDF esistente (espanso dalla shell)
                p = Path(pattern)
                if p.exists() and p.is_file() and p.suffix.lower() == '.pdf':
                    all_pdf_files.append(p)
                    vprint(f"[VERBOSE] Pattern è un file esistente: {p}")
                else:
                    # Altrimenti tratta come pattern
                    vprint(f"[VERBOSE] Pattern non è un file, cerco match...")
                    pdf_files = find_pdf_files(pattern, use_regex=args.regex)
                    all_pdf_files.extend(pdf_files)
                    vprint(f"[VERBOSE] Trovati {len(pdf_files)} file dal pattern")
        
        # Rimuovi duplicati mantenendo l'ordine
        vprint("[VERBOSE] Rimozione duplicati...")
        seen = set()
        pdf_files = []
        for pdf in all_pdf_files:
            if pdf not in seen:
                seen.add(pdf)
                pdf_files.append(pdf)
            else:
                vprint(f"[VERBOSE] Duplicato rimosso: {pdf}")
        
        vprint(f"[VERBOSE] File PDF unici dopo deduplicazione: {len(pdf_files)}")
        
        if not pdf_files:
            print(f"[ERRORE] Nessun file PDF trovato")
            vprint(f"[VERBOSE] Terminazione programma: nessun file da processare")
            # Elimina la cartella timestamp appena creata se è vuota (non in modalità --override)
            if not args.override and output_dir.exists() and not any(output_dir.iterdir()):
                vprint(f"[VERBOSE] Eliminazione cartella vuota: {output_dir}")
                output_dir.rmdir()
                print(f"[PULIZIA] Cartella vuota eliminata: {output_dir}")
            sys.exit(1)
        
        print(f"[TROVATI] {len(pdf_files)} file PDF:")
        for pdf in pdf_files:
            print(f"  - {pdf}")
        print()
        
        # Converti tutti i file
        vprint(f"[VERBOSE] Inizio conversione di {len(pdf_files)} file...")
        successful = 0
        failed = 0
        skipped = 0
        
        for i, pdf_file in enumerate(pdf_files, start=1):
            if interrupted:
                skipped = len(pdf_files) - i + 1
                print(f"\n[INTERRUZIONE] Saltati {skipped} file rimanenti")
                vprint(f"[VERBOSE] Interruzione rilevata, {skipped} file non processati")
                break
            
            print(f"{'='*70}")
            print(f"File {i}/{len(pdf_files)}")
            print(f"{'='*70}")
            vprint(f"[VERBOSE] === Inizio conversione file {i}/{len(pdf_files)}: {pdf_file.name} ===")
            
            if convert_pdf_to_images(pdf_file, output_dir, args.dpi, args.threads, 
                                    image_format, args.no_annotations,
                                    pages_to_convert=pages_to_convert,
                                    override=args.override):
                successful += 1
                vprint(f"[VERBOSE] File {i} completato con SUCCESSO")
            else:
                failed += 1
                vprint(f"[VERBOSE] File {i} FALLITO")
        
        # Riepilogo finale
        print(f"{'='*70}")
        print(f"RIEPILOGO CONVERSIONI")
        print(f"{'='*70}")
        print(f"[RIUSCITE] {successful}")
        if failed > 0:
            print(f"[FALLITE] {failed}")
        if skipped > 0:
            print(f"[SALTATE] {skipped}")
        print(f"[TOTALE] {len(pdf_files)}")
        print(f"{'='*70}\n")
        
        vprint(f"[VERBOSE] === RIEPILOGO FINALE ===")
        vprint(f"[VERBOSE] Riuscite: {successful}")
        vprint(f"[VERBOSE] Fallite: {failed}")
        vprint(f"[VERBOSE] Saltate: {skipped}")
        vprint(f"[VERBOSE] Totale: {len(pdf_files)}")
        
        if interrupted:
            print("[INFO] Programma terminato dall'utente")
            vprint("[VERBOSE] Exit code: 130 (SIGINT)")
            sys.exit(130)  # Codice di uscita standard per SIGINT
        
        vprint("[VERBOSE] Programma completato con successo")
        vprint("[VERBOSE] Exit code: 0")
            
    except KeyboardInterrupt:
        print("\n\n[INTERRUZIONE] Programma terminato forzatamente")
        print("[INFO] Operazione annullata dall'utente\n")
        vprint("[VERBOSE] KeyboardInterrupt catturato nel main")
        vprint("[VERBOSE] Exit code: 130")
        sys.exit(130)


if __name__ == '__main__':
    main()
