def validar_cpf(cpf):
    cpf = str(cpf).replace('.', '').replace('-', '').strip()

    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * len(cpf):
        return False

    def calcular_digito(cpf, pos):
        offset = pos + 1
        soma = sum(int(cpf[i]) * (offset - i) for i in range(pos))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    digito1 = calcular_digito(cpf, 9)
    digito2 = calcular_digito(cpf, 10)

    return cpf[-2:] == digito1 + digito2


def validar_cnpj(cnpj):
    cnpj = str(cnpj).replace('.', '').replace('/', '').replace('-', '').strip()

    if len(cnpj) != 14 or not cnpj.isdigit() or cnpj == cnpj[0] * len(cnpj):
        return False

    def calcular_digito(cnpj, pos):
        offset = pos - 12
        soma = sum(int(cnpj[i]) * (2 + ((11 + offset - i) % 8))
                   for i in list(reversed(range(pos))))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    digito1 = calcular_digito(cnpj, 12)
    digito2 = calcular_digito(cnpj, 13)

    return cnpj[-2:] == digito1 + digito2


def validar_cpf_cnpj(cpf_cnpj):
    cpf_cnpj = str(cpf_cnpj).replace('.', '').replace('/', '')\
        .replace('-', '').strip()

    if len(cpf_cnpj) <= 11:
        if not validar_cpf(cpf_cnpj):
            return 'Não é um CPF válido.'
    else:
        if not validar_cnpj(cpf_cnpj):
            return 'Não é um CNPJ válido.'

    return None
