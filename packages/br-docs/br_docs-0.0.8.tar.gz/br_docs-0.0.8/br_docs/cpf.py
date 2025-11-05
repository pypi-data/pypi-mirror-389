from random import randint
from typing import Generator


def is_masked(cpf: str) -> bool:
    return "." in cpf and "-" in cpf


def mask(cpf: str) -> str:
    if is_masked(cpf):
        return cpf
    new_cpf = ""
    digit_position = 0
    for digit in cpf:
        digit_position += 1
        if digit_position == 3 or digit_position == 6:
            new_cpf += digit + "."
            continue
        if digit_position == 9:
            new_cpf += digit + "-"
            continue
        new_cpf += digit
    return new_cpf


def remove_mask(cpf: str) -> str:
    if not is_masked(cpf):
        return cpf
    new_cpf = ""
    for digit in cpf:
        if digit.isnumeric():
            new_cpf += digit
    return new_cpf


def __is_valid(cpf: str) -> bool:
    if len(cpf) != 11 or cpf.count(cpf[0]) == 11:
        return False
    first_result = 0
    second_result = 0
    sequence = 10
    for digit in cpf[:-2:]:
        digit = int(digit)
        first_result += digit * sequence
        second_result += digit * (sequence + 1)
        sequence -= 1
    second_result += int(cpf[-2]) * 2
    first_result = (first_result * 10) % 11
    if first_result == 10:
        first_result = 0
    second_result = (second_result * 10) % 11
    if second_result == 10:
        second_result = 0
    return str(first_result) == cpf[-2] and str(second_result) == cpf[-1]


def is_valid(cpf: str) -> bool:
    cpf = remove_mask(cpf)
    return __is_valid(cpf)


def validate(cpf: str) -> str:
    cpf = remove_mask(cpf)
    if __is_valid(cpf):
        return cpf
    raise "Invalid CPF"


def __generate_verificator_digits(cpf) -> str:
    first_result = 0
    second_result = 0
    sequence = 10
    for digit in cpf:
        first_result += int(digit) * sequence
        second_result += int(digit) * (sequence + 1)
        sequence -= 1
    first_result = (first_result * 10) % 11
    if first_result == 10:
        first_result = 0
    cpf += str(first_result)
    second_result += first_result * 2
    second_result = (second_result * 10) % 11
    if second_result == 10:
        second_result = 0
    cpf += str(second_result)
    return cpf


def generate(masked: bool = False) -> str:
    cpf = ""
    for _ in range(9):
        cpf += str(randint(0, 9))
    cpf = __generate_verificator_digits(cpf)
    if cpf.count(cpf[0]) != 11:
        if masked:
            return mask(cpf)
        return cpf
    return generate()


def gen_generate(masked: bool = False) -> Generator:
    while True:
        yield generate(masked)
