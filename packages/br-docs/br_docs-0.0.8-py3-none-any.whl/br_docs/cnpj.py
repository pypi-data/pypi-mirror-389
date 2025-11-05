from random import randint
from typing import Generator


def is_masked(cnpj: str) -> bool:
    return "." in cnpj and "/" in cnpj and "-" in cnpj


def mask(cnpj: str) -> str:
    if is_masked(cnpj):
        return cnpj
    masked_cnpj = ""
    for i in range(1, len(cnpj) + 1):
        masked_cnpj += cnpj[i - 1]
        if i == 2 or i == 5:
            masked_cnpj += "."
            continue
        if i == 8:
            masked_cnpj += "/"
            continue
        if i == 12:
            masked_cnpj += "-"
    return masked_cnpj


def remove_mask(cnpj: str) -> str:
    if not is_masked(cnpj):
        return cnpj
    new_cnpj = ""
    for digit in cnpj:
        if digit.isnumeric():
            new_cnpj += digit
    return new_cnpj


def __is_valid(cnpj: str) -> bool:
    if len(cnpj) != 14:
        return False
    first_result = 0
    second_result = 0
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(len(cnpj) - 2):
        first_result += int(cnpj[i]) * weights[i + 1]
        second_result += int(cnpj[i]) * weights[i]
    second_result += int(cnpj[-2]) * weights[-1]
    first_result %= 11
    if first_result < 2:
        first_result = 0
    else:
        first_result = 11 - first_result
    second_result %= 11
    if second_result < 2:
        second_result = 0
    else:
        second_result = 11 - second_result
    return str(first_result) == cnpj[-2] and str(second_result) == cnpj[-1]


def is_valid(cnpj: str) -> bool:
    cnpj = remove_mask(cnpj)
    return __is_valid(cnpj)


def validate(cnpj: str) -> str:
    cnpj = remove_mask(cnpj)
    if __is_valid(cnpj):
        return cnpj
    raise "Invalid CNPJ"


def __generate_verificator_digits(cnpj: str) -> str:
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first_result = 0
    second_result = 0
    for i in range(len(cnpj)):
        first_result += int(cnpj[i]) * weights[i + 1]
        second_result += int(cnpj[i]) * weights[i]
    first_result %= 11
    if first_result < 2:
        first_result = 0
    else:
        first_result = 11 - first_result
    second_result += first_result * 2
    second_result %= 11
    if second_result < 2:
        second_result = 0
    else:
        second_result = 11 - second_result
    cnpj += str(first_result) + str(second_result)
    return cnpj


def generate(masked: bool = False) -> str:
    cnpj = ""
    for _ in range(12):
        cnpj += str(randint(0, 9))
    if masked:
        return mask(__generate_verificator_digits(cnpj))
    return __generate_verificator_digits(cnpj)


def gen_generate(masked: bool = False) -> Generator:
    while True:
        yield generate(masked)
