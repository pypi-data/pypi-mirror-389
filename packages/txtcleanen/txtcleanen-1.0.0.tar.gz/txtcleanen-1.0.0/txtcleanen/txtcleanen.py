import re
import html
import string
import unicodedata
import os

def txtcleanen(text):

    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'(https?://\S+|www\.\S+)', ' ', text)

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  
        "\U0001F300-\U0001F5FF"  
        "\U0001F680-\U0001F6FF"  
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(' ', text)

    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[' + re.escape(string.punctuation) + r']+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text