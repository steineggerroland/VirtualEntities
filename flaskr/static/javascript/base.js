const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

(function () {
   document.querySelectorAll('a.back').forEach(elem => {
       if (elem.href===document.referrer) {
           elem.setAttribute('href', 'javascript:window.history.back()')
       }
   })
})()