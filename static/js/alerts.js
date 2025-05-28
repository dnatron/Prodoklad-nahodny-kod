// Konfigurace notifikací
const notificationConfig = {
    duration: 5000,
    position: 'top-right',
    showClose: true,
    maxVisible: 5
};

// Sledování již zobrazených zpráv pro prevenci duplicit
const shownMessages = new Set();

// Vytvoření nové notifikace
function showNotification(type, message, options = {}) {
    // Kontrola, zda již tato zpráva nebyla zobrazena
    const messageKey = `${type}:${message}`;
    if (shownMessages.has(messageKey)) {
        return null; // Zpráva již byla zobrazena, přeskočíme
    }
    
    // Přidáme zprávu do seznamu zobrazených
    shownMessages.add(messageKey);
    
    // Po určitém čase zprávu ze seznamu odstraníme (aby se mohla znovu zobrazit)
    setTimeout(() => {
        shownMessages.delete(messageKey);
    }, options.duration || notificationConfig.duration + 1000);
    
    const container = document.getElementById('notification-container');
    const toastId = 'toast-' + Date.now();
    
    // Vizuální styly podle typu zprávy
    const iconMap = {
        'success': 'bi-check-circle-fill',
        'danger': 'bi-exclamation-circle-fill', 
        'warning': 'bi-exclamation-triangle-fill',
        'info': 'bi-info-circle-fill'
    };
    
    // Vytvoření Toast elementu
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <i class="bi ${iconMap[type]} me-2"></i>
                <strong class="me-auto">${options.title || 'Oznámení'}</strong>
                <small>${options.subtitle || ''}</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Přidání do DOM
    container.insertAdjacentHTML('beforeend', toastHtml);
    
    // Inicializace a zobrazení
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: options.duration || notificationConfig.duration
    });
    toast.show();
    
    // Automatické odstranění z DOM po skrytí
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
    
    return toastElement;
}

// Zpracování HTMX triggeru
document.addEventListener('htmx:afterRequest', function(evt) {
    const triggerHeader = evt.detail.xhr.getResponseHeader('HX-Trigger');
    
    if (triggerHeader) {
        try {
            const triggers = JSON.parse(triggerHeader);
            if (triggers.showMessage) {
                const { type, message, title } = triggers.showMessage;
                showNotification(type, message, { title });
            }
        } catch (e) {
            console.error('Error parsing HX-Trigger:', e);
            console.error('Header content:', triggerHeader);
        }
    }
});

// Zpracování session zprávy při načtení stránky
document.addEventListener('DOMContentLoaded', function() {
    // Přidáme kontrolu, zda již byly zprávy zpracovány
    if (sessionStorage.getItem('messagesProcessed')) {
        // Pokud ano, vyčistíme flag a přeskočíme zpracování
        sessionStorage.removeItem('messagesProcessed');
        return;
    }
    
    const messageContainer = document.getElementById('message-container');
    if (messageContainer && messageContainer.querySelector('.alert')) {
        const alerts = messageContainer.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const type = alert.classList.contains('alert-success') ? 'success' :
                      alert.classList.contains('alert-danger') ? 'danger' :
                      alert.classList.contains('alert-warning') ? 'warning' : 'info';
            
            // Extrahování textu zprávy (odstranění tlačítka)
            const message = alert.innerHTML.replace(/<button.*?<\/button>/g, '').trim();
            
            // Zobrazení notifikace pomocí toast
            showNotification(type, message);
            
            // Skrýt původní alert
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
        
        // Nastavíme flag, že zprávy byly zpracovány
        sessionStorage.setItem('messagesProcessed', 'true');
    }
});

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});
