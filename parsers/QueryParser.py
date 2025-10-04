import re
import json


def extract_results(input_str):
    pattern = r"\[RESULT\]: (.*?)\n"
    matches = re.findall(pattern, input_str, re.DOTALL)
    results = [json.loads(match) for match in matches]
    return results
