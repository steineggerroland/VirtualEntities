const translations = (styx && styx.translations) ? styx.translations : {}

const t = (key, args) => {
    let text = translations[key] || ''
    for (const argKey in args) {
        text = text.replace(`{${argKey}}`, args[argKey])
    }
    return text
}

export {t}