# Copyright 2025 The Rilla Project Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law of a proprietary software is "available" for public use.
# See the License for the specific language governing permissions and
# limitations under the License.

# Copyright 2025 The Rilla Project Developers

import sys, json, traceback, os, shutil
from typing import Dict, List
from pathlib import Path
from PySide6.QtWidgets import ( QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox, QPushButton, QListWidget, QSplitter, QFileDialog, QListWidgetItem )
from PySide6.QtCore import Qt, QThread, QObject, Signal
from core.interfaces import AbstractSimulationEngine
from engines.pyltspice_engine import PyLTSpiceEngine
class Worker(QObject):
    finished = Signal()
    result = Signal(str) # Emits one JSON string
    progress = Signal(str)
    error = Signal(str)  # Add explicit error signal
    
    def __init__(self, model_info: Dict):
        super().__init__()
        # --- DIAGNOSTIC PRINT ---
        self.model_name = model_info.get('name', 'Unknown')
        self.is_cancelled = False  # Add cancellation support
        self.engine: AbstractSimulationEngine = PyLTSpiceEngine()
        self.model_info = model_info

    def cancel(self):
        """Allow external cancellation of the worker"""
        self.is_cancelled = True

    def run_simulation_task(self):
        try:
            if self.is_cancelled:
                return
                
            self.progress.emit(f"Running simulation for {self.model_info['name']}...")
            
            # Check for cancellation during long operations
            if self.is_cancelled:
                return
                
            json_result = self.engine.run_vth_simulation(model_info=self.model_info)
            
            if not self.is_cancelled:
                self.result.emit(json_result)
                
        except Exception as e:
            if not self.is_cancelled:
                error_message = f"Simulation failed for {self.model_name}: {str(e)}"
                print(f"[ERROR] {error_message}")
                error_data = {
                    "status": "error",
                    "model_name": self.model_info.get('name', 'Unknown'),
                    "error_message": str(e)
                }
                self.error.emit(json.dumps(error_data, indent=4))
        finally:
            self.finished.emit()

class RillaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Store active workers and threads to prevent garbage collection
        self.active_workers = []  # Keep references to prevent GC
        self.active_threads = []  # Keep references to prevent GC
        
        self.running_sims = 0
        self.comparison_results: List[Dict] = []
        
        self.user_models_dir = Path("user_models"); self.config_path = Path("src/models.json"); self.user_models_dir.mkdir(exist_ok=True)
        self.config_data = self.load_config()
        if not self.config_data: sys.exit(1)
        self.comparison_models: List[Dict] = []
        self.setWindowTitle("Rilla - MOSFET Characterization"); self.setGeometry(100, 100, 900, 700)
        self._create_menu_bar(); self.status_bar = self.statusBar(); self.status_bar.showMessage("Ready")
        main_splitter = QSplitter(Qt.Horizontal)
        config_panel = self._create_config_panel()
        self.results_panel = QWidget(); self.results_panel.setLayout(QVBoxLayout()); self.show_initial_message()
        main_splitter.addWidget(config_panel); main_splitter.addWidget(self.results_panel); main_splitter.setStretchFactor(1, 1)
        self.setCentralWidget(main_splitter)

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f: return json.load(f)
        except Exception as e: print(f"CRITICAL ERROR loading {self.config_path}: {e}"); return None
    def _create_menu_bar(self):
        menu_bar = self.menuBar(); file_menu = menu_bar.addMenu("&File")
        add_model_action = file_menu.addAction("Add Model Library..."); add_model_action.triggered.connect(self.on_add_model_library_clicked)
        file_menu.addSeparator(); exit_action = file_menu.addAction("Exit"); exit_action.triggered.connect(self.close)
        help_menu = menu_bar.addMenu("&Help"); about_action = help_menu.addAction("About Rilla")
        return menu_bar
    def _create_config_panel(self):
        config_widget = QWidget(); layout = QVBoxLayout(); comp_group = QGroupBox("1. Select Components"); comp_layout = QVBoxLayout()
        self.component_list_widget = QListWidget(); self.component_list_widget.setFixedHeight(80)
        self.model_library_selector = QComboBox(); self._refresh_model_library_dropdown()
        add_to_comparison_button = QPushButton("Add to Comparison"); add_to_comparison_button.clicked.connect(self.on_add_to_comparison_clicked)
        comp_layout.addWidget(QLabel("Component Library:")); comp_layout.addWidget(self.model_library_selector); comp_layout.addWidget(add_to_comparison_button)
        comp_layout.addSpacing(10); comp_layout.addWidget(QLabel("Components to Compare:")); comp_layout.addWidget(self.component_list_widget); comp_group.setLayout(comp_layout)
        test_group = QGroupBox("2. Select Test"); test_layout = QVBoxLayout(); self.test_list = QListWidget(); self.test_list.addItems(["Vgs Threshold"]); self.test_list.setCurrentRow(0)
        test_layout.addWidget(self.test_list); test_group.setLayout(test_layout); self.run_button = QPushButton("Run Comparison"); self.run_button.clicked.connect(self.on_run_comparison_clicked)
        layout.addWidget(comp_group); layout.addWidget(test_group); layout.addStretch(1); layout.addWidget(self.run_button); config_widget.setLayout(layout)
        return config_widget
    def _get_subckt_name_from_file(self, file_path: Path) -> str | None:
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if line.strip().lower().startswith('.subckt'): parts = line.strip().split();
                    if len(parts) > 1: return parts[1]
            return None
        except Exception as e: print(f"Could not read or parse {file_path}: {e}"); return None
    def on_add_model_library_clicked(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select SPICE Model Files", "", "SPICE Models (*.lib *.mod);;All Files (*)");
        if not file_paths: return
        added_models = 0
        for file_path_str in file_paths:
            file_path = Path(file_path_str); dest_path = self.user_models_dir / file_path.name
            try: shutil.copy(file_path, dest_path)
            except Exception as e: print(f"Error copying file {file_path.name}: {e}"); continue
            model_name = self._get_subckt_name_from_file(dest_path)
            if not model_name: model_name = file_path.stem
            absolute_path = os.path.abspath(dest_path); new_model_entry = {"name": model_name, "path": absolute_path}
            if not any(m['name'] == model_name for m in self.config_data['models']): self.config_data['models'].append(new_model_entry); added_models += 1
        if added_models > 0:
            try:
                with open(self.config_path, 'w') as f: json.dump(self.config_data, f, indent=4)
                self._refresh_model_library_dropdown(); self.status_bar.showMessage(f"Successfully added {added_models} new model(s) to library.")
            except Exception as e: print(f"Error saving updated config to {self.config_path}: {e}")
    def _refresh_model_library_dropdown(self):
        self.model_library_selector.clear(); model_names = [model['name'] for model in self.config_data.get('models', [])]; self.model_library_selector.addItems(model_names)
    def on_add_to_comparison_clicked(self):
        if len(self.comparison_models) >= 2: self.status_bar.showMessage("Cannot compare more than two models at a time."); return
        selected_model_name = self.model_library_selector.currentText()
        if any(m['name'] == selected_model_name for m in self.comparison_models): self.status_bar.showMessage(f"'{selected_model_name}' is already in the comparison list."); return
        model_info = next((m for m in self.config_data['models'] if m['name'] == selected_model_name), None)
        if model_info: self.comparison_models.append(model_info); self._update_comparison_list_widget()
    def _update_comparison_list_widget(self):
        self.component_list_widget.clear()
        for model in self.comparison_models:
            item = QListWidgetItem(self.component_list_widget); 
            item_widget = self._create_comparison_list_item_widget(model); 
            item.setSizeHint(item_widget.sizeHint())
            self.component_list_widget.addItem(item); 
            self.component_list_widget.setItemWidget(item, item_widget)
             # --- NEW: Dynamically update button text ---
        num_models = len(self.comparison_models)
        if num_models == 1:
            self.run_button.setText("Run Simulation")
        else:
            self.run_button.setText("Run Comparison")
        # --- END OF NEW ---
    def _create_comparison_list_item_widget(self, model_info):
        widget = QWidget(); layout = QHBoxLayout(); layout.setContentsMargins(5, 5, 5, 5); label = QLabel(model_info['name']); label.setToolTip(model_info['path'])
        remove_button = QPushButton("✖"); remove_button.setFixedSize(24, 24); remove_button.setToolTip("Remove from comparison")
        remove_button.clicked.connect(lambda: self.on_remove_from_comparison_clicked(model_info)); layout.addWidget(label); layout.addStretch(); layout.addWidget(remove_button)
        widget.setLayout(layout)
        return widget
    def on_remove_from_comparison_clicked(self, model_to_remove):
        self.comparison_models = [m for m in self.comparison_models if m['name'] != model_to_remove['name']]; self._update_comparison_list_widget()

    def mark_worker_finished(self, worker):
        """Remove finished worker from active list"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
            #print(f"[LIFECYCLE] Worker for {worker.model_name} removed from active list")

    def mark_thread_finished(self, thread):
        """Remove finished thread from active list"""
        if thread in self.active_threads:
            self.active_threads.remove(thread)
            #print(f"[LIFECYCLE] Thread removed from active list")

    def cleanup_finished_workers(self):
        """Clean up any workers/threads that are no longer running"""
        # Remove any threads that have finished
        original_count = len(self.active_threads)
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
        #if len(self.active_threads) < original_count:
            #print(f"[LIFECYCLE] Cleaned up {original_count - len(self.active_threads)} finished threads")

    def closeEvent(self, event):
        """Ensure clean shutdown when application is closed"""
        #print(f"[LIFECYCLE] Application closing. Active threads: {len(self.active_threads)}")
        
        # Cancel all workers first
        for worker in self.active_workers:
            worker.cancel()
        
        # Wait for all threads to finish before closing
        for i, thread in enumerate(self.active_threads):
            if thread.isRunning():
                #print(f"[LIFECYCLE] Waiting for thread {i+1} to finish...")
                thread.quit()
                if not thread.wait(5000):  # Wait up to 5 seconds
                    #print(f"[LIFECYCLE] Thread {i+1} did not finish gracefully, forcing termination")
                    thread.terminate()
                    thread.wait(1000)  # Wait 1 more second for termination
        
        # Clear references
        self.active_workers.clear()
        self.active_threads.clear()
        #print("[LIFECYCLE] All threads cleaned up, application closing")
        
        super().closeEvent(event)

    def on_run_comparison_clicked(self):
        num_models = len(self.comparison_models)

        if num_models == 0:
            self.status_bar.showMessage("Please add at least one model to the list to run a simulation.")
            return
        
        if num_models > 2:
            # This is a safeguard, our UI should prevent this.
            self.status_bar.showMessage("Cannot simulate more than two models at a time.")
            return
            
        self.run_button.setEnabled(False); self.clear_results_panel();
        
        self.running_sims = len(self.comparison_models)
        self.comparison_results = []
        self.active_threads.clear(); self.active_workers.clear()
        
        # Update the button text based on the action
        if num_models == 1:
            self.run_button.setText("Run Simulation")
            self.status_bar.showMessage(f"Starting simulation for 1 model...")
        else:
            self.run_button.setText("Run Comparison")
            self.status_bar.showMessage(f"Starting {self.running_sims} simulations for comparison...")

        for model_info in self.comparison_models:
            thread = QThread(); worker = Worker(model_info=model_info); worker.moveToThread(thread)
            worker.progress.connect(self.update_status); worker.result.connect(self.handle_worker_result)
            worker.finished.connect(thread.quit); worker.finished.connect(worker.deleteLater); thread.finished.connect(thread.deleteLater)
            thread.started.connect(worker.run_simulation_task);
            self.active_threads.append(thread); self.active_workers.append(worker); thread.start()

    def handle_worker_error(self, error_json_str: str):
        """Handle worker errors"""
        self.running_sims -= 1
        try:
            error_data = json.loads(error_json_str)
            self.comparison_results.append(error_data)
            model_name = error_data.get('model_name', 'Unknown')
            self.status_bar.showMessage(f"Simulation failed for {model_name}. {self.running_sims} remaining...")
        except json.JSONDecodeError:
            print(f"Received invalid error JSON. {self.running_sims} simulations remaining.")
        
        if self.running_sims == 0:
            self.status_bar.showMessage("All simulations complete.")
            print("--- Comparison finished with errors. Final results: ---")
            print(json.dumps(self.comparison_results, indent=2))
            self.display_final_summary(self.comparison_results)
            self.run_button.setEnabled(True)
            self.cleanup_finished_workers()

    def handle_worker_result(self, json_result_str: str):
        self.running_sims -= 1
        try:
            result_data = json.loads(json_result_str)
            self.comparison_results.append(result_data)
            model_name = result_data.get('model_name', 'Unknown')
            self.status_bar.showMessage(f"Finished simulation for {model_name}. {self.running_sims} remaining...")
        except json.JSONDecodeError:
            print(f"Received invalid JSON. {self.running_sims} simulations remaining.")
        
        if self.running_sims == 0:
            self.status_bar.showMessage("All simulations complete.")
            print("--- Comparison finished. Final results: ---")
            self.display_final_summary(self.comparison_results)
            self.run_button.setEnabled(True)
            
            # Clean up finished workers/threads
            self.cleanup_finished_workers()

    def display_final_summary(self, results_list):
        self.clear_results_panel()
        summary_text = "Comparison complete.\n\n"
        for result in results_list:
            if result.get('status') == 'success':
                model = result.get('model_name')
                vth = result.get('results', {}).get('vth_at_25c_volts', float('nan'))
                summary_text += f"  - {model}: Vth = {vth:.4f} V\n"
            else:
                model = result.get('model_name', 'Unknown')
                error_msg = result.get('error_message', 'Unknown error')
                summary_text += f"  - {model}: FAILED - {error_msg}\n"
        summary_label = QLabel(summary_text)
        summary_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_panel.layout().addWidget(summary_label)
    def update_status(self, message): self.status_bar.showMessage(message)
    def clear_results_panel(self):
        for i in reversed(range(self.results_panel.layout().count())): 
            widget = self.results_panel.layout().itemAt(i).widget()
            if widget is not None: widget.setParent(None)
    def show_initial_message(self):
        self.clear_results_panel()
        initial_message = QLabel("Select two components to compare, then press 'Run Comparison' to view results.")
        initial_message.setAlignment(Qt.AlignCenter); self.results_panel.layout().addWidget(initial_message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RillaMainWindow()
    window.show()
    sys.exit(app.exec())