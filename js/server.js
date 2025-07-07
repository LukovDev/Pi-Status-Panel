//
// server.js - Код реализовывающий логику страницы и работы с сервером.
//


// Отправить данные серверу:
function sendJsonPost(url, data) {
    return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    }).then(response => {
        if (!response.ok) throw new Error('Server Error: ' + response.status);
        return response.json();
    });
}


// Обновить все элементы по айди с Json данных:
function updateElementsFromJson(data) {
    for (const [className, text] of Object.entries(data["classes"])) {
        const elements = document.getElementsByClassName(className);
        if (elements.length === 0) {
            console.warn(`No elements with class "${className}" found.`);
        }
        for (const el of elements) {
            el.textContent = text;
        }
    }
    for (const [id, text] of Object.entries(data["ids"])) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = text;
        } else {
            console.warn(`Element of id "${id}" not found.`);
        }
    }
}


// Создать графики нагрузки процессора:
function CreateCPUUsageBars(value, id_name) {
    const container = document.getElementById(id_name);
    const usage = Math.min(Math.max(parseFloat(value), 0), 100).toFixed(1);

    // Ищем существующий fill:
    let fill = container.querySelector('.progress-bar-fill');
    if (!fill) {
        // Если нет — строим структуру:
        container.innerHTML = '';

        // Текст:
        const info = document.createElement("div");
        info.className = "inline-no-border";
        info.innerHTML = `<div>CPU</div><div>${usage}%</div>`;
        container.appendChild(info);

        // Бар:
        const bar = document.createElement("div");
        bar.className = "progress-bar";
        fill = document.createElement("div");
        fill.className = "progress-bar-fill";
        fill.style.width = '0%';
        bar.appendChild(fill);
        container.appendChild(bar);

        // Делаем первый кадр, чтобы браузер "увидел" 0%:
        requestAnimationFrame(() => {
            fill.style.width = `${usage}%`;
        });
    } else {
        // Если уже есть — просто обновляем ширину:
        const percentDiv = container.querySelector('.inline-no-border > div:last-child');
        if (percentDiv) percentDiv.textContent = `${usage}%`;
        // Запускаем анимацию:
        fill.style.width = `${usage}%`;
    }

    // Если больше 90%, делаем красным:
    if (usage >= 90) {
        fill.classList.add('progress-danger');
    } else {
        fill.classList.remove('progress-danger');
    }
}


// Создать графики нагрузки ядер процессора:
function CreateCPUCoreUsageBars(data, id_name) {
    const container = document.getElementById(id_name);

    data.forEach(([core, usageStr], idx) => {
        const usage = Math.min(Math.max(parseFloat(usageStr), 0), 100).toFixed(1);

        // Для каждого ядра будем искать существующий блок по data-core атрибуту:
        let coreBlock = container.querySelector(`[data-core="${core}"]`);

        if (!coreBlock) {
            // Если нет — создаём:
            coreBlock = document.createElement("div");
            coreBlock.dataset.core = core;

            // Текст:
            const info = document.createElement("div");
            info.className = "inline-no-border";
            info.innerHTML = `<div>${core}</div><div>${usage}%</div>`;
            coreBlock.appendChild(info);

            // Бар:
            const bar = document.createElement("div");
            bar.className = "progress-bar";
            const fill = document.createElement("div");
            fill.className = "progress-bar-fill";
            fill.style.width = '0%';
            bar.appendChild(fill);
            coreBlock.appendChild(bar);

            container.appendChild(coreBlock);

            // Стартовая анимация:
            requestAnimationFrame(() => {
                fill.style.width = `${usage}%`;
            });

            // Если больше 90%, делаем красным:
            if (usage >= 90) {
                fill.classList.add('progress-danger');
            } else {
                fill.classList.remove('progress-danger');
            }
        } else {
            // Обновляем существующий:
            const info = coreBlock.querySelector('.inline-no-border');
            if (info) {
                const percentDiv = info.querySelector('div:last-child');
                if (percentDiv) percentDiv.textContent = `${usage}%`;
            }
            const fill = coreBlock.querySelector('.progress-bar-fill');
            if (fill) fill.style.width = `${usage}%`;

            // Если больше 90%, делаем красным:
            if (usage >= 90) {
                fill.classList.add('progress-danger');
            } else {
                fill.classList.remove('progress-danger');
            }
        }
    });

    // Удалить устаревшие блоки (если ядер стало меньше):
    const existing = Array.from(container.querySelectorAll('[data-core]'));
    existing.forEach(el => {
        const core = el.dataset.core;
        if (!data.find(([c]) => c === core)) {
            el.remove();
        }
    });
}


// Инициализировать кольца прогресса:
function initProgressRings() {
    const rings = document.querySelectorAll(".progress-ring");
    for (const ring of rings) {
        ring.innerHTML = `
            <svg viewBox="0 0 64 64" class="progress-ring-svg">
                <circle class="progress-ring-bg" cx="32" cy="32" r="0"/>
                <circle class="progress-ring-value" cx="32" cy="32" r="0"/>
            </svg>
        `;
    }
}


// Установить параметры круглого прогрессбара:
function setProgressRingById(id, value, radius) {
    usage = Math.min(Math.max(value, 0.0), 100.0);
    const el = document.getElementById(id);
    if (!el) return;

    const circle = el.querySelector('.progress-ring-value');
    const bgCircle = el.querySelector('.progress-ring-bg');
    if (!circle || !bgCircle) return;

    // Устанавливаем радиус у кругов (основного и фона):
    circle.r.baseVal.value = radius;
    bgCircle.r.baseVal.value = radius;

    // Вычисляем длину окружности:
    const circumference = 2 * Math.PI * radius;

    // Обновляем стили для анимации прогресса:
    circle.style.strokeDasharray = circumference;
    circle.style.strokeDashoffset = circumference * (1 - usage / 100);

    // Обновляем data-атрибут и текст, если есть:
    el.dataset.value = usage;

    // Если больше 90%, делаем красным:
    if (usage >= 90) {
        circle.classList.add('progress-danger');
    } else {
        circle.classList.remove('progress-danger');
    }
}


// Функция инициализации страницы:
function init_websize() {
    // Отключаем анимации у кругов:
    const rings = document.querySelectorAll('.progress-ring-value');
    rings.forEach(circle => { circle.style.transition = 'none'; });

    // Инициализируем кольца прогресса:
    initProgressRings();

    // Создаём диаграммы:
    setProgressRingById("ring-ram-using", 0, 20);
    setProgressRingById("ring-storage-using", 0, 20);
    CreateCPUUsageBars(0.0, "cpu-usage-container");
    CreateCPUCoreUsageBars([
        ["Core 0", "0.0"], ["Core 1", "0.0"], ["Core 2", "0.0"], ["Core 3", "0.0"]
    ], "cpu-cores-usage-container");

    // Включаем анимации у кругов:
    requestAnimationFrame(() => {
        rings.forEach(circle => { circle.style.transition = ''; });
    });
}


/*
    < Pi-Status-Panel >
    By LukovDev (@mr_lukov).
    License: MIT
    lakuworx@gmail.com

    Thank you for Using!
*/
