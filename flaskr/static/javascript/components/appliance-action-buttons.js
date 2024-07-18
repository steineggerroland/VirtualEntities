import {socket} from "../refresh.js";

const ActionButtons = function () {
    const self = this;
    const socketHandler = event => {
        const oldAppliance = JSON.parse(self.dataset.applianceJson)
        self.dataset.applianceJson = JSON.stringify(event.appliance)
        if (oldAppliance.running_state !== event.appliance.running_state ||
            (oldAppliance.needs_unloading !== event.appliance.needs_unloading)) {
            socket.off(`appliances/${JSON.parse(self.dataset.applianceJson).name}/updated`, socketHandler);
            self.refresh()
        }
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
    const appliance = JSON.parse(self.dataset.applianceJson)
    const unloadButtonHtml = `<form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
                      action="#" onsubmit="self.submitUnload">
                    <button class="unload btn btn-outline-success p-0 w-100 h-100"
                            type="submit" value="{{ self.unloadLabel }}">{{ self.unloadLabel }}</button>
                </form>`
    const loadButtonHtml = `<form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
                      action="#" onsubmit="self.submitLoad">
                    <button class="needs-unloading btn btn-outline-primary p-0 w-100 h-100"
                            type="submit" value="{{ self.loadLabel }}">{{ self.loadLabel }}</button>
                </form>`
    return !!appliance.needs_unloading ? unloadButtonHtml : (appliance.running_state !== 'running') ? loadButtonHtml : '<div></div>'
}
export {ActionButtons}