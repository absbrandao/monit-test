from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
import requests
import time
import threading

app = FastAPI()

# Variável global para armazenar os dados de monitoramento
monitoring_data = []
monitoring_active = True

def monitor_connection():
    global monitoring_active
    start_time = time.time()
    while time.time() - start_time < 7200:  # 2 horas
        if not monitoring_active:
            break
        start_request = time.time()
        try:
            response = requests.get("https://www.uol.com.br", timeout=5)
            end_request = time.time()
            monitoring_data.append({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "status": "success" if response.status_code == 200 else "failure",
                "status_code": response.status_code,
                "response_time": round(end_request - start_request, 3)
            })
        except requests.RequestException:
            monitoring_data.append({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "status": "failure",
                "status_code": None,
                "response_time": None
            })
        time.sleep(5)
    monitoring_active = False

@app.get("/start-monitoring")
def start_monitoring(background_tasks: BackgroundTasks):
    global monitoring_active
    monitoring_active = True
    background_tasks.add_task(monitor_connection)
    return {"message": "Monitoramento iniciado."}

@app.get("/stop-monitoring")
def stop_monitoring():
    global monitoring_active
    monitoring_active = False
    return {"message": "Monitoramento parado."}

@app.get("/metrics")
def get_metrics():
    return monitoring_data

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monitoramento de Conexão UOL</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }
            h1 { color: #333; }
            button { margin: 10px; padding: 10px; border: none; cursor: pointer; }
            table { width: 80%; margin: auto; border-collapse: collapse; }
            th, td { padding: 10px; border: 1px solid black; }
            .success { background-color: #c8e6c9; }
            .failure { background-color: #ffcdd2; }
        </style>
        <script>
            async function fetchMetrics() {
                const response = await fetch('/metrics');
                const data = await response.json();
                let tableContent = '<tr><th>Timestamp</th><th>Status</th><th>Status Code</th><th>Response Time (s)</th></tr>';
                let times = [], responseTimes = [];
                data.slice(-20).forEach(entry => {
                    let rowClass = entry.status === "success" ? "success" : "failure";
                    tableContent += `<tr class="${rowClass}">
                        <td>${entry.timestamp}</td>
                        <td>${entry.status}</td>
                        <td>${entry.status_code || 'N/A'}</td>
                        <td>${entry.response_time || 'N/A'}</td>
                    </tr>`;
                    times.push(entry.timestamp);
                    responseTimes.push(entry.response_time || 0);
                });
                document.getElementById('metricsTable').innerHTML = tableContent;
                updateChart(times, responseTimes);
            }

            function updateChart(labels, data) {
                let ctx = document.getElementById('responseTimeChart').getContext('2d');
                if (window.responseChart) window.responseChart.destroy();
                window.responseChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Response Time (s)',
                            data: data,
                            borderColor: 'blue',
                            fill: false
                        }]
                    }
                });
            }

            setInterval(fetchMetrics, 5000);
        </script>
    </head>
    <body onload="fetchMetrics()">
        <h1>Monitoramento de Conexão UOL</h1>
        <button style="background-color: #4CAF50; color: white;" onclick="fetch('/start-monitoring')">Iniciar Monitoramento</button>
        <button style="background-color: #f44336; color: white;" onclick="fetch('/stop-monitoring')">Parar Monitoramento</button>
        <table id="metricsTable"></table>
        <canvas id="responseTimeChart" width="400" height="200"></canvas>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
