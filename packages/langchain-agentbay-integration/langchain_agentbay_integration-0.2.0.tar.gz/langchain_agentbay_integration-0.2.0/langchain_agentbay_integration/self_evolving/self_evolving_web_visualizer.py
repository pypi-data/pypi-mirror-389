import os
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.parse
from typing import Dict, Any, List, Optional


class TrainingDataHandler:
    """Handles loading and processing of training data."""
    
    def __init__(self, training_dir=None):
        self.training_dir = training_dir
        self.training_data = {}
        self.epochs = []
        if training_dir:
            self.load_training_data(training_dir)
    
    def load_training_data(self, directory):
        """Load training data from the selected directory."""
        training_path = Path(directory)
        if not training_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")
            
        self.training_data = {}
        self.epochs = []
        
        # Load epoch data
        for epoch_dir in sorted(training_path.glob("epoch_*")):
            if epoch_dir.is_dir():
                epoch_data = {}
                epoch_num = int(epoch_dir.name.split("_")[1])
                
                # Load training plan
                plan_file = epoch_dir / "training_plan.json"
                if plan_file.exists():
                    with open(plan_file, "r", encoding="utf-8") as f:
                        epoch_data["plan"] = json.load(f)
                        
                # Load execution result
                execution_file = epoch_dir / "execution_result.json"
                if execution_file.exists():
                    with open(execution_file, "r", encoding="utf-8") as f:
                        epoch_data["execution"] = json.load(f)
                        
                # Load training result
                result_file = epoch_dir / "training_result.txt"
                if result_file.exists():
                    with open(result_file, "r", encoding="utf-8") as f:
                        epoch_data["result"] = json.load(f)
                        
                self.training_data[epoch_num] = epoch_data
                self.epochs.append(epoch_num)
                
        # Load final result
        final_file = training_path / "final_training_result.txt"
        if final_file.exists():
            with open(final_file, "r", encoding="utf-8") as f:
                self.training_data["final"] = json.load(f)
                
        self.epochs.sort()
    
    def get_epoch_data(self, epoch):
        """Get data for a specific epoch."""
        return self.training_data.get(epoch, {})
    
    def get_final_data(self):
        """Get final training data."""
        return self.training_data.get("final", {})
    
    def format_plan(self, plan_text):
        """Format plan text with line numbers."""
        if not plan_text:
            return "No plan data available"
        lines = plan_text.split('\n')
        formatted_lines = [f"{i+1:2d}. {line}" for i, line in enumerate(lines) if line.strip()]
        return '\n'.join(formatted_lines)
    
    def format_json(self, data, indent=0):
        """Format JSON data for display."""
        lines = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)) and value:
                    lines.append(" " * indent + f"{key}:")
                    lines.append(self.format_json(value, indent + 2))
                else:
                    lines.append(" " * indent + f"{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)) and item:
                    lines.append(" " * indent + f"[{i}]:")
                    lines.append(self.format_json(item, indent + 2))
                else:
                    lines.append(" " * indent + f"[{i}]: {item}")
        else:
            lines.append(" " * indent + str(data))
        return "\n".join(lines)


class VisualizationHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the visualization web server."""
    
    training_handler = None
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/" or path == "/index.html":
            self.serve_main_page()
        elif path == "/data":
            self.serve_data()
        elif path == "/epoch":
            self.serve_epoch_data()
        elif path == "/final":
            self.serve_final_data()
        elif path == "/style.css":
            self.serve_css()
        else:
            self.serve_404()
    
    def serve_main_page(self):
        """Serve the main HTML page."""
        html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Self-Evolving Agent Training Visualizer</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Self-Evolving Agent Training Visualizer</h1>
        </header>
        
        <main>
            <div class="controls">
                <div class="epoch-selector">
                    <label for="epoch-select">Epoch:</label>
                    <select id="epoch-select"></select>
                    <button id="prev-btn">Previous</button>
                    <button id="next-btn">Next</button>
                </div>
            </div>
            
            <div class="tabs">
                <button class="tab-button active" data-tab="plan">Training Plan</button>
                <button class="tab-button" data-tab="execution">Execution Result</button>
                <button class="tab-button" data-tab="result">Training Result</button>
                <button class="tab-button" data-tab="final">Final Result</button>
            </div>
            
            <div class="tab-content">
                <div id="plan-tab" class="tab-pane active">
                    <h2>Training Plan</h2>
                    <pre id="plan-content" class="content-box">Select an epoch to view training plan</pre>
                </div>
                
                <div id="execution-tab" class="tab-pane">
                    <h2>Execution Result</h2>
                    <div class="summary">
                        <p><strong>Player ID:</strong> <span id="execution-player-id">N/A</span></p>
                        <p><strong>Success:</strong> <span id="execution-success">N/A</span></p>
                        <p><strong>Task Description:</strong></p>
                        <pre id="execution-task" class="content-box">N/A</pre>
                    </div>
                    <h3>Execution Details</h3>
                    <pre id="execution-content" class="content-box">No execution data available</pre>
                </div>
                
                <div id="result-tab" class="tab-pane">
                    <h2>Training Result</h2>
                    <div class="summary">
                        <p><strong>Score:</strong> <span id="result-score">N/A</span></p>
                        <p><strong>Feedback:</strong></p>
                        <pre id="result-feedback" class="content-box">N/A</pre>
                    </div>
                    
                    <div class="comparison">
                        <h3>Plan Comparison</h3>
                        <div class="plan-comparison">
                            <div class="plan-box">
                                <h4>Previous Plan</h4>
                                <pre id="prev-plan" class="content-box">No previous plan</pre>
                            </div>
                            <div class="plan-box">
                                <h4>Current Plan</h4>
                                <pre id="current-plan" class="content-box">No current plan</pre>
                            </div>
                        </div>
                    </div>
                    
                    <h3>Result Details</h3>
                    <pre id="result-content" class="content-box">No training result data available</pre>
                </div>
                
                <div id="final-tab" class="tab-pane">
                    <h2>Final Result</h2>
                    <div class="summary">
                        <p><strong>Total Epochs:</strong> <span id="final-epochs">N/A</span></p>
                        <p><strong>Best Score:</strong> <span id="final-score">N/A</span></p>
                        <p><strong>Best Player ID:</strong> <span id="final-player-id">N/A</span></p>
                        <p><strong>Best Plan:</strong></p>
                        <pre id="best-plan" class="content-box">N/A</pre>
                    </div>
                    <h3>Final Details</h3>
                    <pre id="final-content" class="content-box">No final data available</pre>
                </div>
            </div>
        </main>
    </div>
    
    <script>
        let epochs = [];
        let currentEpochIndex = 0;
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadEpochs();
            
            // Tab switching
            document.querySelectorAll('.tab-button').forEach(button => {
                button.addEventListener('click', () => {
                    const tabId = button.getAttribute('data-tab');
                    switchTab(tabId);
                });
            });
            
            // Epoch selection
            document.getElementById('epoch-select').addEventListener('change', function() {
                const selectedIndex = this.selectedIndex;
                if (selectedIndex >= 0) {
                    currentEpochIndex = selectedIndex;
                    loadEpochData(epochs[currentEpochIndex]);
                }
            });
            
            // Navigation buttons
            document.getElementById('prev-btn').addEventListener('click', function() {
                if (currentEpochIndex > 0) {
                    currentEpochIndex--;
                    document.getElementById('epoch-select').selectedIndex = currentEpochIndex;
                    loadEpochData(epochs[currentEpochIndex]);
                }
            });
            
            document.getElementById('next-btn').addEventListener('click', function() {
                if (currentEpochIndex < epochs.length - 1) {
                    currentEpochIndex++;
                    document.getElementById('epoch-select').selectedIndex = currentEpochIndex;
                    loadEpochData(epochs[currentEpochIndex]);
                }
            });
        });
        
        function loadEpochs() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    epochs = data.epochs;
                    const select = document.getElementById('epoch-select');
                    select.innerHTML = '';
                    
                    epochs.forEach((epoch, index) => {
                        const option = document.createElement('option');
                        option.value = epoch;
                        option.textContent = `Epoch ${epoch}`;
                        select.appendChild(option);
                    });
                    
                    if (epochs.length > 0) {
                        currentEpochIndex = 0;
                        select.selectedIndex = 0;
                        loadEpochData(epochs[0]);
                    }
                })
                .catch(error => {
                    console.error('Error loading epochs:', error);
                });
        }
        
        function loadEpochData(epoch) {
            fetch(`/epoch?epoch=${epoch}`)
                .then(response => response.json())
                .then(data => {
                    // Update plan tab
                    document.getElementById('plan-content').textContent = data.plan || 'No plan data available';
                    
                    // Update execution tab
                    if (data.execution) {
                        document.getElementById('execution-player-id').textContent = data.execution.player_id || 'N/A';
                        document.getElementById('execution-success').textContent = data.execution.success || 'N/A';
                        document.getElementById('execution-task').textContent = data.execution.task_description || 'N/A';
                        document.getElementById('execution-content').textContent = data.execution.full_data || 'No execution data';
                    } else {
                        document.getElementById('execution-player-id').textContent = 'N/A';
                        document.getElementById('execution-success').textContent = 'N/A';
                        document.getElementById('execution-task').textContent = 'N/A';
                        document.getElementById('execution-content').textContent = 'No execution data available';
                    }
                    
                    // Update result tab
                    if (data.result) {
                        document.getElementById('result-score').textContent = data.result.score || 'N/A';
                        document.getElementById('result-feedback').textContent = data.result.feedback || 'N/A';
                        document.getElementById('current-plan').textContent = data.result.plan || 'No current plan';
                        
                        // Get previous plan if available
                        if (currentEpochIndex > 0) {
                            fetch(`/epoch?epoch=${epochs[currentEpochIndex - 1]}`)
                                .then(response => response.json())
                                .then(prevData => {
                                    document.getElementById('prev-plan').textContent = prevData.result ? (prevData.result.plan || 'No previous plan') : 'No previous plan';
                                })
                                .catch(error => {
                                    document.getElementById('prev-plan').textContent = 'Error loading previous plan';
                                });
                        } else {
                            document.getElementById('prev-plan').textContent = 'No previous plan (first epoch)';
                        }
                        
                        document.getElementById('result-content').textContent = data.result.full_data || 'No result data';
                    } else {
                        document.getElementById('result-score').textContent = 'N/A';
                        document.getElementById('result-feedback').textContent = 'N/A';
                        document.getElementById('current-plan').textContent = 'No current plan';
                        document.getElementById('prev-plan').textContent = 'No previous plan';
                        document.getElementById('result-content').textContent = 'No training result data available';
                    }
                })
                .catch(error => {
                    console.error('Error loading epoch data:', error);
                });
                
            // Load final data
            fetch('/final')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('final-epochs').textContent = data.total_epochs || 'N/A';
                    document.getElementById('final-score').textContent = data.best_score || 'N/A';
                    document.getElementById('final-player-id').textContent = data.best_player_id || 'N/A';
                    document.getElementById('best-plan').textContent = data.best_plan || 'N/A';
                    document.getElementById('final-content').textContent = data.full_data || 'No final data';
                })
                .catch(error => {
                    console.error('Error loading final data:', error);
                });
        }
        
        function switchTab(tabId) {
            // Hide all tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(button => {
                button.classList.remove('active');
            });
            
            // Show selected tab pane
            document.getElementById(tabId + '-tab').classList.add('active');
            
            // Add active class to selected button
            document.querySelector(`.tab-button[data-tab="${tabId}"]`).classList.add('active');
        }
    </script>
</body>
</html>
'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_css(self):
        """Serve the CSS stylesheet."""
        css_content = '''
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background-color: #333;
    color: white;
    padding: 1rem;
    margin-bottom: 20px;
    border-radius: 5px;
}

header h1 {
    margin: 0;
}

.controls {
    background-color: white;
    padding: 15px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.epoch-selector {
    display: flex;
    align-items: center;
    gap: 10px;
}

.epoch-selector label {
    font-weight: bold;
}

.epoch-selector select {
    padding: 5px;
    border-radius: 3px;
    border: 1px solid #ddd;
}

.epoch-selector button {
    padding: 5px 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
}

.epoch-selector button:hover {
    background-color: #0056b3;
}

.tabs {
    display: flex;
    gap: 5px;
    margin-bottom: 20px;
}

.tab-button {
    padding: 10px 20px;
    background-color: #e9ecef;
    border: none;
    border-radius: 5px 5px 0 0;
    cursor: pointer;
    font-weight: bold;
}

.tab-button.active {
    background-color: #007bff;
    color: white;
}

.tab-button:hover:not(.active) {
    background-color: #d0d0d0;
}

.tab-content {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    overflow: hidden;
}

.tab-pane {
    display: none;
    padding: 20px;
}

.tab-pane.active {
    display: block;
}

.tab-pane h2 {
    margin-top: 0;
    color: #333;
    border-bottom: 2px solid #007bff;
    padding-bottom: 10px;
}

.tab-pane h3 {
    color: #555;
    margin-top: 20px;
}

.summary {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.summary p {
    margin: 5px 0;
}

.comparison {
    margin: 20px 0;
}

.plan-comparison {
    display: flex;
    gap: 20px;
}

.plan-box {
    flex: 1;
}

.plan-box h4 {
    margin-top: 0;
    color: #555;
}

.content-box {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 15px;
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
}

pre.content-box {
    font-family: 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.4;
}

@media (max-width: 768px) {
    .plan-comparison {
        flex-direction: column;
    }
    
    .tabs {
        flex-wrap: wrap;
    }
    
    .tab-button {
        flex: 1 0 auto;
        text-align: center;
    }
}
'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        self.wfile.write(css_content.encode('utf-8'))
    
    def serve_data(self):
        """Serve basic training data info."""
        if not self.training_handler:
            self.send_error(500, "Training handler not initialized")
            return
            
        response_data = {
            "epochs": self.training_handler.epochs
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, indent=2).encode('utf-8'))
    
    def serve_epoch_data(self):
        """Serve data for a specific epoch."""
        if not self.training_handler:
            self.send_error(500, "Training handler not initialized")
            return
            
        # Parse query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        epoch = int(query_params.get('epoch', [0])[0])
        
        epoch_data = self.training_handler.get_epoch_data(epoch)
        
        # Format the data for web display
        response_data = {
            "epoch": epoch
        }
        
        # Process plan data
        if "plan" in epoch_data:
            plan_text = epoch_data["plan"].get("plan", "")
            response_data["plan"] = self.training_handler.format_plan(plan_text)
        else:
            response_data["plan"] = None
            
        # Process execution data
        if "execution" in epoch_data:
            execution = epoch_data["execution"]
            response_data["execution"] = {
                "player_id": execution.get("player_id", "N/A"),
                "success": execution.get("success", "N/A"),
                "task_description": execution.get("task_description", "N/A"),
                "full_data": self.training_handler.format_json(execution)
            }
        else:
            response_data["execution"] = None
            
        # Process result data
        if "result" in epoch_data:
            result = epoch_data["result"]
            response_data["result"] = {
                "score": result.get("score", "N/A"),
                "feedback": result.get("feedback", "N/A"),
                "plan": self.training_handler.format_plan(result.get("plan", "")),
                "full_data": self.training_handler.format_json(result)
            }
        else:
            response_data["result"] = None
            
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, indent=2).encode('utf-8'))
    
    def serve_final_data(self):
        """Serve final training data."""
        if not self.training_handler:
            self.send_error(500, "Training handler not initialized")
            return
            
        final_data = self.training_handler.get_final_data()
        
        # Format the data for web display
        response_data = {
            "total_epochs": final_data.get("total_epochs", "N/A"),
            "best_score": final_data.get("best_score", "N/A"),
            "best_player_id": final_data.get("best_player_id", "N/A"),
            "best_plan": self.training_handler.format_plan(final_data.get("best_plan", "")),
            "full_data": self.training_handler.format_json(final_data)
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, indent=2).encode('utf-8'))
    
    def serve_404(self):
        """Serve a 404 page."""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>404 - Page Not Found</h1>')


class WebVisualizer:
    """Web-based visualizer for self-evolving agent training results."""
    
    def __init__(self, training_dir, port=8000):
        self.training_dir = training_dir
        self.port = port
        self.httpd = None
        
    def start(self):
        """Start the web server."""
        # Initialize the training handler
        VisualizationHandler.training_handler = TrainingDataHandler(self.training_dir)
        
        # Create and start the server
        self.httpd = HTTPServer(('localhost', self.port), VisualizationHandler)
        print(f"Starting web visualizer on http://localhost:{self.port}")
        print(f"Training data directory: {self.training_dir}")
        print("Press Ctrl+C to stop the server")
        
        try:
            webbrowser.open(f'http://localhost:{self.port}')
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            self.httpd.shutdown()


def main(training_dir=None, port=8000):
    """Run the web-based training visualizer."""
    if training_dir is None:
        # Try to find a default training directory
        possible_dirs = [
            "./self_evolving_training_results",
            "./training_results",
            "./results"
        ]
        
        for dir_path in possible_dirs:
            if Path(dir_path).exists():
                training_dir = dir_path
                break
        
        if training_dir is None:
            print("Please specify a training directory with --dir PATH")
            return
    
    try:
        visualizer = WebVisualizer(training_dir, port)
        visualizer.start()
    except Exception as e:
        print(f"Error starting visualizer: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Web-based visualizer for self-evolving agent training results")
    parser.add_argument("--dir", help="Training directory path")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the web server on (default: 8000)")
    
    args = parser.parse_args()
    main(args.dir, args.port)