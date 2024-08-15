import {socket, behave} from "../app.js";

const RoomTemperatureState = function () {
    const self = this
    const room = JSON.parse(self.dataset.roomJson)
    const socketHandler = event => {
        const oldState = JSON.parse(self.dataset.roomJson)
        self.dataset.roomJson = JSON.stringify(event.room)
        if (oldState.temperature_rating !== event.room.temperature_rating) {
            socket.off(`rooms/${room.name}/updated`, socketHandler);
            self.refresh()
        } else {
            if (!!event.room.temperature.value) {
                self.text = parseFloat(event.room.temperature.value).toPrecision(3) + "°C"
            } else {
                self.text = "?°C"
            }
        }
    };
    socket.on(`rooms/${room.name}/updated`, socketHandler);
    self.rating = room.temperature_rating
    if (!!room.temperature) {
        self.text = parseFloat(room.temperature.value).toPrecision(3) + "°C"
        switch (self.rating) {
            case 'unknown':
                self.tooltip = self.dataset.defaultLabel
                self.color = 'secondary'
                self.iconUrl = self.dataset.defaultIconUrl
                break
            case 'optimal':
                self.tooltip = self.dataset.optimalLabel
                self.color = 'success'
                self.iconUrl = self.dataset.optimalIconUrl
                break
            case 'hot':
                self.tooltip = self.dataset.hotLabel
                self.color = 'warning'
                self.iconUrl = self.dataset.hotIconUrl
                break
            case 'critical_hot':
                self.tooltip = self.dataset.criticalHotLabel
                self.color = 'danger'
                self.iconUrl = self.dataset.criticalHotIconUrl
                break
            case 'cold':
                self.tooltip = self.dataset.coldLabel
                self.color = 'warning'
                self.iconUrl = self.dataset.coldIconUrl
                break
            default:
                self.tooltip = self.dataset.criticalColdLabel
                self.color = 'danger'
                self.iconUrl = self.dataset.criticalColdIconUrl
        }
    } else {
        self.text = "?°C"
        self.tooltip = self.dataset.unknwonLabel
        self.color = 'secondary'
        self.iconUrl = self.dataset.unknownIconUrl
    }

    self.onload = (element) => {
        behave.createLogger('room-temperature-state').debug('Loaded')
    }
    let template = '<div style="display: contents !important;">'
    if (!!self.dataset.asBadge) {
        template += `
            <span class="badge temperature text-bg-light border border-{{ self.color }}"
               data-bs-title="{{ self.tooltip }}"
               data-bs-toggle="tooltip">{{ self.text }}</span>`
    } else {
        template += `
            <div class="temperature h-100 w-100 text-center align-content-center text-bg-{{ self.color }} bg-{{ self.color }}"
                data-bs-title="{{ self.tooltip }}" data-bs-toggle="tooltip">
                 <img class="icon" src="{{ self.iconUrl }}" alt="{{ self.text }}"/>
                 <div>{{ self.text }}</div>
            </div>`
    }
    template += `
            <span class="visually-hidden temperature-rating temperature-rating-{{ self.rating }}" role="status">{{self.rating}}</span>
            <style>
            .temperature .icon {
                 height: 50%;
                 mix-blend-mode: multiply;
            }
            
            .temperature:has(.temperature-rating-unknown) .icon {
                 filter: invert();
                 mix-blend-mode: unset;
            }
            </style>
        </div>`
    return template
}
export {RoomTemperatureState}
