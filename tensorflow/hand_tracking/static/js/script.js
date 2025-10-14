// Esegui lo script solo quando l'intera pagina è stata caricata
document.addEventListener('DOMContentLoaded', () => {

    // Stabilisce la connessione WebSocket con il server
    const socket = io();

    // Seleziona gli elementi della pagina con cui interagire
    const toggleBtn = document.getElementById('toggle-btn');
    const actionLog = document.getElementById('action-log');

    // Funzione per aggiungere un messaggio al log
    function addLogEntry(message, type = 'info') {
        const newLogEntry = document.createElement('li');
        newLogEntry.className = 'list-group-item bg-dark text-light';

        // Aggiungi un'icona e formatta il testo
        const icon = type === 'success' ? '✅' : 'ℹ️';
        newLogEntry.innerHTML = `${icon} <span class="text-muted">[${new Date().toLocaleTimeString()}]</span> ${message}`;

        actionLog.prepend(newLogEntry);
    }

    // Inizializza con un messaggio di benvenuto
    addLogEntry('Pronto per il riconoscimento.');

    // 1. Gestione del click sul bottone
    toggleBtn.addEventListener('click', () => {
        // Invia l'evento 'toggle_recognition' al server
        socket.emit('toggle_recognition');

        // Aggiorna la grafica del bottone
        toggleBtn.textContent = '... Riconoscimento in corso ...';
        toggleBtn.classList.remove('btn-primary');
        toggleBtn.classList.add('btn-danger', 'recognizing');
        toggleBtn.disabled = true; // Disabilita il bottone temporaneamente
    });

    // 2. Ascolto dei log dal server
    socket.on('action_log', (msg) => {
        console.log('Azione ricevuta:', msg.data);

        // Aggiungi l'azione ricevuta al log
        addLogEntry(msg.data, 'success');

        // Resetta lo stato del bottone
        toggleBtn.textContent = 'Avvia Riconoscimento';
        toggleBtn.classList.remove('btn-danger', 'recognizing');
        toggleBtn.classList.add('btn-primary');
        toggleBtn.disabled = false; // Riabilita il bottone
    });

});