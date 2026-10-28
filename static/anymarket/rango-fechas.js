(() => {
    const container = document.getElementById('rango-fechas-contenedor');
    const range = document.getElementById('rango-fechas');
    const fallback = document.getElementById('fechas-alternativas');
    const start = document.getElementById('desde');
    const end = document.getElementById('hasta');
    if (!container || !range || !fallback || !start || !end || typeof Litepicker === 'undefined') return;

    // Preserve open-ended ranges from existing links using the native controls.
    if (Boolean(start.value) !== Boolean(end.value)) return;

    try {
        let ready = false;
        const picker = new Litepicker({
            element: range,
            singleMode: false,
            format: 'DD-MM-YYYY',
            delimiter: ' - ',
            lang: 'es-CL',
            autoApply: true,
            setup: (instance) => {
                instance.on('selected', (from, to) => {
                    start.value = from.format('YYYY-MM-DD');
                    end.value = to.format('YYYY-MM-DD');
                    range.setCustomValidity('');
                    if (ready) range.form.requestSubmit();
                });
            },
        });
        const displayDate = (value) => value.split('-').reverse().join('-');
        if (start.value && end.value) picker.setDateRange(displayDate(start.value), displayDate(end.value));
        ready = true;
        range.addEventListener('input', () => {
            const value = range.value.trim();
            if (!value) {
                start.value = '';
                end.value = '';
                range.setCustomValidity('');
                return;
            }
            const match = value.match(/^(\d{2}-\d{2}-\d{4})\s+-\s+(\d{2}-\d{2}-\d{4})$/);
            if (!match) {
                range.setCustomValidity('Escribe dos fechas con el formato DD-MM-AAAA - DD-MM-AAAA.');
                return;
            }
            start.value = displayDate(match[1]);
            end.value = displayDate(match[2]);
            range.setCustomValidity(start.value && end.value && start.value <= end.value
                ? '' : 'Introduce un rango de fechas válido.');
        });
        range.addEventListener('change', () => {
            if (range.checkValidity()) range.form.requestSubmit();
        });
        fallback.hidden = true;
        container.hidden = false;
    } catch (error) {
        // Native date inputs remain available if Litepicker cannot initialize.
    }
})();
