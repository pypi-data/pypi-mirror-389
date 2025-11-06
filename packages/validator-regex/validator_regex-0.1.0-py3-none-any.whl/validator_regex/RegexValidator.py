from validator_regex.ValidatorContext import ValidatorContext
from validator_regex.strategies.EmailValidation import EmailValidation
from validator_regex.strategies.BRLCurrencyValidation import BRLCurrencyValidation
from validator_regex.strategies.NameValidation import NameValidation
from validator_regex.strategies.CPFValidation import CPFValidation
from validator_regex.strategies.CNPJValidation import CNPJValidation
from validator_regex.strategies.TimeValidation import TimeValidation


class RegexValidator:
    """
    Classe utilitária para validação de textos com expressões regulares,
    baseada no padrão de projeto Strategy e no contexto `ValidatorContext`.

    Esta classe atua como uma fachada(Facade) simplificada para diversas estratégias
    de validação (como e-mail, CPF, CNPJ, nome, moeda BRL e hora), permitindo
    que o usuário chame métodos estáticos diretos sem precisar instanciar
    manualmente o contexto ou as estratégias.

    Observations:
        Cada método estático cria internamente uma instância de `ValidatorContext`
        associada à estratégia apropriada, e executa a validação via método `validate()`.

    Attributes:
        Nenhum atributo de instância é definido, pois todos os métodos são estáticos.

    """

    @staticmethod
    def is_email(text: str) -> bool:
        """
        Valida se o texto fornecido é um e-mail válido.

        Args:
            text (str): Texto que será validado como endereço de e-mail.

        Returns:
            bool: Retorna True se o texto corresponder a um e-mail válido;
            caso contrário, retorna False.
        """
        return ValidatorContext(EmailValidation()).validate(text)

    @staticmethod
    def is_brl(text: str) -> bool:
        """
        Valida se o texto fornecido representa um valor monetário BRL válido
        (ex: 'R$ 1.234,56').

        Args:
            text (str): Texto que será validado como valor monetário BRL.

        Returns:
            bool: Retorna True se o texto corresponder a um valor monetário
            válido; caso contrário, retorna False.
        """
        return ValidatorContext(BRLCurrencyValidation()).validate(text)

    @staticmethod
    def is_name(text: str) -> bool:
        """
        Valida se o texto fornecido é um nome válido (apenas letras,
        acentos e espaços).

        Args:
            text (str): Texto que será validado como um nome.

        Returns:
            bool: Retorna True se o texto corresponder a um nome válido;
            caso contrário, retorna False.
        """
        return ValidatorContext(NameValidation()).validate(text)

    @staticmethod
    def is_cpf(text: str) -> bool:
        """
        Valida se o texto fornecido é um CPF válido (ex: '123.456.789-09').

        Args:
            text (str): Texto que será validado como CPF.

        Returns:
            bool: Retorna True se o texto corresponder a um CPF válido;
            caso contrário, retorna False.
        """
        return ValidatorContext(CPFValidation()).validate(text)

    @staticmethod
    def is_cnpj(text: str) -> bool:
        """
        Valida se o texto fornecido é um CNPJ válido (ex: '12.345.678/0001-95').

        Args:
            text (str): Texto que será validado como CNPJ.

        Returns:
            bool: Retorna True se o texto corresponder a um CNPJ válido;
            caso contrário, retorna False.
        """
        return ValidatorContext(CNPJValidation()).validate(text)

    @staticmethod
    def is_time(text: str) -> bool:
        """
        Valida se o texto fornecido é um horário válido no formato 24h
        (ex: '23:59' ou '23:59:59').

        Args:
            text (str): Texto que será validado como hora.

        Returns:
            bool: Retorna True se o texto corresponder a uma hora válida;
            caso contrário, retorna False.
        """
        return ValidatorContext(TimeValidation()).validate(text)
