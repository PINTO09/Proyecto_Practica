(function () {
    document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
        const input = document.getElementById(button.dataset.passwordTarget);
        const icon = button.querySelector('i');
        if (!input) {
            button.hidden = true;
            return;
        }

        button.addEventListener('click', function () {
            const willShow = input.type === 'password';
            input.type = willShow ? 'text' : 'password';
            button.setAttribute('aria-pressed', String(willShow));
            button.setAttribute(
                'aria-label',
                willShow ? 'Ocultar contraseña' : 'Mostrar contraseña'
            );
            icon?.classList.toggle('fa-eye', !willShow);
            icon?.classList.toggle('fa-eye-slash', willShow);
            input.focus({preventScroll: true});
        });
    });
})();
