# AI-Powered Mortgage Processing Crew

This project is an advanced AI-driven application designed to automate and streamline the mortgage loan application process. It leverages a team of specialized AI agents, orchestrated by the CrewAI framework, to perform document validation, data extraction, and creditworthiness assessment. The application is presented through an interactive and user-friendly web interface built with Streamlit.

---

## Description

The primary goal of this project is to significantly reduce the manual effort and time required to process a mortgage application. By uploading the necessary documents (such as ID, payslips, and bank statements), the system automatically validates their completeness, extracts relevant applicant data, and performs an underwriting assessment based on the **Five C's of Credit** framework. The final output is a comprehensive report and a clear approval or rejection decision.

---

## Architecture

The application is built on a modular architecture that separates the user interface from backend processing. The Streamlit front-end provides a simple way for users to upload documents and view the results, while the CrewAI backend orchestrates the complex workflow of the AI agents.

---

## Workflow

1. **Document Upload:** The user uploads the required documents through the Streamlit web interface.
2. **Document Validation:** The Document Validator agent checks if all the required documents and fields are present.
3. **Data Extraction:** The Loan Processor agent extracts and verifies applicant data from the validated documents.
4. **Creditworthiness Assessment:** The Underwriter agent assesses the applicant's creditworthiness based on the extracted data.
5. **Output:** The final decision and a detailed report are displayed to the user and can be downloaded as a PDF.

---

## Features

- **Automated Document Validation:** Automatically checks for the presence of all required documents and essential fields.
- **Intelligent Data Extraction:** Extracts and verifies applicant data from various document formats, including PDFs and images.
- **Comprehensive Underwriting:** Assesses creditworthiness using the "Five C's of Credit" framework (Character, Capacity, Capital, Collateral, and Conditions).
- **Interactive Dashboard:** A user-friendly Streamlit interface for uploading documents and visualizing the results.
- **PDF Report Generation:** Generates a downloadable PDF report with all the applicant data and the underwriting decision.
- **Extensible and Configurable:** The roles, tasks, and backstories of the AI agents can be easily configured in the provided YAML files.

---

## Getting Started

To get the project up and running on your local machine, follow these steps.

### Prerequisites

- Python 3.8+
- An OpenAI API Key
- A Mistral API Key

### Installation

1. **Clone the repository:**

2. **Install the required Python packages:**
    ```sh
    pip install -r requirements.txt
    ```
    *Note: You will need to create a `requirements.txt` file based on the imports in the Python files.*

3. **Set up your environment variables:**

    Create a `.env` file in the root of the project and add the following:
    ```
    OPENAI_API_KEY="your_openai_api_key"
    MISTRAL_API_KEY="your_mistral_api_key"
    ```

---

## Running the Application

To run the Streamlit application, execute the following command in your terminal:

```sh
streamlit run app.py
```

This will start a local web server, and you can access the application through your browser at the provided URL (usually http://localhost:8501).

---

## Configuration

The behavior of the AI agents can be customized by editing the following YAML files:

- **mortgage_agents.yaml:** Defines the roles, goals, and backstories for each AI agent in the crew.
- **mortgage_tasks_lenient.yaml / mortgage_tasks_org.yaml:** Outlines the specific tasks that the agents will perform, including their descriptions and expected outputs.

---

## Tools

- **PDFQATool.py:** A custom tool that leverages the Mistral API to perform OCR and answer questions about the content of PDF and image files. This is essential for extracting data from the uploaded documents.

---

