# coding: utf-8

"""Shows the usage of pywhatlang."""


import pywhatlang
TEXTS = [
    "Hello world. It is my pleasure to be here!",
    "مرحباً بالجميع. من دواعي سروري أن أكون معكم!"
]

def main():
    for text in TEXTS:
        lang, confidence, is_reliable = pywhatlang.detect_lang(text)
        print(f"The detected language is {lang}\nConfidence: {confidence}\nis_reliable: {is_reliable}")


if __name__ == '__main__':
    main()