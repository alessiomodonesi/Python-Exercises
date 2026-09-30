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

    // --- 1. GESTIONE DEL CLICK SUL BOTTONE ---
    toggleBtn.addEventListener('click', () => {
        // Controlla se il bottone è già disabilitato per evitare doppi click
        if (toggleBtn.disabled) {
            return;
        }

        // Invia l'evento 'toggle_recognition' al server
        socket.emit('toggle_recognition');

        // Aggiorna la grafica del bottone
        toggleBtn.textContent = '... Riconoscimento in corso ...';
        toggleBtn.classList.remove('btn-primary');
        toggleBtn.classList.add('btn-danger', 'recognizing');
        toggleBtn.disabled = true; // Disabilita il bottone
    });

    // --- 2. ASCOLTO DEI LOG DAL SERVER ---
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

    // --- 3. NUOVA SEZIONE: GESTIONE DELLA TASTIERA ---
    // Aggiunge un "ascoltatore" di eventi all'intera pagina web.
    // L'evento 'keydown' si attiva ogni volta che un tasto viene premuto.
    document.addEventListener('keydown', (event) => {
        // Controlla se il tasto premuto è la barra spaziatrice (' ' o 'Space').
        // 'event.key' contiene il nome del tasto.
        if (event.key === ' ' || event.key === 'Spacebar') {
            // event.preventDefault() impedisce il comportamento predefinito
            // della barra spaziatrice (es. scorrere la pagina), che non vogliamo.
            event.preventDefault();

            // Simula un click sul bottone di riconoscimento.
            // Questo riutilizza tutta la logica che abbiamo già scritto
            // per il click del mouse, senza dover duplicare il codice.
            toggleBtn.click();
        }
    });

});