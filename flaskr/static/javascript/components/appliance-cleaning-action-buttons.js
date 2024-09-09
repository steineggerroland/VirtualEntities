import {applianceSocket, behave} from "../app.js";

const CleaningActionButtons = function () {
    const self = this;
    self.appliance = JSON.parse(self.dataset.applianceJson)
    let content = ''
    if (!self.appliance.is_cleanable) {
        self.classList.add('d-none')
        return '<div></div>'
    }
    let submit = () => {
    }
    self.submitHandler = e => submit(e)
    const update = () => {
        if (!!self.appliance.needs_cleaning) {
            self.label = self.dataset.cleanLabel
            self.buttonClass = 'clean'
            self.color = 'success'
            submit = function (event) {
                if (event.preventDefault) event.preventDefault();
                fetch(self.dataset.cleanApiUrl, {method: "POST"})
                return false;
            }
        } else {
            self.label = self.dataset.noticeDirtLabel
            self.buttonClass = 'notice-dirt'
            self.color = 'primary'
            submit = function (event) {
                if (event.preventDefault) event.preventDefault();
                fetch(self.dataset.noticeDirtApiUrl, {method: "POST"})
                return false;
            }
        }
    }
    update()
    const socketHandler = (eventName, event) => {
        if (event.entity_name !== self.appliance.name) return
        self.dataset.applianceJson = JSON.stringify(event.entity)
        self.appliance = event.entity
        update()
    }
    applianceSocket.onAny(socketHandler)
    self.onload = (element) => {
        behave.createLogger('appliance-cleaning-action-buttons').debug('Loaded')
    }
    return `<div class="col-4 fs-5 d-flex flex-column align-items-center justify-content-center">
    <form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
          action="#" onsubmit="self.submitHandler">
        <button class="{{self.buttonClass}} btn btn-outline-{{self.color}} p-0 w-100 h-100"
                type="submit" value="{{ self.label }}">{{ self.label }}</button>
    </form>
</div>`
}
export {CleaningActionButtons}