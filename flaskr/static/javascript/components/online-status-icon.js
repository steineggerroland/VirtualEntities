import {applianceSocket, behave, personSocket, roomSocket} from "../app.js";

const OnlineStatusIcon = function () {
    const self = this;
    self.svgStyle = self.dataset.svgStyle || ''
    const socket = self.dataset.entityType === 'appliance' ? applianceSocket :
        self.dataset.entityType === 'room' ? roomSocket :
            personSocket
    let interval, tooltip
    const update = async () => {
        self.onlineStatus = self.dataset.onlineStatus.toString().split('.').pop().toLowerCase()
        self.lastSeenAt = self.dataset.lastSeenAt
        if (self.onlineStatus.toLowerCase().endsWith('online')) {
            self.color = '#02f103'
            self.text = self.dataset.onlineLabel
        } else if (self.onlineStatus.toLowerCase().endsWith('offline')) {
            self.color = '#fd0411'
            self.text = self.dataset.offlineLabel
        } else {
            self.color = '#e4dfe1'
            self.text = self.dataset.unknownLabel
        }

        async function resetTooltip() {
            await tooltip.hide()
            await tooltip.dispose()
            tooltip = bootstrap.Tooltip.getOrCreateInstance(self.svgElement)
        }
        if (!!self.lastSeenAt && !interval) {
            const lastSeenAt = dateFns.formatDistanceToNow(new Date(self.lastSeenAt), {addSuffix: true})
            self.text = `${self.dataset.lastSeenLabel} ${lastSeenAt}`
            await resetTooltip()
            interval = setInterval(async () => {
                const lastSeenAt = dateFns.formatDistanceToNow(new Date(self.lastSeenAt), {addSuffix: true})
                self.text = `${self.dataset.lastSeenLabel} ${lastSeenAt}`
                if (!!tooltip) {
                    await resetTooltip();
                }
            }, (50 + Math.round(Math.random() * 20)) * 1000)
        } else if (!self.lastSeenAt && interval) {
            clearInterval(interval)
        }
    }
    update()
    const socketHandler = (eventName, event) => {
        if (event.entity_name !== self.dataset.entityName) return
        const entity = event.entity
        if (self.dataset.onlineStatus !== entity['online_status'] ||
            self.dataset.lastSeenAt !== entity['last_seen_at']) {
            self.dataset.onlineStatus = entity['online_status']
            self.dataset.lastSeenAt = entity['last_seen_at'] || ''
            update()
        }
    }
    socket.onAny(socketHandler)
    self.onload = (element) => {
        tooltip = bootstrap.Tooltip.getOrCreateInstance(self.svgElement)
        behave.createLogger('online-status-icon').debug('Loaded')
    }
    return `<><svg :ref="self.svgElement" height="20" width="20" xmlns="http://www.w3.org/2000/svg" style="{{ self.svgStyle }}" data-bs-title="{{ self.text }}"
     data-bs-toggle="tooltip">
    <circle r="8" cx="10" cy="10" stroke-width="1" fill="{{ self.color }}" stroke="lightgray"></circle>
</svg><span class="visually-hidden online-status">{{self.onlineStatus}}</span></>`
}

export {OnlineStatusIcon}