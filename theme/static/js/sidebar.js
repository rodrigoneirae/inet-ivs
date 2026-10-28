(() => {
    const sidebar = document.getElementById('menu-lateral');
    const toggle = document.querySelector('[data-sidebar-toggle]');
    if (!sidebar || !toggle) return;

    let expanded = !window.matchMedia('(max-width: 767px)').matches;
    try {
        const saved = localStorage.getItem('inet-ivs-sidebar');
        if (saved !== null) expanded = saved === 'open';
    } catch (error) {
        // Use the screen-size default if storage is unavailable.
    }

    function update() {
        sidebar.hidden = !expanded;
        toggle.setAttribute('aria-expanded', String(expanded));
        toggle.setAttribute('aria-label', expanded ? 'Ocultar menú lateral' : 'Mostrar menú lateral');
        toggle.title = expanded ? 'Ocultar menú lateral' : 'Mostrar menú lateral';
        window.dispatchEvent(new Event('resize'));
    }

    toggle.hidden = false;
    update();
    toggle.addEventListener('click', () => {
        expanded = !expanded;
        try {
            localStorage.setItem('inet-ivs-sidebar', expanded ? 'open' : 'closed');
        } catch (error) {
            // The control still works for the current page.
        }
        update();
    });
})();
