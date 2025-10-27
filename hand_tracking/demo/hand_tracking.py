import cv2
import mediapipe as mp
import time

# --- IMPOSTAZIONI INIZIALI ---

# Inizializza MediaPipe per il disegno degli "scheletri" e dei punti
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Inizializza la webcam usando OpenCV
# Il numero '0' si riferisce alla webcam predefinita del tuo computer
cap = cv2.VideoCapture(0)

# Inizializza il contatore per il calcolo degli FPS (Frames Per Second)
pTime = 0 # Previous time

# --- LOGICA PRINCIPALE IN UN BLOCCO 'with' ---
# Usiamo il modello Hand Landmarker di MediaPipe
with mp_hands.Hands(
    min_detection_confidence=0.7,  # Soglia di confidenza per rilevare una mano
    min_tracking_confidence=0.5    # Soglia per continuare a tracciare la mano
) as hands:

    # Ciclo principale: continua finché la webcam è aperta
    while cap.isOpened():
        # Legge un singolo fotogramma (frame) dalla webcam
        success, image = cap.read()
        if not success:
            print("Impossibile accedere alla webcam.")
            continue

        # Per migliorare le performance, l'immagine viene prima elaborata
        # OpenCV legge in formato BGR, MediaPipe si aspetta RGB
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        
        # Passa l'immagine al modello MediaPipe per trovare le mani
        results = hands.process(image)

        # Riconverti l'immagine in BGR per poterla mostrare con OpenCV
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # --- DISEGNO SULL'IMMAGINE ---
        # Se il modello ha trovato almeno una mano...
        if results.multi_hand_landmarks:
            # Itera su ogni mano trovata
            for hand_landmarks in results.multi_hand_landmarks:
                # Disegna lo "scheletro" della mano (le connessioni tra i punti)
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # --- CALCOLO E VISUALIZZAZIONE DEGLI FPS ---
        cTime = time.time() # Current time
        fps = 1 / (cTime - pTime)
        pTime = cTime
        # Scrivi il valore degli FPS sull'immagine
        cv2.putText(image, f'FPS: {int(fps)}', (10, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        # Mostra l'immagine elaborata in una finestra chiamata "Riconoscimento Mano"
        cv2.imshow('Riconoscimento Mano MediaPipe', image)

        # Interrompi il ciclo se viene premuto il tasto 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

# --- PULIZIA FINALE ---
# Rilascia la risorsa della webcam
cap.release()
# Chiude tutte le finestre di OpenCV
cv2.destroyAllWindows()