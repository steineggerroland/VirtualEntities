import {applianceSocket} from "./app.js";
import {t} from "./translations.js";

function generateNonce() {
    const array = new Uint32Array(1)
    crypto.getRandomValues(array);
    return array.toString();
}

function registerForNotifications() {
    applianceSocket.onAny(async (topic, event) => {
        if (event.event_type === 'finished_run' && !!event.entity_name) {
            const startedAt = new Date(event.run.started_at)
            const finishedAt = new Date(event.run.finished_at)
            const entityName = event.entity_name
            const nonce = generateNonce()

            applianceSocket.once(`appliances/${entityName}/response/${nonce}`, (appliance) => {
                const notification = new Notification(t('notifications.appliance_run_finished_topic', {name: entityName}), {
                    body: t('notifications.appliance_run_finished_body', {run_time: dateFns.formatDistance(startedAt, finishedAt)}),
                    icon: appliance.icon_url,
                    badge: appliance.icon_url,
                    data: {appliance, 'run': {startedAt, finishedAt}}
                })
            })
            applianceSocket.emit(`appliances/request`, {name: entityName, nonce})
        }
    })
}

const params = new URLSearchParams(window.location.search)
if (params.has('browser_notifications') && !!params.get('browser_notifications')) {
    if (Notification.permission !== 'granted') {
        Notification.requestPermission().then((permission) => {
            registerForNotifications()
        })
    } else {
        registerForNotifications()
    }
}
