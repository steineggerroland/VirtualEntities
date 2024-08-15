import {socket, behave} from "../app.js";

const ApplianceCleaningState = function () {
    const self = this;
    self.appliance = JSON.parse(self.dataset.applianceJson)
    if (!self.appliance.is_cleanable) return '<></>'
    const socketHandler = event => {
        const oldAppliance = JSON.parse(self.dataset.applianceJson)
        self.dataset.applianceJson = JSON.stringify(event.appliance)
        self.appliance = event.appliance
        if (oldAppliance.needs_cleaning !== self.appliance.needs_cleaning) {
            update()
        }
    }
    const update = () => {
        if (self.appliance.needs_cleaning) {
            self.text = self.dataset.needsCleaningLabel
            self.color = 'danger'
            self.classList.remove('d-none')
        } else {
            self.text = self.dataset.isCleanLabel
            self.color = 'success'
            self.classList.add('d-none')
        }
    }
    socket.on(`appliances/${self.appliance.name}/updated`, socketHandler);
    update()
    self.onload = (element) => {
        behave.createLogger('appliance-cleaning-state').debug('Loaded')
    }
    let template = '<div class="cleanliness w-100 overflow-hidden align-content-center text-center ' +
        'text-bg-{{ self.color }} bg-{{ self.color }}" style="aspect-ratio: 1">'
    template += '{{self.text}}'
    template += '</div>'
    return template
}
export {ApplianceCleaningState}