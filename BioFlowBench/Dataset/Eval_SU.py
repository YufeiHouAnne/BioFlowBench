from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel,Field
from typing import Optional, List, Union, Dict, Any, Literal
import json
import os
import time
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_core.output_parsers import PydanticOutputParser
import re
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

import os

file_list = ["./Syntax_Understanding.json"]

class QuestionAnswer(BaseModel):
    correct_option: Literal["A", "B", "C", "D"] = Field(description="The key of the correct option (A, B, C, or D)")

exam_prompt_template = '''
You are a bioinformatics expert. 
Your task is to answer the following multiple-choice question accurately.
Question: 
{question}
Options:
{options_str}
Instructions:
1. Evaluate each option (A, B, C, D) carefully based on the documentation or standard behavior of the tool.
2. The output must strictly follow the format: {format_instructions}
'''

class ExamAgent:
    def __init__(self, temperature: float = 0.1):
        self.parser = PydanticOutputParser(pydantic_object=QuestionAnswer)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", exam_prompt_template)
        ])
        
        # 配置 LLM
        self.llm = ChatOpenAI(
            base_url="",
            api_key="",
            model="",
            temperature=temperature
        )

    def solve(self, question: str, options: Dict[str, str]):
        options_str = "\n".join([f"{k}: {v}" for k, v in options.items()])
        
        chain = self.prompt | self.llm | self.parser
        try:
            result = chain.invoke({
                "question": question, 
                "options_str": options_str, 
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            print(f"Error during inference: {e}")
            return None

def answer_question(question: str, options: Dict[str, str]):
    agent = ExamAgent()
    result = agent.solve(question, options)
    
    if result is None:
        return None
    else:
        return result.model_dump()

def get_score(y_true,y_pred):
    acc = accuracy_score(y_true, y_pred)
    p_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    r_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    return acc, p_macro, r_macro, f1_macro

import tqdm
if __name__ == "__main__":
    data1 = {}
    count = 0
    y_true = []
    y_pred = []
    wrong_set = []
    for file in file_list:
        y_true = []
        y_pred = []
        data = json.load(open(file, "r"))
        for item in tqdm.tqdm(data):
            question = item["question"]
            options = item["options"]
            answer = item["answer"]
            result = answer_question(question, options)
            if result:
                y_true.append(answer)
                y_pred.append(result["correct_option"])
                if(answer != result["correct_option"]):
                    wrong_set.append(item)
        acc, p_macro, r_macro, f1_macro = get_score(y_true, y_pred)
        print(file)
        print(acc, p_macro, r_macro, f1_macro)
        data1[str(count)] = {"acc": acc, "p_macro": p_macro, "r_macro": r_macro, "f1_macro": f1_macro}
        count+=1
    print(data1)  
    
