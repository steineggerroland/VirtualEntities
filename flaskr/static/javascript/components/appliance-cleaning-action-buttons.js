import {socket} from "../refresh.js";

const CleaningActionButtons = function () {
    const self = this;
    self.appliance = JSON.parse(self.dataset.applianceJson)
    let content = ''
    if (!self.appliance.is_cleanable) {
        self.classList.add('d-none')
        return '<div></div>'
    }
    let submit = () => {}
    self.submitHandler = e => submit(e)
    const update = () => {
        if (!!self.appliance.needs_cleaning) {
            self.label = self.dataset.cleanLabel
            self.buttonClass = 'clean'
            self.color = 'success'
            submit = function (event) {
                if (event.preventDefault) event.preventDefault();
                fetch(self.dataset.cleanApiUrl, {method: "POST"})
                socket.emit('celebrate')
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
    const socketHandler = event => {
        self.dataset.applianceJson = JSON.stringify(event.appliance)
        self.appliance = event.appliance
        console.log(self.appliance)
        update()
    }
    socket.on(`appliances/${JSON.parse(self.dataset.applianceJson).name}/updated`, socketHandler)
    return `<div class="col-4 fs-5 d-flex flex-column align-items-center justify-content-center">
    <form class="w-100 w-sm-75 overflow-hidden" style="aspect-ratio: 1" method="get"
          action="#" onsubmit="self.submitHandler">
        <button class="{{self.buttonClass}} btn btn-outline-{{self.color}} p-0 w-100 h-100"
                type="submit" value="{{ self.label }}">{{ self.label }}</button>
    </form>
</div>`
}
export {CleaningActionButtons}