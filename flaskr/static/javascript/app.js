import {io, Socket} from "./socket.io.min.esm.js";

const socket = io();
const roomSocket = io('/rooms');
const applianceSocket = io('/appliances');
const personSocket = io('/persons');

const params = new URLSearchParams(window.location.search)
const isDebugMode = params.has('debug') && params.get('debug') || params.has('debug.js') && params.get('debug.js');
const createLogger = (name) => {
    return {
        error: (msg) => console.error(`${new Date().toISOString()} <${name}>: ${msg}`),
        debug: !isDebugMode ? () => {
        } : (msg) => console.debug(`${new Date().toISOString()} <${name}>: ${msg}`),
        info: !isDebugMode ? () => {
        } : (msg) => console.info(`${new Date().toISOString()} <${name}>: ${msg}`)
    }
};
const behave = {
    createLogger,
    isDebugMode
}
const logger = createLogger('app');
logger.debug('Logging is enabled')

const sockets = [socket, applianceSocket, roomSocket, personSocket]
sockets.forEach(s => {
    s.on('connect', function () {
        logger.debug(`Connected to ${s.nsp} socket`)
    });
    s.connect()
})
if (behave.isDebugMode) {
    sockets.forEach(s => {
        s.onAny((event) => {
            logger.debug(event)
        });
    });
}
const loader = import("./date-fns@3.6.0.js")
if (document.documentElement.lang === 'de') {
    loader.then(() => import("./date-fns@3.6.0-locale-de.js").then(() => {
        dateFns.setDefaultOptions({locale: dateFns.locale.de})
    }))
}
const are_notifications_enabled = true
loader.then(() => import('./translations.js'))
    .then(() => import('./components.js'))
    .then(() => import('./base.js'))
    .then(() => import('./notifications-service.js'))

export {socket, roomSocket, applianceSocket, personSocket, behave}
