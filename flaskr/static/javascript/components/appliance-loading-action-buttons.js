import {applianceSocket, behave} from "../app.js";

const LoadingActionButtons = function () {
    const self = this;
    self.appliance = JSON.parse(self.dataset.applianceJson)
    let content = ''
    if (!!self.appliance.is_loadable) {
        const socketHandler = (eventName, event) => {
            if (event.entity_name !== self.appliance.name) return
            const oldAppliance = JSON.parse(self.dataset.applianceJson)
            self.dataset.applianceJson = JSON.stringify(event.entity)
            if (oldAppliance.running_state !== event.entity.running_state ||
                (oldAppliance.needs_unloading !== event.entity.needs_unloading)) {
                update()
            }
        }
        const update = () => {
            applianceSocket.offAny(socketHandler);
            self.refresh()
        }
        applianceSocket.onAny(socketHandler);
        self.submitUnload = function (event) {
            if (event.preventDefault) event.preventDefault();
            fetch(self.dataset.unloadApiUrl, {method: "POST"})
            return false;
        }
        self.submitLoad = function (event) {
            if (event.preventDefault) event.preventDefault();
            fetch(self.dataset.loadApiUrl, {method: "POST"})
            return false;
        }

        self.unloadLabel = self.dataset.unloadLabel
        self.loadLabel = self.dataset.loadLabel
        if (!!self.appliance.needs_unloading) {
            content += `<div class="col-4 d-flex flex-column align-items-center justify-content-center">
<form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
          action="#" onsubmit="self.submitUnload">
        <button class="unload btn btn-outline-success p-0 w-100 h-100"
                type="submit" value="{{ self.unloadLabel }}">{{ self.unloadLabel }}</button>
    </form>
</div>`
        } else if (self.appliance.running_state !== 'running') {
            content += `<div class="col-4 d-flex flex-column align-items-center justify-content-center">
    <form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
          action="#" onsubmit="self.submitLoad">
        <button class="needs-unloading btn btn-outline-primary p-0 w-100 h-100"
                type="submit" value="{{ self.loadLabel }}">{{ self.loadLabel }}</button>
    </form>
</div>`
        }
    }
    self.onload = (element) => {
        behave.createLogger('appliance-loading-action-buttons').debug('Loaded')
    }
    if (!!content) {
        self.classList.remove('d-none')
        return content
    } else {
        self.classList.add('d-none')
        return '<div></div>'
    }
}
export {LoadingActionButtons}