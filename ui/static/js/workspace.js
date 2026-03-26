document.addEventListener('DOMContentLoaded', () => {
    const toggles = document.querySelectorAll('[data-presenter-target]');
    const views = document.querySelectorAll('[data-presenter-view]');

    if (!toggles.length || !views.length) {
        return;
    }

    toggles.forEach((toggle) => {
        toggle.addEventListener('click', () => {
            const target = toggle.getAttribute('data-presenter-target');

            toggles.forEach((item) => item.classList.toggle('is-active', item === toggle));
            views.forEach((view) => {
                view.classList.toggle('is-active', view.getAttribute('data-presenter-view') === target);
            });
        });
    });
});
