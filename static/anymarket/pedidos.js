(() => {
    const table = document.querySelector('#pedidos-tabla');
    const target = document.querySelector('#pedidos-tabulator');
    const fallback = document.querySelector('#pedidos-respaldo');
    if (!table || !target || !fallback || typeof Tabulator === 'undefined') return;

    const fields = ['canal', 'pedido', 'cliente', 'fecha', 'items', 'total', 'estado'];
    const rows = Array.from(table.tBodies[0].rows, (row) =>
        Object.fromEntries(fields.map((field, index) => [field, row.cells[index].textContent.trim()]))
    );
    const text = (cell) => {
        const span = document.createElement('span');
        span.textContent = cell.getValue();
        return span;
    };
    const ordenar = (_event, column) => {
        const field = column.getField();
        const direction = target.dataset.orden === field && target.dataset.direccion === 'asc' ? 'desc' : 'asc';
        const url = new URL(window.location.href);
        url.searchParams.set('orden', field);
        url.searchParams.set('direccion', direction);
        url.searchParams.delete('page');
        window.location.assign(url);
    };
    const titulo = (label, field) => target.dataset.orden === field
        ? `${label} ${target.dataset.direccion === 'asc' ? '▲' : '▼'}` : `${label} ▴`;
    const filtro = (field, source, label) => () => {
        const select = document.createElement('select');
        select.setAttribute('aria-label', `Filtrar por ${label}`);
        select.className = 'filtro-encabezado';
        const choices = JSON.parse(document.getElementById(source).textContent);
        const selected = target.dataset[field] || '';
        const values = Array.from(new Set([...choices.filter(value => typeof value === 'string' && value), selected]));
        select.add(new Option('Todos', ''));
        const canales = {'mercado_livre': 'MERCADO LIBRE', 'shopify': 'PORTOMENAJE', 'c52434-09': 'YAKU'};
        values.filter(Boolean).forEach(value => select.add(new Option(
            field === 'canal' ? (canales[value.toLowerCase()] || value) : value, value
        )));
        select.value = selected;
        ['click', 'keydown', 'pointerdown'].forEach(event => select.addEventListener(event, e => e.stopPropagation()));
        select.addEventListener('change', () => {
            const url = new URL(window.location.href);
            if (select.value) url.searchParams.set(field, select.value);
            else url.searchParams.delete(field);
            url.searchParams.delete('page');
            window.location.assign(url);
        });
        return select;
    };
    target.hidden = false;
    try {
        const tabulator = new Tabulator(target, {
            data: rows,
            layout: 'fitColumns',
            movableColumns: true,
            rowHeight: 50,
            placeholder: 'No hay pedidos para mostrar.',
            columnDefaults: {headerSort: false, formatter: text, headerClick: ordenar},
            columns: [
                {title: titulo('Canal', 'canal'), field: 'canal', minWidth: 150,
                    headerFilter: filtro('canal', 'filtro-canales', 'canal'), headerFilterFunc: () => true},
                {title: titulo('OC', 'pedido'), field: 'pedido', minWidth: 130},
                {title: titulo('Cliente', 'cliente'), field: 'cliente', minWidth: 200, widthGrow: 2},
                {title: titulo('Fecha', 'fecha'), field: 'fecha', minWidth: 165},
                {title: titulo('Ítems', 'items'), field: 'items', minWidth: 80, hozAlign: 'center'},
                {title: titulo('Venta', 'total'), field: 'total', minWidth: 100, hozAlign: 'right'},
                {title: titulo('Status', 'estado'), field: 'estado', minWidth: 170,
                    headerFilter: filtro('estado', 'filtro-estados', 'status'), headerFilterFunc: () => true},
            ],
        });
        tabulator.on('tableBuilt', () => {
            tabulator.getColumns().forEach(column => {
                const element = column.getElement();
                element.tabIndex = 0;
                element.setAttribute('aria-label', `Ordenar por ${column.getDefinition().title}`);
                element.addEventListener('keydown', event => {
                    if (event.target === element && (event.key === 'Enter' || event.key === ' ')) {
                        event.preventDefault();
                        ordenar(event, column);
                    }
                });
            });
        });
        fallback.hidden = true;
    } catch (error) {
        target.hidden = true;
    }
})();
