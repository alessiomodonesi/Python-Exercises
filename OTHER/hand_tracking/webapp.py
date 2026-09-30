# --- 1. IMPORTAZIONE DELLE LIBRERIE ---

# Da 'flask', importiamo le classi e funzioni necessarie:
# - Flask: il nucleo del nostro framework web per creare il server.
# - render_template: serve a caricare e servire i file HTML dalla cartella 'templates'.
# - Response: è usato per creare una risposta HTTP di tipo streaming, essenziale per il nostro video.
from flask import Flask, render_template, Response

# Da 'flask_socketio', importiamo le classi per la comunicazione in tempo reale (WebSocket):
# - SocketIO: estende Flask per gestire i WebSockets, permettendo una comunicazione bidirezionale.
# - emit: è la funzione usata per inviare messaggi (eventi) dal server al browser.
from flask_socketio import SocketIO, emit

# cv2 è la libreria OpenCV, il nostro strumento principale per la computer vision:
# catturare il video, manipolare le immagini (convertire colori, specchiare), e disegnarci sopra.
import cv2

# mediapipe è la libreria di Google che ci fornisce il modello di machine learning pre-allenato
# per il riconoscimento dei punti chiave (landmark) della mano.
import mediapipe as mp

# math ci fornisce funzioni matematiche di base, come la radice quadrata (sqrt),
# che usiamo per calcolare la distanza tra le dita.
import math


# --- 2. INIZIALIZZAZIONE DELL'APPLICAZIONE ---

# Crea l'oggetto principale dell'applicazione Flask. `__name__` è una variabile speciale
# di Python che aiuta Flask a localizzare le risorse come i template.
app = Flask(__name__)

# Imposta una "chiave segreta", una stringa casuale necessaria a Flask per
# gestire in modo sicuro le sessioni e altre funzionalità, inclusa SocketIO.
app.config['SECRET_KEY'] = 'la-mia-chiave-super-segreta!'

# Inizializza SocketIO, avvolgendo l'applicazione Flask per aggiungergli
# le capacità di comunicazione WebSocket.
socketio = SocketIO(app)


# --- 3. GESTIONE DELLO STATO ---

# Definiamo una variabile globale che funge da interruttore per il riconoscimento.
# Se `True`, il server cercherà attivamente i gesti.
# Se `False`, si limiterà a visualizzare lo scheletro della mano.
# Questa variabile viene modificata dal browser tramite un evento WebSocket.
is_recognizing = False


# --- 4. CONFIGURAZIONE DI MEDIAPIPE E OPENCV ---

# Creiamo due "specifiche di disegno" personalizzate per un look più accattivante dell'overlay.
# `DrawingSpec` è una classe di MediaPipe che permette di definire l'aspetto di punti e linee.
# Stile per i landmark (i 21 punti): colore magenta (RGB: 255,0,128), spessore 2, raggio del cerchio 2.
landmark_style = mp.solutions.drawing_utils.DrawingSpec(color=(255, 0, 128), thickness=2, circle_radius=2)
# Stile per le connessioni (le linee tra i punti): colore ciano (RGB: 0,255,255), spessore 2.
connection_style = mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2)

# Inizializza la soluzione "Hands" di MediaPipe, che contiene il modello AI vero e proprio.
mp_hands = mp.solutions.hands

# Inizializza l'oggetto di cattura video di OpenCV. L'argomento `0` si riferisce
# alla webcam predefinita del computer. Se avessi più webcam, potresti usare 1, 2, ecc.
cap = cv2.VideoCapture(0)


# --- 5. FUNZIONE PER LO STREAMING VIDEO E LA LOGICA AI ---

def generate_frames():
    """
    Funzione generatore che produce un flusso di frame video elaborati.
    Viene eseguita in un loop continuo finché il server è attivo e un client è connesso.
    """
    # Dichiara che vogliamo leggere e modificare la variabile globale `is_recognizing`
    # dall'interno di questa funzione.
    global is_recognizing
    
    # Inizializza il modello `Hands` usando un blocco `with`. Questo è il modo raccomandato
    # perché gestisce automaticamente l'allocazione e il rilascio delle risorse del modello.
    # `min_detection_confidence`: soglia di confidenza per rilevare una mano in un'immagine (70%).
    # `min_tracking_confidence`: soglia per continuare a tracciare una mano già rilevata (50%).
    with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5) as hands:
        # Il loop infinito che costituisce il cuore dell'applicazione in tempo reale.
        while True:
            # Legge un singolo frame dalla webcam. 'success' è un booleano, 'frame' è l'immagine (array NumPy).
            success, frame = cap.read()
            if not success:
                # Se la lettura del frame fallisce (es. webcam disconnessa), interrompe il ciclo.
                break
            
            # --- PRE-ELABORAZIONE DEL FRAME ---
            # 1. `cv2.flip(frame, 1)`: Specchia l'immagine orizzontalmente. L'argomento `1` indica il flip orizzontale.
            # 2. `cv2.cvtColor(...)`: Converte lo spazio colore da BGR (formato standard di OpenCV) a RGB (richiesto da MediaPipe).
            frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            
            # --- INFERENZA DEL MODELLO ---
            # `hands.process(frame)`: Qui avviene la magia. Il frame viene passato al modello AI
            # che rileva le mani e calcola la posizione dei 21 landmark per ciascuna.
            results = hands.process(frame)

            # Riconvertiamo il frame in BGR per poter usare le funzioni di disegno di OpenCV, che si aspettano questo formato.
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Inizializza una stringa vuota per il nome dell'azione.
            action = ""

            # Controlla se il modello ha trovato almeno una mano (`multi_hand_landmarks` è una lista non vuota).
            if results.multi_hand_landmarks:
                # Itera su ogni mano trovata nel frame (potrebbero essercene più di una).
                for hand_landmarks in results.multi_hand_landmarks:
                    # Disegna SEMPRE lo scheletro della mano, usando gli stili personalizzati.
                    # Questo viene fatto ad ogni frame, indipendentemente dallo stato di 'is_recognizing'.
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        landmark_style,
                        connection_style
                    )

                    # Esegue la logica di riconoscimento del gesto SOLO se l'utente ha premuto il bottone (`is_recognizing` è True).
                    if is_recognizing:
                        # Estrae la lista dei 21 landmark per la mano corrente.
                        landmarks = hand_landmarks.landmark
                        # Estrae le coordinate della punta del pollice (landmark numero 4).
                        thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
                        # Crea un dizionario per mappare i numeri delle dita (2-5) ai loro landmark corrispondenti.
                        finger_tip_ids = {2: mp_hands.HandLandmark.INDEX_FINGER_TIP, 3: mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP, 4: mp.solutions.hands.HandLandmark.RING_FINGER_TIP, 5: mp.solutions.hands.HandLandmark.PINKY_TIP}
                        
                        # Itera sulle dita (indice, medio, anulare, mignolo).
                        for finger_num, tip_id in finger_tip_ids.items():
                            finger_tip = landmarks[tip_id]
                            # Calcola la distanza Euclidea 2D tra la punta del pollice e quella del dito corrente.
                            # Le coordinate x e y sono normalizzate (da 0.0 a 1.0), quindi la distanza è relativa alla dimensione dell'immagine.
                            distance = math.sqrt((thumb_tip.x - finger_tip.x)**2 + (thumb_tip.y - finger_tip.y)**2)
                            
                            # Soglia di distanza per considerare un "tocco". Questo valore è stato trovato empiricamente.
                            touch_threshold = 0.05
                            
                            # Se la distanza è sotto la soglia, abbiamo un'azione.
                            if distance < touch_threshold:
                                action_num = finger_num - 1 # Converte il numero del dito (2-5) in numero di azione (1-4).
                                action = f"Azione {action_num} Rilevata" # Prepara una stringa per il log.
                                
                                # Invia l'azione al browser tramite un evento WebSocket chiamato 'action_log'.
                                # Il payload è un dizionario JSON.
                                socketio.emit('action_log', {'data': action})
                                
                                # Disattiva subito il riconoscimento per evitare azioni multiple e accidentali.
                                # L'utente dovrà premere di nuovo il bottone per un'altra azione.
                                is_recognizing = False
                                break # Interrompe il ciclo delle dita, non serve controllarne altre.
                        if action:
                            break # Interrompe il ciclo delle mani se un'azione è stata trovata.
            
            # --- STREAMING DEL FRAME AL BROWSER ---
            # Codifica il frame (con i disegni sopra) in formato JPEG in memoria.
            ret, buffer = cv2.imencode('.jpg', frame)
            # Converte l'immagine codificata in un array di bytes.
            frame_bytes = buffer.tobytes()
            # `yield` è la parola chiave che rende questa funzione un generatore.
            # Invia il frame al client, formattato secondo lo standard dello streaming MJPEG.
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- 6. ROUTING E GESTIONE DEGLI EVENTI ---

# Il decoratore `@app.route('/')` collega l'URL principale del sito ("/") alla funzione `index`.
@app.route('/')
def index():
    # Questa funzione semplicemente carica e restituisce il file 'index.html' al browser.
    return render_template('index.html')

# Il decoratore `@app.route('/video_feed')` collega questo URL allo streaming.
# L'HTML userà questo URL nell'attributo `src` del tag `<img>`.
@app.route('/video_feed')
def video_feed():
    # Restituisce una 'Response' di tipo streaming, che esegue la nostra funzione generatore.
    # Il mimetype `multipart/x-mixed-replace` dice al browser di aspettarsi un flusso di dati
    # che si aggiornano continuamente (il nostro video).
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Il decoratore `@socketio.on(...)` registra una funzione per gestire un evento WebSocket
# specifico inviato dal client JavaScript.
@socketio.on('toggle_recognition')
def handle_toggle_recognition():
    """Questa funzione viene eseguita quando il server riceve l'evento 'toggle_recognition' dal browser."""
    global is_recognizing
    # Attiva l'interruttore del riconoscimento (solo se era spento).
    if not is_recognizing:
        is_recognizing = True
        print("Riconoscimento ATTIVATO.") # Log sul terminale del server per debug.

# --- 7. AVVIO DELL'APPLICAZIONE ---

# Questo blocco di codice standard in Python assicura che il server venga avviato
# solo quando lo script viene eseguito direttamente (e non quando viene importato da un altro script).
if __name__ == '__main__':
    # `socketio.run()` avvia il server web. È una versione potenziata di `app.run()`
    # che include il supporto per i WebSockets.
    # `host='0.0.0.0'` rende il server accessibile da altri dispositivi sulla stessa rete locale.
    # `port=8888` imposta la porta su cui il server si mette in ascolto.
    # `debug=True` attiva la modalità di debug, che ricarica automaticamente il server ad ogni modifica
    # del codice e mostra errori dettagliati nel browser. Da non usare in produzione!
    socketio.run(app, host='0.0.0.0', port=8888, debug=True)