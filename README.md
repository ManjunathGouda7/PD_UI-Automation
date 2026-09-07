# GRL USB PD C2 (V-DPWR-EPR) UI Automation Framework

Enterprise-grade Page Object Model (POM) test automation framework for the **GRL-V-DPWR-EPR / USB Power Delivery and Type-C™ Test Software (v1.1.1.1)** running at `http://localhost:5003/v1.1.1.html`.

---

## 🚀 Key Highlights

- **Complete 8-Panel Coverage**:
  1. `Connection Setup`: Network scanning, IP assignment (`192.168.102.76`), Tester status.
  2. `Product Capability`: XML VIF loading, DUT roles (Provider Only / Consumer), cable selection.
  3. `Test Config`: 207 Automated Compliance Test cases, search filters, engineer metadata.
  4. `Results`: Waveform charts, Zoom, Pan, Markers, real-time Pass/Fail counters.
  5. `Report`: View Report, HTML & DUT data download.
  6. `Configure`: Controller Mode (UFP/Sink), VBUS, SENSE, CC1/CC2 channel control.
  7. `LoopBack`: Throughput monitor, data transfer testing.
  8. `Help`: Diagnostics & debug log generation.
- **Modern PyQt6 Desktop Runner**: Obsidian & Electric Amber theme with presets, worker controls, retry selector, and live search.
- **Reporting Engine**: Standalone Interactive HTML Dashboard with dark/light mode toggle + multi-sheet Excel reports.
- **CI/CD Ready**: Dockerfile, Docker Compose, and Jenkinsfile pipelines.

---

## 📂 Project Architecture

```
D:\Manju\PD-UI-Automation\
├── Configurations/
│   ├── pytest.ini                      # Pytest runner options & markers
│   └── .env.example                    # Environment configuration
├── jsons/
│   ├── Inputs.json                     # Hardware & API configurations
│   └── test_data.json                  # Centralized test parameters & profiles
├── Scripts/
│   ├── Data/                           # Test data managers
│   ├── Helpers/                        # Config, rotating logger, smart selector, locators
│   ├── Pages/                          # Page Object Models for all 8 panels
│   ├── TestCases/                      # Pytest test suites (test_01 to test_08)
│   ├── UI/                             # Modern PyQt6 GUI & HTML/Excel report generators
│   └── conftest.py                     # Playwright context, tracing, failure screenshots
├── MainGUI.py                          # Desktop GUI Runner Entrypoint
├── Dockerfile                          # Playwright container
├── docker-compose.yml                  # Containerized test runner + Allure service
├── Jenkinsfile                         # Declarative CI/CD pipeline
├── pyproject.toml                      # Ruff lint rules
└── requirements.txt                    # Python dependencies
```

---

## ⚡ Quick Start

### 1. Launch Desktop GUI Runner
```powershell
python MainGUI.py
```

### 2. Run Headless via CLI
```powershell
# Run smoke tests
pytest -c Configurations/pytest.ini Scripts/TestCases -m smoke

# Run full suite in parallel with retries
pytest -c Configurations/pytest.ini Scripts/TestCases -n 2 --reruns 1
```

### 3. Lint Code
```powershell
ruff check .
```
