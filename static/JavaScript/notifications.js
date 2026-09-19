document.addEventListener('DOMContentLoaded', function() {
    const btnNotification = document.getElementById('notification-btn');
    const dropdownNotification = document.getElementById('notification-dropdown');
    const markReadBtn = document.getElementById('mark-read-btn');

    if (btnNotification && dropdownNotification) {
        btnNotification.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownNotification.style.display = dropdownNotification.style.display === 'flex' ? 'none' : 'flex';
        });

        document.addEventListener('click', function(e) {
            if (!dropdownNotification.contains(e.target) && !btnNotification.contains(e.target)) {
                dropdownNotification.style.display = 'none';
            }
        });
    }

    // Petición AJAX para marcar como leídas
    if (markReadBtn) {
        markReadBtn.addEventListener('click', function() {
            fetch('/marcar-leidas/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Ocultar el badge rojo de la campana
                    const badge = document.querySelector('.notification-badge');
                    if (badge) badge.style.display = 'none';

                    // Quitar la clase 'unread' de las notificaciones en pantalla
                    document.querySelectorAll('.notification-item').forEach(item => {
                        item.classList.remove('unread');
                    });
                }
            });
        });
    }
});

// Función auxiliar para obtener el token de seguridad CSRF de Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}