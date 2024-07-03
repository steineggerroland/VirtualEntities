const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

(function () {
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
})()