import {io} from "./socket.io.min.esm.js";

const socket = io();
socket.on('connect', function () {
    console.debug('Connected to socket')
});
socket.onAny((event) => {
    //console.log(`${new Date().getTime()}: ${event}`)
});


export {socket}