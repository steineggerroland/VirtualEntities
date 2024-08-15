import {socket} from "../refresh.js";

const formatWatt = (watt) => {
    watt = parseFloat(watt)
    if (isNaN(watt)) return {wattFormatted: "?W", wattFormattedShort: "?W"}
    let multiplier = ""
    let value = watt
    if (watt >= 1000) {
        value = (watt / 1000).toPrecision(Math.max(2, Math.ceil(Math.log10(watt / 1000))))
        multiplier = "k"
    } else if (watt >= 10) {
        value = watt.toPrecision(Math.max(1, Math.ceil(Math.log10(watt))))
    } else {
        value = watt.toPrecision(2)
    }
    return {wattFormatted: watt + "W", wattFormattedShort: value + multiplier + "W"}
}
const PowerConsumption = function () {
    const self = this;
    self.asBadge = !!self.dataset.asBadge
    self.name = self.dataset.name
    self.tooltip = self.dataset.tooltip
    let bootstrap_tooltip

    function update() {
        const {wattFormatted, wattFormattedShort} = formatWatt(self.dataset.watt);
        self.wattFormattedShort = wattFormattedShort
        self.wattFormatted = wattFormatted
    }

    const socketHandler = event => {
        if (self.dataset.powerState !== event.appliance['power_state'] &&
            (self.dataset.powerState === 'charging' || event.appliance['power_state'] === 'charging')) {
            self.dataset.powerState = event.appliance['power_state']
            self.dataset.watt = event.appliance.watt
            socket.off(`appliances/${self.name}/power-consumption/updated`, socketHandler);
            self.refresh()
        } else if (parseFloat(self.dataset.watt) !== event.appliance.watt) {
            self.dataset.watt = event.appliance.watt
            update()
        }
    };
    update()
    socket.on(`appliances/${self.name}/power-consumption/updated`, socketHandler);
    self.onload = (element) => {
        bootstrap_tooltip = new bootstrap.Tooltip(element)
    }
    const wattSpan = `<span title="{{ self.wattFormatted }}">{{ self.wattFormattedShort }}</span>`
    if (self.asBadge) {
        return `<span class="badge text-bg-secondary power-consumption" data-bs-title="{{ self.tooltip }}"
          data-bs-toggle="tooltip">${wattSpan}</span>`
    } else {
        let template = `<div class="h-100 w-100 d-flex flex-column justify-content-center align-items-center power-consumption" data-bs-title="{{ self.tooltip }}" data-bs-toggle="tooltip">`
        template += self.dataset.powerState === 'charging' ? `<img class="icon charging" src="${self.dataset.chargingIconUrl}" alt="" />` : ' '
        template += wattSpan
        template += `</div>`;
        return template
    }
}
export {PowerConsumption}