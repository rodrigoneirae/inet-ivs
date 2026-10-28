(() => {
    if (typeof Litepicker === 'undefined') return;

    document.querySelectorAll('input[data-litepicker]').forEach((input) => {
        const value = input.value;
        try {
            input.type = 'text';
            input.value = value;
            input.placeholder = 'AAAA-MM-DD';
            input.autocomplete = 'off';
            new Litepicker({
                element: input,
                singleMode: true,
                format: 'YYYY-MM-DD',
                lang: 'es-CL',
                autoApply: true,
                allowRepick: true,
            });
        } catch (error) {
            input.type = 'date';
            input.value = value;
        }
    });
})();
