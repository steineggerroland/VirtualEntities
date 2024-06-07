(function () {

    function drawChart(powerConsumptionMeasures, containerId) {
        const margin = {top: 10, right: 30, bottom: 30, left: 60}
        const maxWidth = parseInt(window.innerWidth * 0.7)
        const maxHeight = parseInt(window.innerHeight * 0.7)
        const useHeight = maxHeight / maxWidth < 1
        let width, height = 0
        if (useHeight) {
            height = maxHeight
            width = maxHeight
        } else {
            height = maxWidth
            width = maxWidth
        }
        document.getElementById(containerId).childNodes.forEach(function (child) {
            child.parentElement.removeChild(child)
        })
        let svg = d3.select(`#${containerId}`)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");

        function addData(data) {
            var x = d3.scaleTime()
                .domain(d3.extent(data, function (d) {
                    return d.date;
                }))
                .range([0, width]);
            svg.append("g")
                .attr("transform", "translate(0," + height + ")")
                .call(d3.axisBottom(x));

            var y = d3.scaleLinear()
                .domain([0, d3.max(data, function (d) {
                    return +d.value;
                })])
                .range([height, 15]);
            svg.append("g")
                .call(d3.axisLeft(y))
                .call(g => g.append("text")
                    .attr("x", -margin.left)
                    .attr("y", 10)
                    .attr("fill", "currentColor")
                    .attr("class", "text-primary")
                    .attr("text-anchor", "start")
                    .text("Watt"));

            svg.append("path")
                .datum(data)
                .attr("fill", "none")
                .attr("stroke", "steelblue")
                .attr("class", "stroke-primary")
                .attr("stroke-width", 1.5)
                .attr("d", d3.line()
                    .x(function (d) {
                        return x(d.date)
                    })
                    .y(function (d) {
                        return y(d.value)
                    })
                )
        }

        addData(powerConsumptionMeasures)
    }

    document.querySelectorAll('.power-consumption.diagram').forEach(container => {
        const thingName = container.dataset.thingName
        if (!container.id) container.id = "power-consumption-diagram-container-" + thingName
        const measurements = []
        const fetchAndDrawDiagram = () => fetch(`/api/appliances/${thingName}/power-consumptions`)
            .then(data => data.json())
            .then(data => {
                measurements.splice(0, measurements.length)
                measurements.push(data.map(d => {
                    return {"date": new Date(d.time), "value": d.consumption}
                }))
                drawChart(measurements, container.id)
            }).then(() => window.setTimeout(fetchAndDrawDiagram, 30 * 1000))
        fetchAndDrawDiagram().then(() => window.addEventListener('resize', () => drawChart(measurements, container.id)))
    })
})()