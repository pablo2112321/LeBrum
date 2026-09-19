/* ============================================================
   REGISTRO-VALIDACION.JS
   Validación en tiempo real sincronizada 1:1 con las reglas
   de RegistroUsuarioForm (forms.py). Es solo UX: la validación
   real y segura vive en el servidor (Django clean_*), este JS
   nunca la reemplaza.
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-registro');
    if (!form) return;

    const DOMINIOS_PERMITIDOS = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'live.com'];

    /* ---------- Helpers genéricos ---------- */

    function getBox(input) {
        return input.closest('.input-box') || input.closest('.game-glass-box');
    }

    function setState(input, state, message) {
        const box = getBox(input);
        if (!box) return;

        box.classList.remove('valid', 'invalid');
        if (state === 'valid') box.classList.add('valid');
        if (state === 'invalid') box.classList.add('invalid');

        const errorEl = box.querySelector('.field-error-text, .game-error-text');
        if (errorEl) errorEl.textContent = message || '';
    }

    function ensureErrorSpan(input, className) {
        const box = getBox(input);
        if (!box) return null;
        let span = box.querySelector('.' + className);
        if (!span) {
            span = document.createElement('span');
            span.className = className;
            box.appendChild(span);
        }
        return span;
    }

    /* ---------- Referencias a los campos (ids que genera Django) ---------- */

    const username = document.getElementById('id_username');
    const email = document.getElementById('id_email');
    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    const checkRiot = document.getElementById('check_riot');
    const idRiot = document.getElementById('id_riot');
    const checkSteam = document.getElementById('check_steam');
    const idSteam = document.getElementById('id_steam');

    [username, email, password1, password2].forEach(function (input) {
        if (input) ensureErrorSpan(input, 'field-error-text');
    });
    [idRiot, idSteam].forEach(function (input) {
        if (input) ensureErrorSpan(input, 'game-error-text');
    });

    /* ---------- Reglas (mismas que clean_username / clean_email / clean_password1) ---------- */

    // Usuario: 3-16 caracteres, letras/números/guion/guion_bajo
    function validarUsername() {
        if (!username) return true;
        const valor = username.value.trim();
        const regex = /^[a-zA-Z0-9_-]+$/;

        if (valor.length === 0) {
            setState(username, 'invalid', 'El nombre de usuario es obligatorio.');
            return false;
        }
        if (valor.length < 3) {
            setState(username, 'invalid', 'Debe tener al menos 3 caracteres.');
            return false;
        }
        if (valor.length > 16) {
            setState(username, 'invalid', 'No puede exceder los 16 caracteres.');
            return false;
        }
        if (!regex.test(valor)) {
            setState(username, 'invalid', 'Solo letras, números, guiones (-) y guion bajo (_).');
            return false;
        }
        setState(username, 'valid', '');
        return true;
    }

    // Email: formato válido + dominio dentro de la lista permitida
    function validarEmail() {
        if (!email) return true;
        const valor = email.value.trim().toLowerCase();
        const regexFormato = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

        if (valor.length === 0) {
            setState(email, 'invalid', 'El correo electrónico es obligatorio.');
            return false;
        }
        if (!regexFormato.test(valor)) {
            setState(email, 'invalid', 'Ingresa un correo con formato válido.');
            return false;
        }
        const dominio = valor.split('@')[1];
        if (!DOMINIOS_PERMITIDOS.includes(dominio)) {
            setState(email, 'invalid', 'Solo aceptamos Gmail, Outlook, Hotmail, Yahoo o Live.');
            return false;
        }
        setState(email, 'valid', '');
        return true;
    }

    // Contraseña 1: máximo 8 caracteres, solo alfanumérica, mínimo 2 dígitos
    function validarPassword1() {
        if (!password1) return true;
        const valor = password1.value;
        const regexAlfanumerica = /^[a-zA-Z0-9]*$/;
        const numeros = (valor.match(/[0-9]/g) || []).length;

        if (valor.length === 0) {
            setState(password1, 'invalid', 'La contraseña es obligatoria.');
            return false;
        }
        if (valor.length > 8) {
            setState(password1, 'invalid', 'Máximo 8 caracteres permitidos.');
            return false;
        }
        if (!regexAlfanumerica.test(valor)) {
            setState(password1, 'invalid', 'No se permiten símbolos (+, -, @, etc.). Solo letras y números.');
            return false;
        }
        if (numeros < 2) {
            setState(password1, 'invalid', 'Debe incluir al menos 2 números.');
            return false;
        }
        setState(password1, 'valid', '');
        if (password2 && password2.value.length > 0) validarPassword2();
        return true;
    }

    // Contraseña 2: debe coincidir exactamente con la contraseña 1
    function validarPassword2() {
        if (!password2 || !password1) return true;
        const valor = password2.value;

        if (valor.length === 0) {
            setState(password2, 'invalid', 'Confirma tu contraseña.');
            return false;
        }
        if (valor !== password1.value) {
            setState(password2, 'invalid', 'Las contraseñas no coinciden.');
            return false;
        }
        setState(password2, 'valid', '');
        return true;
    }

    // Riot ID: formato Nombre#TAG (solo si el checkbox está marcado)
    function validarRiot() {
        if (!checkRiot || !idRiot) return true;
        const box = getBox(idRiot);

        if (!checkRiot.checked) {
            if (box) box.classList.remove('valid', 'invalid');
            return true;
        }
        const valor = idRiot.value.trim();
        const regex = /^.{3,16}#[A-Za-z0-9]{2,5}$/;

        if (valor.length === 0) {
            setState(idRiot, 'invalid', 'Ingresa tu Riot ID o desmarca la casilla.');
            return false;
        }
        if (!regex.test(valor)) {
            setState(idRiot, 'invalid', 'Formato esperado: Nombre#TAG (ej: Leyenda#LAS).');
            return false;
        }
        setState(idRiot, 'valid', '');
        return true;
    }

    // Steam ID64: exactamente 17 dígitos (solo si el checkbox está marcado)
    function validarSteam() {
        if (!checkSteam || !idSteam) return true;
        const box = getBox(idSteam);

        if (!checkSteam.checked) {
            if (box) box.classList.remove('valid', 'invalid');
            return true;
        }
        const valor = idSteam.value.trim();
        const regex = /^\d{17}$/;

        if (valor.length === 0) {
            setState(idSteam, 'invalid', 'Ingresa tu Steam ID64 o desmarca la casilla.');
            return false;
        }
        if (!regex.test(valor)) {
            setState(idSteam, 'invalid', 'Debe ser un código numérico de 17 dígitos.');
            return false;
        }
        setState(idSteam, 'valid', '');
        return true;
    }

    /* ---------- Listeners en tiempo real ---------- */

    if (username) username.addEventListener('input', validarUsername);
    if (email) email.addEventListener('input', validarEmail);
    if (password1) password1.addEventListener('input', validarPassword1);
    if (password2) password2.addEventListener('input', validarPassword2);
    if (idRiot) idRiot.addEventListener('input', validarRiot);
    if (idSteam) idSteam.addEventListener('input', validarSteam);
    if (checkRiot) checkRiot.addEventListener('change', validarRiot);
    if (checkSteam) checkSteam.addEventListener('change', validarSteam);

    /* ---------- Validación final al enviar ---------- */

    form.addEventListener('submit', function (evento) {
        const okUsername = validarUsername();
        const okEmail = validarEmail();
        const okPassword1 = validarPassword1();
        const okPassword2 = validarPassword2();
        const okRiot = validarRiot();
        const okSteam = validarSteam();

        const todoValido = okUsername && okEmail && okPassword1 && okPassword2 && okRiot && okSteam;

        if (!todoValido) {
            evento.preventDefault();
            const primerError = form.querySelector('.input-box.invalid input, .game-glass-box.invalid input');
            if (primerError) {
                primerError.focus();
                primerError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
});