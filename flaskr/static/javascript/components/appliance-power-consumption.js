import {socket} from "../refresh.js";

const formatWatt = (watt) => {
    watt = parseFloat(watt)
    if (isNaN(watt)) return {watt_formatted: "?W", watt_formatted_short: "?W"}
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
    return {watt_formatted: watt + "W", watt_formatted_short: value + multiplier + "W"}
}
const PowerConsumption = function () {
    const self = this;
    self.name = self.dataset.name
    const socketHandler = event => {
        self.dataset.watt = event.appliance.watt
        const {watt_formatted, watt_formatted_short} = formatWatt(self.dataset.watt);
        self.watt_formatted_short = watt_formatted_short
        self.watt_formatted = watt_formatted
    };
    socket.on(`appliances/${self.name}/powerConsumptionUpdated`, socketHandler);
    const {watt_formatted, watt_formatted_short} = formatWatt(self.dataset.watt);
    self.watt_formatted_short = watt_formatted_short
    self.watt_formatted = watt_formatted
    return `<span title="{{self.watt_formatted}}">{{ self.watt_formatted_short }}</span>`;
}
export {PowerConsumption}