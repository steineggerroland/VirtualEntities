(function () {

    function drawChart(measures, containerId, xAxisLabel) {
        let diagramContainer = document.getElementById(containerId);
        diagramContainer.childNodes.forEach(function (child) {
            diagramContainer.removeChild(child)
        })
        const maxWidth = Math.min(parseInt(window.innerWidth * 0.7), diagramContainer.clientWidth)
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
        const date_now = new Date();
        const date_before_two_hours = new Date(date_now - 2 * 60 * 60 * 1000);
        const margin = {top: 10, right: 30, bottom: 30, left: 60}
        const svg = d3.select(`#${containerId}`)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
        diagram = svg.append("g")
            .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");
        // adds date now and date before two hours to set default range
        const x = d3.scaleTime()
            .domain(d3.extent([...measures, {'date': date_now}, {'date': date_before_two_hours}], function (d) {
                return d.date;
            }))
            .range([0, width - margin.left - margin.right]);
        diagram.append("g")
            .attr("transform", "translate(0," + (height - margin.top - margin.bottom) + ")")
            .call(d3.axisBottom(x));

        const y = d3.scaleLinear()
            .domain([-5 + d3.min(measures, function (d) {
                return +d.value;
            }), 5 + d3.max(measures, function (d) {
                return +d.value;
            })])
            .range([height - margin.top - margin.bottom, 15]);
        diagram.append("g")
            .call(d3.axisLeft(y))
            .call(g => g.append("text")
                .attr("x", -margin.left)
                .attr("y", 10)
                .attr("fill", "currentColor")
                .attr("class", "text-primary")
                .attr("text-anchor", "start")
                .text(xAxisLabel));

        diagram.append("path")
            .datum(measures)
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

    document.querySelectorAll('.room-climate.diagram').forEach(container => {
        const thingName = container.dataset.thingName
        const attribute = container.dataset.attribute
        const xAxisLabel = container.dataset.xAxisLabel
        if (!container.id) container.id = attribute + "-diagram-container-" + makeSafeForCSS(thingName)
        const measurements = []
        const fetchAndDrawDiagram = () => fetch(`/api/rooms/${thingName}/${attribute}`)
            .then(data => data.json())
            .then(data => {
                measurements.splice(0, measurements.length)
                measurements.push(...data.map(d => {
                    return {"date": new Date(d.time), "value": d[attribute]}
                }))
                drawChart(measurements, container.id, xAxisLabel)
            }).then(() => window.setTimeout(fetchAndDrawDiagram, 30 * 1000))
        fetchAndDrawDiagram().then(() => window.addEventListener('resize', () => drawChart(measurements, container.id, xAxisLabel)))
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