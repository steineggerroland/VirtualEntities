(function () {

    function drawChart(measures, containerId, strategy, xAxisLabel, fullscreen) {
        let diagramContainer = document.getElementById(containerId);
        diagramContainer.childNodes.forEach(function (child) {
            diagramContainer.removeChild(child)
        })
        const marks = []
        if (strategy && strategy.name === 'simple_history_run_complete_strategy') {
            marks.push(Plot.areaY(measures, {
                x: 'time',
                y: strategy.power_consumption_threshold,
                fill: '#CCCCCC',
                fillOpacity: 0.25
            }))
        }
        let plot = Plot.plot({
            y: {
                domain: [0, Math.min(2400, Math.max(...measures.map(m => m.consumption + 10)))],
                label: xAxisLabel
            },
            style: "overflow: visible;",
            marks: [
                ...marks,
                Plot.lineY(measures, {x: "time", y: "consumption", curve: "catmull-rom", marker: 'dot'}),
                Plot.crosshairX(measures, {x: "time", y: "consumption"})
            ]
        });
        diagramContainer.append(plot)
    }

    document.querySelectorAll('.power-consumption.diagram').forEach(container => {
        const thingName = container.dataset.thingName
        const xAxisLabel = container.dataset.xAxisLabel
        const fullscreen = !!container.dataset.fullscreen
        if (!container.id) container.id = "power-consumption-diagram-container-" + makeSafeForCSS(thingName)
        const measures = []
        let strategy
        const fetchAndDrawDiagram = () => fetch(`/api/appliances/${thingName}/power-consumptions`)
            .then(data => data.json())
            .then(data => {
                measures.pop()
                data.forEach(d => {
                    d.time = new Date(d.time)
                }) // convert isoformat to date
                data = data.filter(d => !(measures.map(m => m.time.toISOString()).includes(d.time.toISOString())))
                measures.push(...data)
                return measures
            })
            .then(measurements => drawChart(measurements, container.id, strategy, xAxisLabel, fullscreen))
            .then(() => window.setTimeout(fetchAndDrawDiagram, 30 * 1000))
        fetch(`/api/appliances/${thingName}/run-complete-strategy`)
            .then(data => data.json())
            .then(data => {
                strategy = data
            })
            .then(() => fetchAndDrawDiagram())
            .then(() => window.addEventListener('resize', () => drawChart(measures, container.id, marks, xAxisLabel, fullscreen)))
    })

    // Thanks to PleaseStand at StackOverflow: https://stackoverflow.com/a/7627603
    function makeSafeForCSS(name) {
        return name.replace(/[^a-z0-9]/g, function (s) {
            let c = s.charCodeAt(0);
            if (c == 32) return '-';
            if (c >= 65 && c <= 90) return '_' + s.toLowerCase();
            return '__' + ('000' + c.toString(16)).slice(-4);
        });
    }
})()