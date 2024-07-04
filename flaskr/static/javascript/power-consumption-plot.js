(function () {

    function drawChart(measures, containerId, xAxisLabel, fullscreen) {
        let diagramContainer = document.getElementById(containerId);
        diagramContainer.childNodes.forEach(function (child) {
            diagramContainer.removeChild(child)
        })
        diagramContainer.append(Plot.plot({
            y: {
                domain: [0, Math.min(2400, Math.max(...measures.map(m => m.consumption + 10)))],
                label: xAxisLabel
            },
            style: "overflow: visible;",
            marks: [
                Plot.lineY(measures, {x: "time", y: "consumption", curve: "catmull-rom"}),
                Plot.dotY(measures, {x: "time", y: "consumption", stroke: "currentColor", symbol: 'times'}),
                Plot.crosshairX(measures, {x: "time", y: "consumption"})
            ]
        }))
    }

    document.querySelectorAll('.power-consumption.diagram').forEach(container => {
        const thingName = container.dataset.thingName
        const xAxisLabel = container.dataset.xAxisLabel
        const fullscreen = !!container.dataset.fullscreen
        if (!container.id) container.id = "power-consumption-diagram-container-" + makeSafeForCSS(thingName)
        const measurements = []
        const fetchAndDrawDiagram = () => fetch(`/api/appliances/${thingName}/power-consumptions`)
            .then(data => data.json())
            .then(data => {
                measurements.splice(0, measurements.length) // delete all data on updates
                data.forEach(d => {d.time = new Date(d.time)}) // convert isoformat to date
                measurements.push(...data)
                drawChart(measurements, container.id, xAxisLabel, fullscreen)
            }).then(() => window.setTimeout(fetchAndDrawDiagram, 30 * 1000))
        fetchAndDrawDiagram().then(() => window.addEventListener('resize', () => drawChart(measurements, container.id, xAxisLabel, fullscreen)))
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