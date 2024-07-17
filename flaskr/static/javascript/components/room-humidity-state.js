import {socket} from "../refresh.js";

const RoomHumidityState = function () {
    const self = this
    const room = JSON.parse(self.dataset.roomJson)
    const socketHandler = event => {
        const oldState = JSON.parse(self.dataset.roomJson)
        self.dataset.roomJson = JSON.stringify(event.room)
        if (oldState.humidity_rating !== event.room.humidity_rating) {
            socket.off(`rooms/${room.name}/updated`, socketHandler);
            self.refresh()
        } else {
            self.text = parseFloat(event.room.humidity).toPrecision(3) + "%"
        }
    };
    socket.on(`rooms/${room.name}/updated`, socketHandler);
    self.rating = room.humidity_rating
    if (!!room.humidity) {
        self.text = parseFloat(room.humidity).toPrecision(3) + "%"
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
            case 'dry':
                self.tooltip = self.dataset.dryLabel
                self.color = 'warning'
                self.iconUrl = self.dataset.dryIconUrl
                break
            case 'critical_dry':
                self.tooltip = self.dataset.criticalDryLabel
                self.color = 'danger'
                self.iconUrl = self.dataset.criticalDryIconUrl
                break
            case 'wet':
                self.tooltip = self.dataset.wetLabel
                self.color = 'warning'
                self.iconUrl = self.dataset.wetIconUrl
                break
            default:
                self.tooltip = self.dataset.criticalWetLabel
                self.color = 'danger'
                self.iconUrl = self.dataset.criticalWetIconUrl
        }
    } else {
        self.text = "?%"
        self.tooltip = self.dataset.unknwonLabel
        self.color = 'secondary'
        self.iconUrl = self.dataset.unknownIconUrl
    }

    let template = '<div style="display: contents !important;">'
    if (!!self.dataset.asBadge) {
        template += `
            <span class="humidity badge text-bg-light border border-{{ self.color }}"
               data-bs-title="{{ self.tooltip }}"
               data-bs-toggle="tooltip">{{ self.text }}</span>`
    } else {
        template += `
            <div class="humidity h-100 w-100 text-center align-content-center text-bg-{{ self.color }} bg-{{ self.color }}"
                data-bs-title="{{ self.tooltip }}" data-bs-toggle="tooltip">
                 <img class="icon" src="{{ self.iconUrl }}" alt="{{ self.text }}"/>
                 <div>{{ self.text }}</div>
            </div>`
    }
    template += `
            <span class="visually-hidden humidity-rating humidity-rating-{{ self.rating }}" role="status">{{self.rating}}</span>
            <style>
            .humidity .icon {
                 height: 50%;
                 mix-blend-mode: multiply;
            }
            
            .humidity:has(.humidity-rating-unknown) .icon {
                 filter: invert();
                 mix-blend-mode: unset;
            }
            </style>
        </div>`
    return template
}
export {RoomHumidityState}
