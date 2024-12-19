document.addEventListener('click', function (event) {
    if (event.target.matches('.subscribe-btn')) {
        const button = event.target;
        const actionUrl = button.getAttribute('data-action-url');

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.status === 'subscribed') {
                    button.textContent = 'Unsubscribe';
                    button.classList.remove('subscribe');
                    button.classList.add('unsubscribe');
                } else if (data.status === 'unsubscribed') {
                    button.textContent = 'Subscribe';
                    button.classList.remove('unsubscribe');
                    button.classList.add('subscribe');
                }
            })
            .catch((error) => console.error('Error:', error));
    }

    if (event.target.matches('.like, .dislike')) {
        event.preventDefault();
        const button = event.target;
        const form = button.closest('form');
        const actionUrl = form.action;

        fetch(actionUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
        })
            .then((response) => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('Network response was not ok');
            })
            .then((data) => {
                console.log('Action successful:', data);
                location.reload();
            })
            .catch((error) => console.error('Error:', error));
    }
});

setTimeout(function () {
    const msg = document.getElementById('msg');
    if (msg) {
        msg.remove();
    }
}, 5000);
