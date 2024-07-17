import {ActionButtons} from "./components/appliance-action-buttons.js";
import {PowerConsumption} from "./components/appliance-power-consumption.js";
import {ApplianceState} from "./components/appliance-state.js";

import {RoomHumidityState} from "./components/room-humidity-state.js";
import {RoomTemperatureState} from "./components/room-temperature-state.js";

import {ConfettiWall} from "./components/celebration.js";


/* GENERAL COMPONENTS */
lemonade.createWebComponent('confetti-wall', ConfettiWall, {
    shadowRoot: false,
});


/* APPLIANCE COMPONENTS */
lemonade.createWebComponent('power-consumption', PowerConsumption, {
    shadowRoot: false,
});
lemonade.createWebComponent('appliance-action-buttons', ActionButtons, {
    shadowRoot: false,
});
lemonade.createWebComponent('appliance-state', ApplianceState, {
    shadowRoot: false,
});


/* ROOM COMPONENTS */
lemonade.createWebComponent('room-humidity-state', RoomHumidityState, {
    shadowRoot: false,
});
lemonade.createWebComponent('room-temperature-state', RoomTemperatureState, {
    shadowRoot: false,
});
