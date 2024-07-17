import {socket} from "./refresh.js";

(function () {

    function drawChart(measures, containerId, xAxisLabel, fullscreen) {
        const diagramContainer = document.getElementById(containerId)
        diagramContainer.dataset.displayedMeasures = JSON.stringify(measures)
        diagramContainer.childNodes.forEach(function (child) {
            diagramContainer.removeChild(child)
        })
        const maxWidth = fullscreen ? diagramContainer.clientWidth : Math.min(parseInt(window.innerWidth * 0.7), diagramContainer.clientWidth)
        const maxHeight = fullscreen ? diagramContainer.clientWidth : parseInt(window.innerHeight * 0.7)
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
        const margin = fullscreen ? {top: 0, right: 0, bottom: 0, left: 0} : {top: 10, right: 30, bottom: 30, left: 60}
        const svg = d3.select(`#${containerId}`)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
        const diagram = svg.append("g")
            .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");
        const x = d3.scaleTime()
            // adds date now and date before two hours to set default range
            .domain(d3.extent([...measures, {'date': date_now}, {'date': date_before_two_hours}], function (d) {
                return d.date;
            }))
            .range([0, width - margin.left - margin.right]);
        if (!fullscreen) {
            diagram.append("g")
                .attr("transform", "translate(0," + (height - margin.top - margin.bottom) + ")")
                .call(d3.axisBottom(x));
        }

        const y = d3.scaleLinear()
            .domain([0, d3.max(measures, function (d) {
                return +d.value;
            })])
            .range([height - margin.top - margin.bottom, 15]);
        if (!fullscreen) {
            diagram.append("g")
                .call(d3.axisLeft(y))
                .call(g => g.append("text")
                    .attr("x", -margin.left)
                    .attr("y", 10)
                    .attr("fill", "currentColor")
                    .attr("class", "text-primary")
                    .attr("text-anchor", "start")
                    .text(xAxisLabel));
        }

        diagram.append("path")
            .datum(measures)
            .attr("fill", "none")
            .attr("stroke", fullscreen ? "red" : "steelblue")
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

    document.querySelectorAll('.power-consumption.diagram').forEach(container => {
        const entityName = container.dataset.entityName
        const xAxisLabel = container.dataset.xAxisLabel
        const fullscreen = !!container.dataset.fullscreen
        if (!container.id) container.id = "power-consumption-diagram-container-" + makeSafeForCSS(entityName)
        const measurements = []
        const fetchAndDrawDiagram = () => fetch(`/api/appliances/${entityName}/power-consumptions`)
            .then(data => data.json())
            .then(data => {
                measurements.splice(0, measurements.length)
                measurements.push(...data.map(d => {
                    return {"date": new Date(d.time), "value": d.consumption}
                }))
                if (measurements.length > 0) {
                    const newest = measurements.pop()
                    measurements.push(newest)
                    measurements.push({date: new Date(), value: newest.value})
                }
                drawChart(measurements, container.id, xAxisLabel, fullscreen)
            })
            .then(() => fetch(`/api/appliances/${entityName}`))
            .then(data => data.json())
            .then(data => {
                const value = data.watt
                if (value !== null) {
                    const lastSeenAt = new Date(data['last_seen_at'])
                    if (measurements.length > 0) {
                        measurements.pop()
                    } else {
                        measurements.push({date: lastSeenAt, value})
                    }
                    measurements.push({date: new Date(), value})
                    drawChart(measurements, container.id, xAxisLabel, fullscreen)
                }
            })
        socket.on(`appliances/${entityName}/powerConsumptionUpdated`, event => {
            const measure = event.measure
            measurements.pop()
            measurements.push({"date": new Date(measure.time), "value": measure.consumption})
            measurements.push({"date": new Date(), "value": measure.consumption})
            drawChart(measurements, container.id, xAxisLabel, fullscreen)
        });
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