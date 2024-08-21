import {applianceSocket, behave} from "../app.js";

const ApplianceState = function () {
    const self = this;
    const appliance = JSON.parse(self.dataset.applianceJson)
    self.text = self.color = self.icon = null
    const socketHandler = (eventName, event) => {
        if (!eventName.startsWith(appliance.name)) return
        const oldAppliance = JSON.parse(self.dataset.applianceJson)
        self.dataset.applianceJson = JSON.stringify(event.appliance)
        if (oldAppliance.running_state !== event.appliance.running_state ||
            (oldAppliance.type !== event.appliance.type) ||
            (oldAppliance.needs_unloading !== event.appliance.needs_unloading) ||
            (oldAppliance.started_run_at !== event.appliance.started_run_at)) {
            refresh()
        }
    }
    const refresh = () => {
        if (self.interval) {
            clearInterval(self.interval)
        }
        applianceSocket.offAny(socketHandler);
        self.refresh()
    }
    applianceSocket.onAny(socketHandler);
    if (appliance.running_state === 'running') {
        self.text = self.dataset.runningLabel
        self.color = 'warning'
        switch (appliance.type) {
            case 'dishwasher':
                self.icon = self.dataset.runningDishwasherIconUrl
                break
            case 'dryer':
                self.icon = self.dataset.runningDryerIconUrl
                break
            case 'washing_machine':
                self.icon = self.dataset.runningWashingMachineIconUrl
                break
            default:
                self.icon = self.dataset.runningApplianceIconUrl
        }
        self.runTimer = ''
        if (!!appliance.started_run_at) {
            let startTime = new Date(appliance.started_run_at);

            function updateElapsedTime() {
                let currentTime = new Date();
                let timeDifference = currentTime - startTime;

                //let seconds = Math.floor((timeDifference / 1000) % 60);
                let minutes = Math.floor((timeDifference / 1000 / 60) % 60);
                let hours = Math.floor(timeDifference / 1000 / 60 / 60);

                let formattedHours = ('' + hours).slice(-2);
                let formattedMinutes = ('0' + minutes).slice(-2);
                //let formattedSeconds = ('0' + seconds).slice(-2);

                self.runTimer = `${formattedHours}:${formattedMinutes}`;
                //timeSpan.textContent = `${formattedHours}:${formattedMinutes}:${formattedSeconds}`;
            }

            // Update time immediately
            updateElapsedTime();
            // Set the interval to update the time every second
            self.interval = setInterval(updateElapsedTime, 30 * 1000);
        }
    } else if (appliance.needs_unloading) {
        self.text = self.dataset.loadedLabel
        self.color = 'danger'
        switch (appliance.type) {
            case 'dishwasher':
                self.icon = self.dataset.loadedDishwasherIconUrl
                break
            case 'dryer':
                self.icon = self.dataset.loadedDryerIconUrl
                break
            case 'washing_machine':
                self.icon = self.dataset.loadedWashingMachineIconUrl
                break
            default:
                self.icon = self.dataset.loadedApplianceIconUrl
        }
    } else {
        self.text = self.dataset.idlingLabel
        self.color = 'success'
    }
    self.runningSinceLabel = self.dataset.runningSinceLabel
    self.onload = (element) => {
        behave.createLogger('appliance-state').debug('Loaded')
    }
    let template = `<div class="running-state w-100 overflow-hidden text-bg-{{ self.color }} bg-{{ self.color }} align-content-center text-center"
             style="aspect-ratio: 1" role="status">`
    if (appliance.running_state == 'running') {
        template += `<div class="visually-hidden">{{self.text}}</div>
        <img class="icon" src="{{self.icon}}" alt="{{self.runningSinceLabel}}"/>
        <div>{{self.runTimer}}</div>`
    } else if (appliance.needs_unloading) {
        template += `<img class="icon" src="{{self.icon}}"
             alt="{{self.finishedLastRunBeforeLabel}}"/>
        <div>{{self.text}}</div>`
    } else {
        template += `{{self.text}}`
    }
    template += `</div>`
    return template
}
export {ApplianceState}
