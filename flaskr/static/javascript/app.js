import {io} from "./socket.io.min.esm.js";

const socket = io();

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

socket.on('connect', function () {
    logger.debug('Connected to socket')
});
if (behave.isDebugMode) {
    socket.onAny((event) => {
        logger.debug(event)
    });
}
const loader = import("./date-fns@3.6.0.js")
if (document.documentElement.lang === 'de') {
    loader.then(() => import("./date-fns@3.6.0-locale-de.js").then(() => {
        dateFns.setDefaultOptions({locale: dateFns.locale.de})
    }))
}
loader.then(() => import('./components.js'))
    .then(() => import('./base.js'))

export {socket, behave}
