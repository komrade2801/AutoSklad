# frontend/setting_router.py
from fastapi import APIRouter, BackgroundTasks
from starlette.responses import HTMLResponse
from Core.default import run_setup_process, progress_data, progress_lock

setting_router = APIRouter(tags=["setting"])

@setting_router.get("/progress")
async def get_progress():
    with progress_lock:
        return {
            "status": progress_data["status"],
            "stage": progress_data["current_stage"],
            "messages": progress_data["messages"][-5:],
            "percentage": progress_data["percentage"]
        }


@setting_router.post("/start")
async def start_setup(background_tasks: BackgroundTasks):
    with progress_lock:
        if progress_data["status"] == "in_progress":
            return {"error": "Operation already in progress"}

        # Сброс прогресса
        progress_data.update({
            "status": "in_progress",
            "messages": [],
            "current_stage": "",
            "percentage": 0
        })

        background_tasks.add_task(run_setup_process)
        return {"message": "Database setup started"}


@setting_router.get("/get_interface", response_class=HTMLResponse)
async def get_interface():
    return """
    <html>
    <head>
        <title>DB Setup Progress</title>
        <style>
            .container { width: 80%; margin: 50px auto; }
            .progress-bar { 
                height: 30px; 
                background: #eee;
                border-radius: 15px;
                overflow: hidden;
                position: relative;
            }
            .progress-fill {
                height: 100%;
                background: #4CAF50;
                transition: width 0.3s ease;
            }
            .progress-text {
                margin: 10px 0;
                text-align: center;
            }
            .messages {
                height: 150px;
                overflow-y: auto;
                border: 1px solid #ddd;
                padding: 10px;
                margin: 20px 0;
            }
            button {
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:disabled {
                background: #cccccc;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Database Setup Progress</h1>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">0%</div>
            <div class="messages" id="messages"></div>
            <button onclick="startSetup()" id="startButton">Start Setup</button>
        </div>
        <script>
            let isProcessing = false;

            async function updateProgress() {
                const response = await fetch('/progress');
                const data = await response.json();

                // Update progress bar
                document.getElementById('progressFill').style.width = data.percentage + '%';
                document.getElementById('progressText').textContent = 
                    `${data.stage} (${data.percentage}%)`;

                // Update messages
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML = data.messages
                    .map(msg => `<div>${msg}</div>`)
                    .join('');

                // Auto-scroll messages
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                // Update button state
                const button = document.getElementById('startButton');
                if (data.status === 'in_progress') {
                    button.disabled = true;
                    button.textContent = 'Processing...';
                    setTimeout(updateProgress, 1000);
                } else {
                    button.disabled = false;
                    button.textContent = 'Start Setup';
                }
            }

            async function startSetup() {
                if (isProcessing) return;

                isProcessing = true;
                document.getElementById('startButton').disabled = true;

                try {
                    const response = await fetch('/start', {
                        method: 'POST'
                    });
                    const result = await response.json();

                    if (result.error) {
                        alert(result.error);
                    } else {
                        updateProgress();
                    }
                } catch (error) {
                    alert('Error starting setup: ' + error.message);
                } finally {
                    isProcessing = false;
                }
            }
        </script>
    </body>
    </html>
    """

