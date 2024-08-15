import {io} from "./socket.io.min.esm.js";

const socket = io();
socket.on('connect', function () {
    console.debug('Connected to socket')
});
const params = new URL(document.location.toString()).searchParams

export {socket}