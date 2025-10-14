# --- 1. IMPORTAZIONE DELLE LIBRERIE ---
# Flask è il framework web che usiamo per creare il server.
# render_template serve a caricare i file HTML.
# Response è usato per inviare lo streaming video.
from flask import Flask, render_template, Response
# Flask-SocketIO gestisce la comunicazione in tempo reale (WebSocket) tra server e browser.
from flask_socketio import SocketIO, emit
# cv2 è la libreria OpenCV, usata per catturare e manipolare le immagini dalla webcam.
import cv2
# mediapipe è la libreria di Google per il riconoscimento della mano.
import mediapipe as mp
# math ci serve per calcoli matematici, come la radice quadrata per la distanza.
import math

# --- 2. INIZIALIZZAZIONE DELL'APPLICAZIONE ---
# Crea un'istanza dell'applicazione Flask.
app = Flask(__name__)
# Imposta una chiave segreta, necessaria a Flask-SocketIO per funzionare in modo sicuro.
app.config['SECRET_KEY'] = 'la-mia-chiave-super-segreta!'
# Inizializza SocketIO, legandolo alla nostra app Flask.
socketio = SocketIO(app)

# --- 3. GESTIONE DELLO STATO ---
# Una variabile globale che funge da interruttore.
# Se True, il server cerca di riconoscere i gesti. Se False, disegna solo i punti.
is_recognizing = False

# --- 4. CONFIGURAZIONE DI MEDIAPIPE E OPENCV ---
# Crea due "specifiche di disegno" personalizzate per l'overlay della mano.
# landmark_style: definisce l'aspetto dei 21 punti (colore magenta, spessore 2, raggio 2).
landmark_style = mp.solutions.drawing_utils.DrawingSpec(color=(255, 0, 128), thickness=2, circle_radius=2)
# connection_style: definisce l'aspetto delle linee di connessione (colore ciano, spessore 2).
connection_style = mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2)

# Carica il modello pre-allenato per il riconoscimento della mano.
mp_hands = mp.solutions.hands
# Inizializza l'oggetto per catturare il video dalla webcam predefinita (indice 0).
cap = cv2.VideoCapture(0)

# --- 5. FUNZIONE PER LO STREAMING VIDEO E LA LOGICA AI ---
def generate_frames():
    """
    Funzione generatore che produce un flusso di frame video elaborati.
    Viene eseguita in un loop continuo finché il server è attivo.
    """
    # Dichiara che useremo la variabile globale 'is_recognizing' per poterla modificare.
    global is_recognizing
    
    # Inizializza il modello di MediaPipe con i parametri di confidenza.
    # Questo blocco 'with' gestisce l'allocazione e il rilascio delle risorse del modello.
    with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5) as hands:
        # Loop infinito per catturare e processare i frame.
        while True:
            # Legge un singolo frame dalla webcam. 'success' è un booleano, 'frame' è l'immagine.
            success, frame = cap.read()
            if not success:
                # Se non riesce a leggere un frame, interrompe il ciclo.
                break
            
            # --- PRE-ELABORAZIONE DELL'IMMAGINE ---
            # Specchia l'immagine orizzontalmente per un effetto "selfie" più naturale.
            # Converte i colori da BGR (formato di OpenCV) a RGB (formato di MediaPipe).
            frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            
            # --- INFERENZA DEL MODELLO ---
            # Passa il frame al modello MediaPipe. Questa è l'operazione di AI vera e propria.
            results = hands.process(frame)

            # Riconverte il frame in BGR per poterlo visualizzare e disegnare con OpenCV.
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Inizializza una stringa vuota per il nome dell'azione.
            action = ""

            # Controlla se il modello ha rilevato almeno una mano.
            if results.multi_hand_landmarks:
                # Itera su ogni mano trovata nel frame.
                for hand_landmarks in results.multi_hand_landmarks:
                    # Disegna sempre i punti e le connessioni, usando gli stili personalizzati.
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        landmark_style,
                        connection_style
                    )

                    # Esegue la logica di riconoscimento del gesto solo se l'interruttore è attivo.
                    if is_recognizing:
                        landmarks = hand_landmarks.landmark
                        thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
                        finger_tip_ids = {2: mp_hands.HandLandmark.INDEX_FINGER_TIP, 3: mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP, 4: mp.solutions.hands.HandLandmark.RING_FINGER_TIP, 5: mp.solutions.hands.HandLandmark.PINKY_TIP}
                        
                        # Itera sulle dita (indice, medio, anulare, mignolo).
                        for finger_num, tip_id in finger_tip_ids.items():
                            finger_tip = landmarks[tip_id]
                            # Calcola la distanza tra la punta del pollice e quella del dito corrente.
                            distance = math.sqrt((thumb_tip.x - finger_tip.x)**2 + (thumb_tip.y - finger_tip.y)**2)
                            
                            touch_threshold = 0.05 # Soglia per considerare un "tocco".
                            
                            # Se la distanza è sotto la soglia, abbiamo un'azione.
                            if distance < touch_threshold:
                                action_num = finger_num - 1
                                action = f"Azione {action_num} Rilevata"
                                
                                # Invia l'azione al browser tramite un evento WebSocket chiamato 'action_log'.
                                socketio.emit('action_log', {'data': action})
                                
                                # Disattiva il riconoscimento per evitare rilevamenti multipli.
                                is_recognizing = False
                                break # Interrompe il ciclo delle dita.
                        if action:
                            break # Interrompe il ciclo delle mani se un'azione è stata trovata.
            
            # --- STREAMING DEL FRAME ---
            # Codifica il frame elaborato in formato JPEG.
            ret, buffer = cv2.imencode('.jpg', frame)
            # Converte il buffer in bytes.
            frame_bytes = buffer.tobytes()
            # 'yield' invia il frame al browser nel formato speciale per lo streaming (MJPEG).
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# --- 6. ROUTING E GESTIONE DEGLI EVENTI ---
# Definisce la route per la pagina principale ('/').
@app.route('/')
def index():
    # Carica e restituisce il file 'index.html' dalla cartella 'templates'.
    return render_template('index.html')

# Definisce la route per lo stream video.
@app.route('/video_feed')
def video_feed():
    # Restituisce una risposta di tipo 'streaming' che esegue la funzione generatore.
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Definisce un gestore di eventi per SocketIO.
# Si mette in ascolto dell'evento 'toggle_recognition' inviato dal browser.
@socketio.on('toggle_recognition')
def handle_toggle_recognition():
    global is_recognizing
    # Attiva l'interruttore del riconoscimento.
    if not is_recognizing:
        is_recognizing = True
        print("Riconoscimento ATTIVATO.")

# --- 7. AVVIO DEL SERVER ---
# Questo blocco viene eseguito solo se lo script viene lanciato direttamente.
if __name__ == '__main__':
    # Avvia il server usando SocketIO (che gestisce Flask al suo interno).
    # host='0.0.0.0' lo rende visibile sulla rete locale.
    # port=8888 imposta la porta.
    # debug=True attiva la modalità di debug per vedere gli errori.
    socketio.run(app, host='0.0.0.0', port=8888, debug=True)