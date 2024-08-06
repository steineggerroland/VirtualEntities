import {socket} from "../refresh.js";

const LoadingActionButtons = function () {
    const self = this;
    const appliance = JSON.parse(self.dataset.applianceJson)
    let content = ''
    if (!!appliance.is_loadable) {
        const socketHandler = event => {
            const oldAppliance = JSON.parse(self.dataset.applianceJson)
            self.dataset.applianceJson = JSON.stringify(event.appliance)
            if (oldAppliance.running_state !== event.appliance.running_state ||
                (oldAppliance.needs_unloading !== event.appliance.needs_unloading)) {
                update()
            }
        }
        const update = () => {
            socket.off(`appliances/${JSON.parse(self.dataset.applianceJson).name}/updated`, socketHandler);
            self.refresh()
        }
        socket.on(`appliances/${JSON.parse(self.dataset.applianceJson).name}/updated`, socketHandler);
        self.submitUnload = function (event) {
            if (event.preventDefault) event.preventDefault();
            fetch(self.dataset.unloadApiUrl, {method: "POST"})
            socket.emit('celebrate')
            return false;
        }
        self.submitLoad = function (event) {
            if (event.preventDefault) event.preventDefault();
            fetch(self.dataset.loadApiUrl, {method: "POST"})
            return false;
        }

        self.unloadLabel = self.dataset.unloadLabel
        self.loadLabel = self.dataset.loadLabel
        if (!!appliance.needs_unloading) {
            content += `<div class="col-4 d-flex flex-column align-items-center justify-content-center">
<form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
          action="#" onsubmit="self.submitUnload">
        <button class="unload btn btn-outline-success p-0 w-100 h-100"
                type="submit" value="{{ self.unloadLabel }}">{{ self.unloadLabel }}</button>
    </form>
</div>`
        } else if (appliance.running_state !== 'running') {
            content += `<div class="col-4 d-flex flex-column align-items-center justify-content-center">
    <form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
          action="#" onsubmit="self.submitLoad">
        <button class="needs-unloading btn btn-outline-primary p-0 w-100 h-100"
                type="submit" value="{{ self.loadLabel }}">{{ self.loadLabel }}</button>
    </form>
</div>`
        }
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