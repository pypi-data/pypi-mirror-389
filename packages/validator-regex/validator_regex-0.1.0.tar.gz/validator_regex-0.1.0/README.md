# 📌 validator-regex 

[![PyPI version](https://img.shields.io/pypi/v/validator-regex.svg)](https://pypi.org/project/validator-regex/)  
[![Python versions](https://img.shields.io/pypi/pyversions/validator-regex.svg)](https://pypi.org/project/validator-regex/)  
[![License](https://img.shields.io/pypi/l/validator-regex.svg)](https://github.com/jcarlossc/validator-regex/blob/main/LICENSE)  
[![Documentation Status](https://readthedocs.org/projects/validator-regex/badge/?version=latest)](https://validator-regex.readthedocs.io/en/latest/)

## 📌 Descrição

**validator-regex** é uma biblioteca Python que fornece uma arquitetura modular para validação de entradas usando expressões regulares (Regex), aplicando o padrão de projeto *Strategy* e *Facade*.  
Ela suporta vários tipos de validação: e-mail, valores monetários (BRL), CPF, CNPJ, hora e nomes próprios.

O objetivo é permitir que desenvolvedores **importem e usem facilmente** estratégias de validação prontas, e possam **adicionar novas estratégias** conforme suas necessidades.

---

## 📌 Funcionalidades principais

- Validação de e-mails conforme padrão RFC (com alguns limites práticos)  
- Validação de valores monetários no formato **BRL** (ex: `R$ 1.234,56`)  
- Validação de CPF (formato `###.###.###-##`)  
- Validação de CNPJ (formato `##.###.###/####-##`)  
- Validação de hora no formato 24h (ex: `HH:MM` ou `HH:MM:SS`)  
- Validação de nomes próprios  
- Arquitetura limpa com Strategy + Facade → fácil extensão  
- Tipagem estática suportada (mypy) – boas práticas de qualidade de código  
- Testes automatizados com pytest e formatação com black

---

## 📌 Estrutura do Projeto
```bash
validator-regex/
│
├── validator_regex/                       # Código-fonte principal
│   ├── __init__.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── ValidationStrategy.py          # Interface Strategy
│   │   ├── EmailValidation.py
│   │   ├── BRLCurrencyValidation.py
│   │   ├── CPFValidation.py
│   │   ├── CNPJValidation.py
│   │   ├── TimeValidation.py
│   │   └── NameValidation.py
│   ├── ValidatorContext.py                # Contexto que usa as estratégias
│   └── RegexValidator.py                  # Facade simples
│
├── tests/
│   ├── __init__.py
│   ├── test_emailvalidation.py
│   ├── test_brlcurrencyvalidation.py
│   ├── test_cpfvalidation.py
│   ├── test_cnpjvalidation.py
│   ├── test_timevalidation.py
│   └── test_namevalidation.py
│                    
├── LICENSE                      
├── .gitignore                    
├── poetry.lock                        
├── pyproject.toml                         # Configuração do Poetry
├── README.md                              # Documentação do projeto
└── LICENSE

```
---

## 📌 Instalação

```bash
pip install validator-regex
```
---

## 📌 Ou se estiver usando Poetry:
```bash
poetry add validator-regex
```
---

---

## 📌 Mode de utilizar
```bash
from validator_regex.RegexValidator import RegexValidator

# E-mail
print(RegexValidator.is_email("usuario@exemplo.com"))   # → True
print(RegexValidator.is_email("usuario.exemplo"))       # → False

# Moeda BRL
print(RegexValidator.is_brl("R$ 1.234,56"))             # → True
print(RegexValidator.is_brl("R$1234.56"))               # → False

# CPF
print(RegexValidator.is_cpf("123.456.789-09"))          # → True
print(RegexValidator.is_cpf("12345678909"))             # → False

# CNPJ
print(RegexValidator.is_cnpj("12.345.678/0001-95"))     # → True

# Hora
print(RegexValidator.is_time("23:59"))                  # → True
print(RegexValidator.is_time("24:00"))                  # → False

# Nomes
print(RegexValidator.is_name("Carlos da Costa"))        # → True
print(RegexValidator.is_name("Carlos123"))              # → True
```
---

## 📌 Contribuição

Contribuições são bem-vindas!
Se você deseja adicionar uma nova estratégia de validação ou melhorar a existente, siga estes passos:

- Faça um fork do repositório
- Crie uma branch com a nova funcionalidade (feature/nova-validacao)
- Escreva o código e os testes correspondentes
- Certifique-se de que todos os testes passam:

```bash
poetry run pytest
```
- Envie um pull request explicando a mudança
- Por favor, siga as convenções de código (pytest, black e mypy) e mantenha qualidade de código.

## 📌 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📌 Autor
📌Carlos da Costa<br>
📌Recife, PE - Brasil<br>
📌Telefone: +55 81 99712 9140<br>
📌Telegram: @jcarlossc<br>
📌Blogger linguagem R: https://informaticus77-r.blogspot.com/<br>
📌Blogger linguagem Python: https://informaticus77-python.blogspot.com/<br>
📌Email: jcarlossc1977@gmail.com<br>
📌Portfólio temporário: https://portfolio-carlos-costa.netlify.app/<br>
📌LinkedIn: https://www.linkedin.com/in/carlos-da-costa-669252149/<br>
📌GitHub: https://github.com/jcarlossc<br>
📌Kaggle: https://www.kaggle.com/jcarlossc/<br>
📌Twitter/X: https://x.com/jcarlossc1977<br>

---



