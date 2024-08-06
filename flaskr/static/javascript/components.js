import {LoadingActionButtons} from "./components/appliance-loading-action-buttons.js";
import {CleaningActionButtons} from "./components/appliance-cleaning-action-buttons.js";
import {PowerConsumption} from "./components/appliance-power-consumption.js";
import {ApplianceState} from "./components/appliance-state.js";
import {ApplianceCleaningState} from "./components/appliance-cleaning-state.js";

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
lemonade.createWebComponent('appliance-loading-action-buttons', LoadingActionButtons)
lemonade.createWebComponent('appliance-cleaning-action-buttons', CleaningActionButtons)
lemonade.createWebComponent('appliance-cleaning-state', ApplianceCleaningState)
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
