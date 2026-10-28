(() => {
    const root = document.documentElement;
    let savedTheme = null;
    try {
        savedTheme = localStorage.getItem('inet-ivs-theme');
    } catch (error) {
        // The system preference remains available when storage is blocked.
    }
    const isDark = savedTheme === 'dark' ||
        (savedTheme !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    root.classList.toggle('dark', isDark);

    function updateButtons() {
        const dark = root.classList.contains('dark');
        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            button.setAttribute('aria-pressed', String(dark));
            button.setAttribute('aria-label', dark ? 'Activar tema claro' : 'Activar tema oscuro');
            button.title = dark ? 'Activar tema claro' : 'Activar tema oscuro';
            button.textContent = dark ? '☀' : '☾';
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        updateButtons();
        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            button.addEventListener('click', () => {
                const dark = root.classList.toggle('dark');
                try {
                    localStorage.setItem('inet-ivs-theme', dark ? 'dark' : 'light');
                } catch (error) {
                    // Keep the selected theme for the current page.
                }
                updateButtons();
            });
        });
    });
})();
