import {ActionButtons} from "./components/appliance-action-buttons.js";
import {PowerConsumption} from "./components/appliance-power-consumption.js";
import {ApplianceState} from "./components/appliance-state.js";


lemonade.createWebComponent('power-consumption', PowerConsumption, {
    shadowRoot: false,
});
lemonade.createWebComponent('appliance-action-buttons', ActionButtons, {
    shadowRoot: false,
});
lemonade.createWebComponent('appliance-state', ApplianceState, {
    shadowRoot: false,
});
