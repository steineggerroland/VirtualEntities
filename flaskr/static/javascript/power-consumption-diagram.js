(function() {
    var margin = {top: 10, right: 30, bottom: 30, left: 60}

    let svg
    function drawChart(powerConsumptionMeasures) {
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
        container = document.getElementById("power-consumption")
        container.childNodes.forEach(function(child) {
            container.removeChild(child)
        })
        var margin = {top: 10, right: 30, bottom: 30, left: 60}
        svg = d3.select("#power-consumption")
          .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform",
                  "translate(" + margin.left + "," + margin.top + ")");

          function addData(data) {
            var x = d3.scaleTime()
              .domain(d3.extent(data, function(d) { return d.date; }))
              .range([ 0, width ]);
            svg.append("g")
              .attr("transform", "translate(0," + height + ")")
              .call(d3.axisBottom(x));

            var y = d3.scaleLinear()
              .domain([0, d3.max(data, function(d) { return +d.value; })])
              .range([ height, 15 ]);
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
                .x(function(d) { return x(d.date) })
                .y(function(d) { return y(d.value) })
                )
        }
        addData(powerConsumptionMeasures)
    }

    thing_name = document.getElementById('power-consumption').getAttribute('itemid')
    const fetchAndDrawDiagram = () => {
        return fetch(`/api/appliances/${thing_name}/power-consumptions`)
            .then(data => data.json())
            .then(data => {
                drawChart(data.map(d => {return {"date": new Date(d.time), "value": d.consumption}}))
            }).then(() => window.setTimeout(() => fetchAndDrawDiagram(), 30 * 1000))
    }
    fetchAndDrawDiagram().then(() => window.addEventListener('resize', drawChart ))
})()