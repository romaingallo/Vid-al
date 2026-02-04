const params = new URLSearchParams(window.location.search);
const alertObj = params.get('alert');

if (alertObj) {
    alert(alertObj);
}