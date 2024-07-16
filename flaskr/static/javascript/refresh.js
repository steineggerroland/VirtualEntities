import {io} from "./socket.io.min.esm.js";

const socket = io();
socket.on('connect', function () {
    console.log('Connected to socket')
});
socket.onAny((event) => {
    //console.log(event)
});


export {socket}