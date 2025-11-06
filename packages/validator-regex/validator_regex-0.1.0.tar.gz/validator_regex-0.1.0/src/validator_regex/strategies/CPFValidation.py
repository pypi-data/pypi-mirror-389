import regex
from validator_regex.strategies.ValidationStrategy import ValidationStrategy


class CPFValidation(ValidationStrategy):
    """
    Estratégia de validação para valores de CPF.

    Esta classe implementa a interface `ValidationStrategy` e utiliza expressões
    regulares para validar se uma string representa corretamente um valor de
    CPF.

    Attributes:
        pattern (Pattern): Expressão regular pré-compilada usada para validar
        o formato CPF.
    """

    pattern = regex.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")

    def validate(self, text: str) -> bool:
        """
        Valida se o texto fornecido representa um valor de CPF.

        Args:
            text (str): Texto que se deseja validar, por exemplo,
            "123.456.789-12".

        Returns:
            bool:
                - `True` se o texto corresponder ao CPF válido.
                - `False` caso contrário.
        """
        return bool(self.pattern.match(text))
