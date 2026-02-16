# Data Directory

This directory contains the knowledge base for the Enterprise Supply Chain Copilot. The system uses Retrieval-Augmented Generation (RAG) to ground its responses in these specific industry reports.

## Document Inventory

The current knowledge base consists of 13 public PDF reports focusing on supply chain trends, resilience, and digital transformation for the 2025 horizon.

### General Industry Trends & Strategy

* **ASCM Top 10 Supply Chain Trends 2025.pdf**: Association for Supply Chain Management's annual ranking of critical industry trends.
* **DHL Logistics Trend Radar.pdf**: Comprehensive analysis of social, business, and technology trends impacting the future of logistics.
* **KPMG Future of Supply Chain Report.pdf** & **KPMG The Future of Supply Chain.pdf**: Strategic insights into operating models and future-proofing supply networks.
* **BSR Future of Supply Chains 2025.pdf**: Focus on sustainability, human rights, and climate resilience in supply chains.

### Corporate Annual Reports & Performance

* **Accenture Annual Report 2025.pdf**: Corporate strategy and performance metrics for Accenture.
* **Accenture 360° Value Report 2025.pdf**: Detailed reporting on non-financial metrics including sustainability and talent.
* **Maersk Annual Report 2024.pdf**: Financials and strategic outlook for a leading global logistics integrator (provides 2025 baseline context).

### Resilience & Risk Management

* **BSI MESH Supply Chain Resilience Report 2025.pdf**: Analysis of global supply chain risks, geopolitical threats, and resilience strategies.
* **WEF Resilience Pulse Check 2025.pdf**: World Economic Forum's assessment of global organizational resilience.

### Technology & Digital Transformation

* **HFS EY Intelligent Supply Chain Services 2025.pdf**: Analysis of EY's capabilities in AI and digital supply chain services.
* **HFS Genpact Intelligent Supply Chain Services 2025.pdf**: Analysis of Genpact's capabilities in AI and digital supply chain services.
* **WEF Supporting Digitalization of SMEs 2025.pdf**: Strategies for integrating Small and Medium Enterprises into digital supply networks.

## Usage Instructions

1. **Adding Files:** To expand the knowledge base, add standard PDF files to this directory.
2. **Indexing:** After adding or removing files, you must rebuild the vector database by running the ingestion script from the project root:
```bash
python retrieval/ingest.py

```


3. **File Requirements:** Ensure files are text-readable (not scanned images) for optimal retrieval performance. The ingestion script supports `PyMuPDF`, `PyPDF`, and `pdfplumber` for robust loading.