from crewai import Agent, Crew, Process, Task
from crewai_tools import  DirectoryReadTool
import os
import yaml
from crewai import LLM
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
load_dotenv()
from PDFQATool import PDFQATool

# Pydantic Models
class DocumentValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether all required documents and fields are present")
    missing_documents: List[str] = Field(default_factory=list, description="List of missing document types")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing fields")

class ApplicantData(BaseModel):
    name: str = Field(..., description="Applicant's full name")
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    address: str = Field(..., description="Residential address")
    income: float = Field(..., description="Annual income in USD")
    assets: float = Field(..., description="Total asset value in USD")
    credit_score: int = Field(..., description="Credit score (300-850)")
    property_value: float = Field(..., description="Appraised property value in USD")
    discrepancies: List[str] = Field(default_factory=list, description="List of issues or inconsistencies")

class UnderwritingDecision(BaseModel):
    approved: bool = Field(..., description="Loan approval status")
    score: float = Field(..., description="Creditworthiness score (0-100)")
    explanation: str = Field(..., description="Detailed decision explanation based on Five C’s")
    ltv_ratio: float = Field(..., description="Loan-to-value ratio (%)")
    dti_ratio: float = Field(..., description="Debt-to-income ratio (%)")

# Load configurations
with open("./mortgage_agents.yaml", "rb") as f:
    agents_config = yaml.safe_load(f)
with open("./mortgage_tasks_lenieant.yaml", "rb") as f:
    tasks_config = yaml.safe_load(f)

# Initialize LLM
llm = LLM(model="openai/gpt-4o-mini", temperature=0.1)

# Set environment variables (replace with your API keys)
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
# os.environ['ANTHROPIC_API_KEY'] = "your_anthropic_api_key"



# import mlflow

# mlflow.crewai.autolog()
# mlflow.set_tracking_uri("http://localhost:5000")
# mlflow.set_experiment("Mortgage_Crew_Experiment")





class MortgageCrew:
    def __init__(self):
        self.agents_config = agents_config
        self.tasks_config = tasks_config
        self.DirectorySearchTool = DirectoryReadTool(directory='./documents')
        # self.VisionTool = VisionTool()
        self.PDFQATool = PDFQATool()    

    def document_validator(self) -> Agent:
        return Agent(
            config=self.agents_config['document_validator'],
            verbose=True,
            tools=[self.DirectorySearchTool, self.PDFQATool,],
            allow_delegation=False,
            memory=True,
            llm=llm,
        )

    def loan_processor(self) -> Agent:
        return Agent(
            config=self.agents_config['loan_processor'],
            verbose=True,
            tools=[self.DirectorySearchTool, self.PDFQATool, ],
            allow_delegation=False,
            memory=True,
            llm=llm,
        )

    def underwriter(self) -> Agent:
        return Agent(
            config=self.agents_config['underwriter'],
            verbose=True,
            tools=[self.DirectorySearchTool, self.PDFQATool,],
            allow_delegation=True,
            memory=True,
            llm=llm,
        )

    def validate_documents_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_documents_task'],
            verbose=True,
            agent=self.document_validator(),
            tools=[self.DirectorySearchTool, self.PDFQATool,],
            output_pydantic=DocumentValidationResult,
            human_input=False,
         
        )

    def process_documents_task(self) -> Task:
        return Task(
            config=self.tasks_config['process_documents_task'],
            verbose=True,
            agent=self.loan_processor(),
            tools=[self.DirectorySearchTool, self.PDFQATool,],
            output_pydantic=ApplicantData,
            human_input=False,
            # fallback_tools=[self.VisionTool],
        )

    def underwriter_task(self) -> Task:
        return Task(
            config=self.tasks_config['assess_creditworthiness_task'],
            verbose=True,
            agent=self.underwriter(),
            tools=[self.DirectorySearchTool, self.PDFQATool,],
            output_pydantic=UnderwritingDecision,
            human_input=False,
          
        )

    def crew(self):
        return Crew(
            agents=[self.document_validator(), self.loan_processor(), self.underwriter()],
            tasks=[
                self.validate_documents_task(),
                self.process_documents_task(),
                self.underwriter_task(),
            ],
            process=Process.sequential,
            memory=True,
            verbose=True,
        )

    def kickoff(self, inputs=None):
        validation_only = inputs.get('validation_only', False) if inputs else False
        if validation_only:
            crew = Crew(
                agents=[self.document_validator()],
                tasks=[self.validate_documents_task()],
                process=Process.sequential,
                memory=True,
                verbose=True,
            )
            return crew.kickoff(inputs=inputs)
        return self.crew().kickoff(inputs=inputs)
