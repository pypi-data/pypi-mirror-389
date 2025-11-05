"""
This file offers a functionality of going through every diff and checking for most common cabersecurity mistake i.e. Broken Access Control
"""

from typing import List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .base_analyzer import BaseAnalyzer, Finding, Commit, DiffItem
from .prompts import security_misconfig_prompt
from .pydantic_models import Finding, FindingsList



class SecurityMisconfigAnalyzer(BaseAnalyzer[Finding]):
    
    def __init__(self, repo_url: str, llm_api_key: str, 
                 model: str = "gpt-4.1"):
        super().__init__(repo_url)
        
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=llm_api_key,
            temperature=0
        ).with_structured_output(FindingsList)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", security_misconfig_prompt),
            ("human", "Commit: {commit_hash}\nFile: {file_path}\n\nDiff:\n{diff_content}")
        ])
        
        self.chain = self.prompt | self.llm
    
    def _analyze_diff(self, commit: Commit, diff_item: DiffItem, 
                     file_path: str) -> List[Finding]:
        
        added_lines = self._parse_added_lines(diff_item.diff)
        
        if len(added_lines) < 2:
            return []
        
        try:
            formatted = '\n'.join(f"Line {num}: {content}" for num, content in added_lines)
            
            result = self.chain.invoke({
                "commit_hash": commit.hexsha,
                "file_path": file_path,
                "diff_content": formatted
            })
            
            return result.findings
            
        except Exception as e:
            print(f"Error: {e}")
            return []