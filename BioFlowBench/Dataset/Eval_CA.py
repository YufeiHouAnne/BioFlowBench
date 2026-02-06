import typing
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


class QuestionAnswer(BaseModel):
    BLANK: str = Field(description="the blank value that should replace the '[BLANK]' in the statement")

fill_in_the_blank_prompt_template = """You are a highly specialized expert in bioinformatics command-line tools. Your knowledge is precise and up-to-date.
Your task is to provide the exact value that should replace the '[BLANK]' in the following statement.
The output must strictly follow the format: {format_instructions}
Now, the question is: {question}
Provide the answer now.
"""

class ExamAgent:
    def __init__(self, temperature: float = 0.1):
        self.parser = PydanticOutputParser(pydantic_object=QuestionAnswer)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", fill_in_the_blank_prompt_template)
        ])
        
        # 配置 LLM
        self.llm = ChatOpenAI(
            base_url="",
            api_key="",
            model="",
            temperature=temperature
        )

    def solve(self, question: str):
        
        chain = self.prompt | self.llm | self.parser
        try:
            result = chain.invoke({
                "question": question, 
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            print(f"Error during inference: {e}")
            return None

def answer_question(question: str):
    agent = ExamAgent()
    result = agent.solve(question)
    
    if result is None:
        return None
    else:
        return result.model_dump()


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False

def calculate_custom_accuracy(ground_truths: typing.List[str], predictions: typing.List[str]) -> float:
    if len(ground_truths) != len(predictions):
        raise ValueError("The length of ground_truths and predictions must be the same.")

    total_count = len(ground_truths)
    if total_count == 0:
        return 0.0  
    correct_count = 0
    for gt, pred in zip(ground_truths, predictions):
        is_matched = False
        if gt.strip() == pred.strip():
            is_matched = True
        
        if is_matched:
            correct_count += 1
            
    return correct_count 


import tqdm
if __name__ == "__main__":
    data1 = {}
    count = 0
    y_true = []
    y_pred = []
    wrong_set = []
    file_list = ["./Contextual_Application.json"]
    for file in file_list:
        y_true = []
        y_pred = []
        data = json.load(open(file, "r"))
        for item in tqdm.tqdm(data):
            question = item["question"]
            answer = item["correct_answer"]
            result = answer_question(question)
            if result:
                y_true.append(answer)
                y_pred.append(result["BLANK"])
                if(answer != result["BLANK"]):
                    wrong_set.append(item)
        acc = calculate_custom_accuracy(y_true, y_pred)
        print(file)
        print(acc)
        data1[str(file)] = {"acc": acc}
        count+=1
    print(data1)