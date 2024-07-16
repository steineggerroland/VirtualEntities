import {RoomHumidityState} from "./components/room-humidity-state.js";
import {RoomTemperatureState} from "./components/room-temperature-state.js";


lemonade.createWebComponent('room-humidity-state', RoomHumidityState, {
    shadowRoot: false,
});
lemonade.createWebComponent('room-temperature-state', RoomTemperatureState, {
    shadowRoot: false,
});
