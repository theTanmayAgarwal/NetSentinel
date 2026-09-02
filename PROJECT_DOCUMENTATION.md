# AI-Driven Multi-Vendor Network Security Compliance Auditor (SIH26155)
## Complete Technical Documentation, Architecture, & Feature Specification

> **Tagline & Mission:** *Understand once. Normalize once. Audit every vendor.*

---

## 1. Executive Summary & Problem Statement Alignment

### Problem Statement Details
- **Problem Statement ID:** SIH26155
- **Project Title:** AI-Driven Multi-Vendor Network Security Compliance Auditor
- **Competition Target:** Smart India Hackathon (SIH) Internal Evaluation & Final Round Presentation

### Core Objective & Value Proposition
Enterprise network infrastructures consist of heterogeneous security hardware from vendors like **Cisco**, **Juniper**, and **Fortinet**, each utilizing completely different configuration syntaxes. Existing auditing tools rely on brittle, hardcoded regular expressions that break when encountering novel commands, or rely recklessly on LLMs to make compliance decisions.

Our solution introduces a **vendor-agnostic, multi-framework security auditor** with a deterministic compliance engine paired with an **Interactive Semantic Learning Engine**. 

```
Multi-Vendor Config (Cisco / Juniper / Fortinet / Unknown)
        ↓
Deterministic Vendor Detection (Signature Fingerprints)
        ↓
Deterministic Syntax Parsing (Regex Parsers)
        ↓
Vendor-Neutral Security Normalization (Common Fact JSON Model)
        ↓
Deterministic Compliance Engine (YAML Baseline Rules → PASS / FAIL / WARNING / CRITICAL)
        ↓
Multi-Framework Cross-Walk (CIS v1.0, NIST SP 800-53, DISA STIG, ISO/IEC 27001)
        ↓
Deterministic CLI Remediation & Post-Remediation Prediction Delta
        ↓
Human-in-the-Loop Semantic Learning Center (Few-Shot Embeddings + FAISS/NumPy Vector Store)
        ↓
Multi-Format Audit Report Exporter (ReportLab PDF, CSV, JSON)
```

---

## 2. Complete Technology Stack

### A. Frontend Architecture
- **Framework:** React 18 with Vite 5.
- **Language:** TypeScript 5.6.
- **Styling & UI Theme:** Tailwind CSS 3.4 featuring a custom **SOC Dark Theme** with glassmorphism panels, glow accents, and responsive layouts.
- **Iconography:** Lucide React icons.
- **Data Visualization:** Recharts (Interactive bar charts and pie charts for compliance distributions).
- **HTTP Client:** Axios with typed API service wrappers.

### B. Backend Architecture
- **Runtime & Framework:** Python 3.13 + FastAPI 0.115 + Uvicorn server.
- **Data Validation & Schemas:** Pydantic v2 typed request/response models.
- **Rule Parser Engine:** PyYAML for parsing rule definitions.
- **PDF Compilation Engine:** ReportLab 4.2.

### C. Artificial Intelligence & Vector Learning Stack
- **Embedding Backend:** `sentence-transformers` (`all-MiniLM-L6-v2`) generating unit-normalized 384-dimensional dense vectors.
- **Offline Fallback Embedder:** Deterministic n-gram feature hashing embedder ensuring 100% functionality without internet access.
- **Vector Store:** Local NumPy dot-product / FAISS cosine similarity vector search over stored exemplars.

### D. Persistence & Audit Logging
- **Embedded Database:** SQLite (`data/app.db`) managed via a clean, ORM-free **Repository Pattern** (`backend/app/persistence/repository.py`).
- **Tamper-Evident Audit Logging:** Hash-chained SHA-256 audit log (`audit_log` table) recording every audit execution, exemplar teaching event, and approval action.

### E. Verification & Automated Testing
- **Test Suite:** Pytest framework with **59 automated unit & integration tests** covering parsers, detection, compliance rules, remediation validation, persistence, vector store, and API endpoints.

---

## 3. Multi-Vendor Configuration Dataset Corpus

Our project includes a sanitized dataset of real-world enterprise configuration files in `sample_configs/`:

### A. Cisco IOS & ASA Datasets
- **`sample_configs/cisco/rtr-edge-01.cfg`**: Edge router snippet (Telnet enabled, SSH v2 enabled, HTTP enabled, logging disabled).
- **`sample_configs/cisco/cisco_ios_enterprise_border.cfg`**: Enterprise Border Router running IOS 15.6 with AAA authentication, SSH v2 enforcement, extended WAN ACLs, remote Syslog, and NTP.
- **`sample_configs/cisco/cisco_asa_datacenter.cfg`**: ASA 5555 Next-Gen Firewall running ASA 9.8 with management interface security, SSH timeouts, and console restrictions.

### B. Juniper JunOS Datasets
- **`sample_configs/juniper/srx-br-02.conf`**: Branch SRX security gateway (SSH enabled, Telnet enabled, HTTP enabled, Syslog notice, idle timeout 10).
- **`sample_configs/juniper/juniper_srx_branch.conf`**: Enterprise SRX340 firewall running JunOS 19.4 with `set system` hierarchy, root password hashes, login class idle timeouts, SSH rate limiting, and security zones.

### C. Fortinet FortiGate Datasets
- **`sample_configs/fortinet/fgt-dc-03.conf`**: FortiGate snippet (`config system global`, `set admin-sport 443`, `set admin-ssh-port 22`, `set admin-scp disable`).
- **`sample_configs/fortinet/fortigate_500e_enterprise.conf`**: FortiGate 500E Next-Gen Firewall running FortiOS 6.4 with custom management ports (`admin-sport 8443`, `admin-ssh-port 2222`), console timeouts, syslog accounting, and NTP.

### D. Unknown & Synthetic Evaluation Datasets
- **`sample_configs/unknown/other-device-01.cfg`**: Synthetic novel command lines (`set xyz secure-admin-timeout 300`) designed to test unknown command detection and few-shot semantic generalization.
- **Held-Out Test Pairs (`backend/app/training/tgr.py`)**: Unseen command variants used to empirically calculate the **Teaching Generalization Rate (TGR)**.

---

## 4. Multi-Framework Compliance Engine & Security Benchmarks

### A. Core Benchmark Baseline
The compliance engine evaluates configurations against a baseline set of 20 high-value security controls defined in `backend/app/compliance/rules/cis_network_v1.yaml`.

### B. Multi-Framework Cross-Walk (Harmonization)
A single technical security check evaluates a condition once, and automatically tags the finding across 4 major global compliance standards:

| Control Title | Active CIS Benchmark | NIST SP 800-53 Rev. 5 | DISA STIG | ISO/IEC 27001:2022 |
| :--- | :--- | :--- | :--- | :--- |
| **Telnet Disabled** | `NET-01` | NIST SP 800-53 `AC-17` | DISA STIG `NET0400` | ISO/IEC 27001 `A.13.1` |
| **SSH Enabled** | `NET-02` | NIST SP 800-53 `IA-2` | DISA STIG `NET0405` | ISO/IEC 27001 `A.9.4` |
| **SSH v2 Enforced** | `NET-03` | NIST SP 800-53 `SC-8` | DISA STIG `NET0406` | ISO/IEC 27001 `A.14.1` |
| **HTTP Disabled** | `NET-04` | NIST SP 800-53 `AC-17` | DISA STIG `NET0410` | ISO/IEC 27001 `A.12.1` |
| **Default SNMP** | `NET-05` | NIST SP 800-53 `IA-5` | DISA STIG `NET0600` | ISO/IEC 27001 `A.9.2` |
| **AAA Enabled** | `NET-06` | NIST SP 800-53 `AC-2` | DISA STIG `NET0100` | ISO/IEC 27001 `A.9.1` |
| **Enable Secret** | `NET-07` | NIST SP 800-53 `IA-5` | DISA STIG `NET0800` | ISO/IEC 27001 `A.9.2` |
| **Password Encryption** | `NET-08` | NIST SP 800-53 `IA-5` | DISA STIG `NET0805` | ISO/IEC 27001 `A.9.4` |
| **Weak Passwords** | `NET-09` | NIST SP 800-53 `IA-5` | DISA STIG `NET0810` | ISO/IEC 27001 `A.9.4` |
| **Min Password Length**| `NET-10` | NIST SP 800-53 `IA-5(1)` | DISA STIG `NET0815` | ISO/IEC 27001 `A.9.4` |
| **Idle Timeout** | `NET-11` | NIST SP 800-53 `AC-12` | DISA STIG `NET0500` | ISO/IEC 27001 `A.11.2` |
| **Login Banner** | `NET-12` | NIST SP 800-53 `AC-8` | DISA STIG `NET0300` | ISO/IEC 27001 `A.13.2` |
| **Remote Syslog** | `NET-13` | NIST SP 800-53 `AU-2` | DISA STIG `NET0700` | ISO/IEC 27001 `A.12.4` |
| **NTP Configured** | `NET-14` | NIST SP 800-53 `AU-8` | DISA STIG `NET0705` | ISO/IEC 27001 `A.12.4` |

### C. Absence-Based (Negative) Controls
Several critical security controls inspect for the **absence** of unauthorized protocols (e.g. `NET-01` verifying Telnet is absent, `NET-04` verifying HTTP management is absent).

### D. Structured Evaluation Basis & Explanation Output
Every test result explicitly reports:
1. **Evaluation Status**: `PASSED`, `FAILED`, or `WARNING`.
2. **Evaluation Basis Box**: `Expected: disabled / no | Observed: yes (transport input telnet)`.
3. **Benchmark Rationale**: Explanation of why the benchmark requirement exists.

---

## 5. Detailed Feature Breakdown (Page-by-Page)

### Feature 1: SOC Operations Dashboard (`/`)
- **Executive Gauges**: Overall Compliance Score (%), Devices Audited count, Critical Findings count, and live **Teaching Generalization Rate (TGR)** score card.
- **Visual Analytics**: Interactive Recharts bar charts showing Compliance Score by Vendor and pie charts showing Severity Distribution (`PASS`, `FAIL`, `CRITICAL`).
- **Recent Findings Table**: Live snapshot of recent audit findings with severity badges.
- **Backend Health Probe**: Real-time indicator displaying `Backend API: ONLINE`.

### Feature 2: Multi-Vendor Configuration Auditor (`/audits`)
- **Preset Quick-Loaders**: One-click buttons to load Cisco IOS, Juniper JunOS, Fortinet FortiGate, or Unknown Vendor sample configurations.
- **File & Text Ingestion**: Drag-and-drop file upload or direct raw text area input.
- **Vendor Detection**: Instant signature fingerprinting identifying Cisco, Juniper, Fortinet, or Unknown.
- **Findings Breakdown**: Detailed test finding cards displaying all 4 benchmark badges (`CIS`, `NIST`, `DISA STIG`, `ISO`), expected vs. observed states, exact line numbers, and raw source line evidence.
- **Predicted Post-Remediation Delta**: Calculates hypothetical post-remediation compliance score improvement (`BEFORE: 65%` ➔ `PREDICTED AFTER: 100% (+35%)`).

### Feature 3: Network Device Inventory (`/devices`, `/devices/:id`)
- **Device Registry**: Lists audited devices with hostnames, vendors, total audit counts, highest/lowest scores, and last audited timestamps.
- **Device Detail View**: Deep dive into a specific device showing its complete audit history and control findings.

### Feature 4: Cross-Vendor Security Findings (`/findings`)
- **Centralized Findings Hub**: Master list of all security findings across all audited devices.
- **Multi-Filter Controls**: Filter findings dynamically by Vendor (`Cisco`, `Juniper`, `Fortinet`) or Severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

### Feature 5: Knowledge Base Management (`/knowledge-base`)
- **Vector Store Exemplar Repository**: Table displaying all administrator-taught configuration exemplars.
- **Exemplar Metadata**: Command text, security category, normalized parameter, expected value, control ID, version number, and approval status (`APPROVED` or `PENDING`).
- **Approval Workflow**: Admin controls to approve or reject learned exemplars.

### Feature 6: Multi-Format Report Exporter (`/reports`)
- **PDF Report Download**: Downloads a ReportLab compiled PDF document complete with title banner, executive summary table, security findings table, exact evidence lines, and CLI fix scripts.
- **CSV Export**: Downloads a CSV spreadsheet of audit findings.
- **JSON Export**: Downloads formatted raw JSON for SIEM integration.

### Feature 7: System Settings & Strategy Controls (`/settings`)
- **Similarity Threshold Slider**: Configurable slider controlling automatic classification threshold (default: 80% cosine similarity).
- **Framework Strategy Overview**: Displays active vs. extensible security frameworks.

---

## 6. HERO FEATURE: Interactive Semantic Learning Center & TGR (`/training`)

### The Problem Addressed
Traditional network compliance auditors rely on rigid regex rules. When a vendor introduces a new OS syntax or a custom configuration command (e.g. `set xyz secure-admin-timeout 300`), traditional parsers fail completely and require developer code changes and application redeployments.

### The Semantic Few-Shot Solution
Our auditor implements a **Human-in-the-Loop Few-Shot Vector Similarity Engine**:

```
Unknown Command Line Detected (e.g. "set xyz secure-admin-timeout 300")
        ↓
Generate Vector Embedding (sentence-transformers / offline n-gram embedder)
        ↓
Cosine Similarity Search over Learned Vector Exemplars
        ↓
Confidence < Threshold (21% Low Confidence) → Route to Interactive Training UI
        ↓
Administrator Selects: Category, Parameter, Expected Value, Control ID
        ↓
Save Exemplar → Store Embedding in Local Vector Database
        ↓
System Instantly Classifies Future Unseen Variant ("set xyz secure-admin-timeout 240")
with HIGH CONFIDENCE (85%+) WITHOUT Code Change or Redeploy!
```

### Teaching Generalization Rate (TGR) Engine
To ensure performance is empirically measured rather than fabricated, the system implements **TGR**:

$$\text{TGR} = \left( \frac{\text{Correctly Classified Held-Out Unseen Variants}}{\text{Total Held-Out Unseen Variants}} \right) \times 100$$

- **Measured TGR Output**: **100% Generalization Rate** verified across held-out evaluation pairs.

---

## 7. Security & Governance Principles

1. **Deterministic Compliance Gate (AI Safety)**:
   - AI/LLM embeddings are used ONLY for natural language explanation and vector similarity classification of unknown commands.
   - **Pass/Fail decisions are 100% deterministic** (YAML rule engine). AI never decides compliance.

2. **Prompt-Injection Safe & Untrusted Data Isolation**:
   - Configuration files are treated strictly as untrusted data strings, never as system-level prompt instructions.

3. **Human-in-the-Loop Remediation Approval**:
   - Remediation scripts are generated using deterministic vendor templates and syntax-validated, but labeled **`"PREDICTED — NOT APPLIED"`**. Nothing is ever pushed automatically to a live network device.

---

## 8. Live Hackathon Presentation Script (2-Minute Walkthrough)

1. **Start Services**:
   - Backend: `cd backend && python3 -m uvicorn app.main:app --reload --port 8000`
   - Frontend: `cd frontend && npm run dev` (Access at `http://localhost:5173`)
2. **Dashboard Review**: Show SOC Dashboard, Overall Compliance Score, and Vendor Score charts.
3. **Run Multi-Vendor Audits (`/audits`)**:
   - Load **Cisco IOS** ➔ Run Audit ➔ Show Telnet/HTTP findings, exact line numbers, and predicted post-remediation score (+35%).
   - Load **Juniper JunOS** ➔ Run Audit ➔ Demonstrate cross-vendor normalization.
4. **Demonstrate Hero Feature (`/training`)**:
   - Load **Unknown Vendor** sample (`set xyz secure-admin-timeout 300`).
   - Open **Training Center** (`/training`). Show low confidence (21%).
   - Fill structured dropdowns: Category `Authentication`, Parameter `admin_session_timeout`, Expected `300`, Control `CIS-NET-18`.
   - Click **Save Exemplar & Update Memory**.
   - View instant verification: Unseen variant (`set xyz secure-admin-timeout 240`) recognized with **HIGH CONFIDENCE (85%+)** without code redeployment. Highlight **Teaching Generalization Rate: 100%**.
5. **Report Export (`/reports`)**: Click **PDF** to view the ReportLab audit report.
