from flask import Flask, render_template, Response
import cv2
import mediapipe as mp

# Inizializza l'applicazione Flask
app = Flask(__name__)

# Inizializza MediaPipe e la webcam
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
cap = cv2.VideoCapture(0)

def generate_frames():
    """
    Questa funzione cattura i frame dalla webcam, li elabora con MediaPipe
    e li restituisce come un flusso di immagini JPEG.
    """
    with mp_hands.Hands(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5) as hands:
        
        while True:
            # Legge un frame dalla webcam
            success, frame = cap.read()
            if not success:
                break
            else:
                # Inverti l'immagine e converti i colori
                frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
                
                # Elabora l'immagine con MediaPipe
                results = hands.process(frame)

                # Riconverti in BGR per disegnarci sopra con OpenCV
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Disegna lo scheletro della mano se rilevata
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(
                            frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Codifica il frame in formato JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                # Restituisci il frame nel formato per lo streaming
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Pagina principale che renderizza il template HTML."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Endpoint per lo streaming video."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Avvia il server rendendolo accessibile sulla rete locale usando host='0.0.0.0'
    app.run(host='0.0.0.0', debug=True)