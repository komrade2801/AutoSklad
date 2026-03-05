function doImportTools() {
    const selectedFile = document.getElementById("importToolsFile").files[0];
    const useCount = document.getElementById("getToolCount").checked;
    const endpointUrl = "../backend/upload";
    const formData = new FormData();
    const btnImport = document.getElementById("importTools");
    const fileInput = document.getElementById("importToolsFile");
    const form = document.getElementById("importToolsForm");

    if (!selectedFile) {
        return;
    }

    formData.append("file", selectedFile);
    formData.append("use_count", useCount);

    // Блокировка UI до конца загрузки/обработки
    const lockUi = () => {
        if (btnImport) {
            btnImport.disabled = true;
            btnImport.textContent = "Загрузка…";
        }
        if (fileInput) fileInput.disabled = true;
        if (form) form.style.pointerEvents = "none";
    };
    const unlockUi = () => {
        if (btnImport) {
            btnImport.disabled = false;
            btnImport.textContent = "Загрузить xlsx";
        }
        if (fileInput) fileInput.disabled = false;
        if (form) form.style.pointerEvents = "";
    };

    lockUi();

    console.log("[Импорт Excel] Отправка файла:", selectedFile.name, "| Учитывать количество:", useCount);

    var uploadTimeoutMs = 10 * 60 * 1000;
    var controller = new AbortController();
    var timeoutId = setTimeout(function () { controller.abort(); }, uploadTimeoutMs);
    var unlockInFinally = true;

    function showResultToast(result) {
        var errorsTotal = result.errors_total ?? (Array.isArray(result.errors) ? result.errors.length : 0);
        var added = (result.processed || 0) - (result.repeated || 0);
        var repeated = result.repeated || 0;
        var ignored = errorsTotal;
        var msg = "Импорт завершён. ";
        if (added > 0) msg += "Добавлено: " + added + ". ";
        if (repeated > 0) msg += "Повторов (уже существовали): " + repeated + ". ";
        if (ignored > 0) msg += "Пропущено (ошибки/нет полей): " + ignored + ".";
        if (added === 0 && repeated === 0 && ignored === 0) msg += "Нет данных для импорта.";
        var toastType = ignored > 0 && (added > 0 || repeated > 0) ? "info" : (ignored > 0 ? "warning" : "success");
        if (typeof showToast === "function") showToast(msg.trim(), toastType);
    }

    function pollStatus(jobId) {
        var statusUrl = "../backend/upload/status/" + jobId;
        var pollInterval = 2000;
        var deadline = Date.now() + uploadTimeoutMs;
        function poll() {
            if (Date.now() > deadline) {
                if (typeof showToast === "function") showToast("Импорт отменён по таймауту (10 мин).", "danger");
                unlockUi();
                return;
            }
            fetch(statusUrl)
                .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error(r.status)); })
                .then(function (st) {
                    if (st.status === "completed") {
                        console.log("[Импорт Excel] Фоновый импорт завершён:", st.result);
                        showResultToast(st.result || {});
                        if (typeof loadToolLibraryTable === "function") loadToolLibraryTable(1);
                        unlockUi();
                        return;
                    }
                    if (st.status === "failed") {
                        var errMsg = st.error || "Импорт завершился с ошибкой.";
                        if (typeof showToast === "function") showToast(errMsg, "danger");
                        unlockUi();
                        return;
                    }
                    setTimeout(poll, pollInterval);
                })
                .catch(function (err) {
                    console.error("Ошибка опроса статуса:", err);
                    if (typeof showToast === "function") showToast("Ошибка при проверке статуса импорта.", "danger");
                    unlockUi();
                });
        }
        poll();
    }

    fetch(endpointUrl, {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(function (response) {
        if (response.status === 202) {
            return response.json().then(function (data) {
                var jobId = data.job_id;
                if (jobId) {
                    unlockInFinally = false;
                    console.log("[Импорт Excel] Запущен в фоне, job_id:", jobId);
                    pollStatus(jobId);
                } else {
                    unlockUi();
                }
            });
        }
        if (!response.ok) {
            return response.json().then(function (errData) {
                throw new Error(errData.detail || 'Ошибка сети: ' + response.status);
            });
        }
        return response.json();
    })
    .then(function (result) {
        if (!result) return;
        if (result.job_id) return;
        showResultToast(result);
        if (typeof loadToolLibraryTable === "function") loadToolLibraryTable(1);
    })
    .catch(function (error) {
        console.error("Ошибка при импорте:", error);
        var msg = error.name === "AbortError" ? "Импорт отменён по таймауту (10 мин)." : (error.message || "Неизвестная ошибка при импорте");
        if (typeof showToast === "function") showToast(msg, "danger");
    })
    .finally(function () {
        clearTimeout(timeoutId);
        if (unlockInFinally && typeof unlockUi === "function") unlockUi();
    });
}

function changeTab(idToShow, idToHide) {
    elemToShow = $(idToShow);
    elemToHide = $(idToHide);
    elemToHide.hide();
    elemToShow.show();

    $('#tool_library_table').bootstrapTable('refreshOptions', {'height': 100});
    $('#group_library_table').bootstrapTable('refreshOptions', {'height': 100});
    $('#tool_library_table').bootstrapTable('refreshOptions', {'height': $("#tool_library_div").height()});
    $('#group_library_table').bootstrapTable('refreshOptions', {'height': $("#group_library_div").height()});
}

// Делаем функцию доступной глобально
window.changeTab = changeTab;