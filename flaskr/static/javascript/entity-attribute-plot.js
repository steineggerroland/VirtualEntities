(function () {

    function drawChart(measures, containerId, attribute, thresholds, strategy, xAxisLabel, fullscreen, locale) {
        if (attribute === 'power-consumption') {
            measures.forEach(m => m[attribute] = m['consumption'])
        }
        const diagramContainer = document.getElementById(containerId)
        diagramContainer.dataset.displayedMeasures = JSON.stringify(measures)
        diagramContainer.childNodes.forEach(function (child) {
            diagramContainer.removeChild(child)
        })
        let yDomain, yTickFormat
        if (attribute === 'temperature') {
            yDomain = [Math.min(...measures.map(m => m[attribute])) - 5, Math.max(...measures.map(m => m[attribute])) + 5]
            yTickFormat = v => v + "°C"
        } else if (attribute === 'humidity') {
            yDomain = [Math.min(...measures.map(m => m[attribute])) - 10, Math.max(...measures.map(m => m[attribute])) + 10]
            yTickFormat = v => v + "%"
        } else {
            yDomain = [0, Math.min(2400, Math.max(...measures.map(m => m[attribute])) + 10)]
            yTickFormat = v => v + "W"
        }
        const marks = []
        if (strategy && strategy.name === 'simple_history_run_complete_strategy') {
            marks.push(Plot.areaY(measures, {
                x: 'time',
                y: strategy.power_consumption_threshold,
                fill: '#ececec',
            }))
        }
        if (thresholds) {
            const lowerBound = yDomain[0]
            const yUpperBound = yDomain[1]
            const isTemperature = attribute === 'temperature'
            const yHardUpperThreshold = isTemperature ? Math.max(Math.max(...measures.map(m => m[attribute])), thresholds.heat_threshold) + 5 : 100;
            const yWeakUpperThreshold = isTemperature ? thresholds.heat_threshold : thresholds.wetness_threshold;
            const yOptimum = thresholds.optimal_upper;
            if (yUpperBound > yWeakUpperThreshold) {
                marks.push(Plot.areaY(measures, {
                    x: 'time',
                    y1: Math.min(yHardUpperThreshold, yUpperBound),
                    y2: Math.max(yOptimum, lowerBound),
                    fill: isTemperature ? '#F06122' : '#4CB0FF',
                    fillOpacity: 0.25
                }))
            }
            const yWeakLowerThreshold = thresholds.optimal_lower;
            if (yUpperBound > yOptimum && lowerBound < yWeakUpperThreshold) {
                marks.push(Plot.areaY(measures, {
                    x: 'time',
                    y1: Math.min(yWeakUpperThreshold, yUpperBound),
                    y2: Math.max(yWeakLowerThreshold, lowerBound),
                    fill: isTemperature ? '#FDC848' : '#2BEEFF',
                    fillOpacity: 0.25
                }))
            }
            const yHardLowerThreshold = isTemperature ? thresholds.frostiness_threshold : thresholds.drought_threshold;
            if (yUpperBound > yWeakLowerThreshold && lowerBound < yOptimum) {
                marks.push(Plot.areaY(measures, {
                    x: 'time',
                    y1: Math.min(yOptimum, yUpperBound),
                    y2: Math.max(yHardLowerThreshold, lowerBound),
                    fill: '#83FF6B',
                    fillOpacity: 0.25
                }))
            }
            if (yUpperBound > yHardLowerThreshold && lowerBound < yWeakLowerThreshold) {
                marks.push(Plot.areaY(measures, {
                    x: 'time',
                    y1: Math.min(yWeakLowerThreshold, yUpperBound),
                    y2: Math.max(yHardLowerThreshold, lowerBound),
                    fill: isTemperature ? '#2BEEFF' : '#FDC848',
                    fillOpacity: 0.25
                }))
            }
            if (lowerBound < yHardLowerThreshold) {
                marks.push(Plot.areaY(measures, {
                    x: 'time',
                    y1: Math.min(yHardLowerThreshold, yUpperBound),
                    y2: lowerBound,
                    fill: isTemperature ? '#4CB0FF' : '#F06122',
                    fillOpacity: 0.25
                }))
            }
        }
        const dateTickFormat = (date) => {
            if (!date || !date.getMinutes) return date
            if (date.getMinutes() === 0) {
                return new Intl.DateTimeFormat(locale, {hour: "numeric"}).format(date)
            } else {
                return new Intl.DateTimeFormat(locale, {hour: "numeric", minute: "numeric"}).format(date)
            }
        };
        let plot = Plot.plot({
            y: {
                domain: yDomain,
                label: xAxisLabel
            },
            style: "overflow: visible;",
            marks: [
                ...marks,
                Plot.lineY(measures, {
                    x: "time",
                    y: attribute,
                    curve: "monotone-x",
                    marker: 'dot',
                    className: `data-${attribute}`
                }),
                Plot.crosshairX(measures, {x: "time", y: attribute}),
                Plot.axisX({
                    tickFormat: dateTickFormat
                }),
                Plot.axisY({
                    tickFormat: yTickFormat
                })
            ]
        });
        diagramContainer.append(plot)
    }

    document.querySelectorAll('.diagram').forEach(container => {
        if (!container.dataset.entityName) return
        const entityName = container.dataset.entityName
        const entityType = container.dataset.entityType
        const attribute = container.dataset.attribute
        const xAxisLabel = container.dataset.xAxisLabel
        const fullscreen = !!container.dataset.fullscreen
        const locale = container.dataset.locale || 'en-GB'
        if (!container.id) container.id = `${makeSafeForCSS(entityType)}-${makeSafeForCSS(entityName)}-${makeSafeForCSS(attribute)}-diagram-container`
        const measures = []
        let thresholds
        let strategy
        const fetchAndDrawDiagram = () => fetch(`/api/${entityType}s/${entityName}/${attribute}s`)
            .then(data => data.json())
            .then(data => {
                measures.pop()
                data.forEach(d => {
                    d.time = new Date(d.time)
                }) // convert isoformat to date
                data = data.filter(d => !(measures.map(m => m.time.toISOString()).includes(d.time.toISOString())))
                measures.push(...data)
                if (measures.length > 0) {
                    const newest = measures.pop()
                    measures.push(newest)
                    const m = {...newest}
                    m.time = new Date()
                    measures.push(m)
                }
                return measures
            })
            .then(measurements => drawChart(measurements, container.id, attribute, thresholds, strategy, xAxisLabel, fullscreen, locale))
            .then(() => fetch(`/api/${entityType}s/${entityName}`))
            .then(data => data.json())
            .then(data => {
                const value = data[attribute] ? typeof (data[attribute]) === 'object' ? data[attribute].value : data[attribute] : null
                if (!!value) {
                    if (measures.length > 0) {
                        measures.pop()
                    } else {
                        const lastSeenAt = new Date(data['last_seen_at'])
                        if (lastSeenAt) {
                            const m = {time: lastSeenAt}
                            m[attribute] = value
                            measures.push(m)
                        }
                    }
                    const m = {time: new Date()}
                    m[attribute] = value
                    measures.push(m)
                    drawChart(measures, container.id, attribute, thresholds, strategy, xAxisLabel, fullscreen, locale)
                }
            })
            .then(() => window.setTimeout(fetchAndDrawDiagram, 30 * 1000))
        let promisesBeforeDrawing = []
        if (!!container.dataset.useRunCompleteStrategy) {
            promisesBeforeDrawing.push(fetch(`/api/${entityType}s/${entityName}/run-complete-strategy`)
                .then(data => data.json())
                .then(data => {
                    strategy = data
                }))
        }
        if (!!container.dataset.useThresholds) {
            promisesBeforeDrawing.push(fetch(`/api/${entityType}s/${entityName}`)
                .then(data => data.json())
                .then(data => {
                    thresholds = data[`${attribute}_thresholds`]
                }))
        }
        Promise.all(promisesBeforeDrawing).then(() => fetchAndDrawDiagram())
            .then(() => window.addEventListener('resize', () => drawChart(measures, container.id, attribute, thresholds, strategy, xAxisLabel, fullscreen, locale)))
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