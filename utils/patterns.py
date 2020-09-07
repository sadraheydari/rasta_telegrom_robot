import re


def is_pdf(file_name: str):
    __pattern = re.compile("(.*)\.pdf", flags=re.IGNORECASE)
    return bool(__pattern.match(file_name))


def is_img(file_name: str):
    __pattern = re.compile("(.*).[jpg|png|jpeg]", flags=re.IGNORECASE)
    return bool(__pattern.match(file_name))