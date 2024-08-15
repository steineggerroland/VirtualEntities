import "./refresh.js";
import "./components.js";
import {socket} from "./refresh.js";

const behave = (function () {
    const params = new URLSearchParams(window.location.search)
    if (params.has('refresh_interval')) {
        setTimeout(() => {
            window.location.reload()
        }, params.get('refresh_interval') * 1000)
    }

    document.querySelectorAll('a.back').forEach(element => {
        if (element.href === document.referrer) {
            element.setAttribute('href', 'javascript:window.history.back()')
        }
    })
    document.querySelectorAll('.running-state').forEach(element => {
        if (!element.dataset.startedRunAt) return;
        let startTime = new Date(element.dataset.startedRunAt);
        let timeSpan = document.createElement('div');
        element.insertAdjacentElement('beforeend', timeSpan);

        function updateElapsedTime() {
            let currentTime = new Date();
            let timeDifference = currentTime - startTime;

            //let seconds = Math.floor((timeDifference / 1000) % 60);
            let minutes = Math.floor((timeDifference / 1000 / 60) % 60);
            let hours = Math.floor(timeDifference / 1000 / 60 / 60);

            let formattedHours = ('' + hours).slice(-2);
            let formattedMinutes = ('0' + minutes).slice(-2);
            //let formattedSeconds = ('0' + seconds).slice(-2);

            timeSpan.textContent = `${formattedHours}:${formattedMinutes}`;
            //timeSpan.textContent = `${formattedHours}:${formattedMinutes}:${formattedSeconds}`;
        }

        // Update time immediately
        updateElapsedTime();

        // Set the interval to update the time every second
        setInterval(updateElapsedTime, 60 * 1000);
    })

    document.querySelectorAll('form').forEach(form => {
        if (!form.dataset.apiUrl) return
        form.onsubmit = event => {
            if (event.preventDefault) event.preventDefault();
            fetch(form.dataset.apiUrl, {method: "POST"}).then(() => {
                window.location.reload()
            })
            return false;
        }
        form.querySelectorAll('[type="submit"]').forEach(submitElement => {
            submitElement.removeAttribute('disabled')
        })
    })

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    const isDebugMode = params.has('debug') && params.get('debug') || params.has('debug.js') && params.get('debug.js');
    return {
        logger: (name) => {
            return {
                error: (msg) => console.error(`${new Date().toISOString()} <${name}>: ${msg}`),
                debug: !isDebugMode ? () => {
                } : (msg) => console.debug(`${new Date().toISOString()} <${name}>: ${msg}`),
                info: !isDebugMode ? () => {
                } : (msg) => console.info(`${new Date().toISOString()} <${name}>: ${msg}`)
            }
        },
        isDebugMode
    }
})()

behave.logger('base').debug('Logging is enabled')

if (behave.isDebugMode) {
    socket.onAny((event) => {
        behave.logger('ws').debug(event)
    });
}

export {behave}