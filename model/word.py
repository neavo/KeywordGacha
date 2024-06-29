import os
import re
import json
import concurrent.futures
from openai import OpenAI
from collections import Counter
from concurrent.futures import as_completed


class Word:
    def __init__(self):
        self.name = False
        self.count = 0
        self.context = []
        self.surface = ""
        self.llmresponse = ""

    def set_name(self, name: bool):
        self.name = name

    def set_count(self, count: int):
        self.count = count

    def set_context(self, context: list):
        self.context = context

    def set_surface(self, surface: str):
        self.surface = surface

    def set_llmresponse(self, llmresponse: str):
        self.llmresponse = llmresponse