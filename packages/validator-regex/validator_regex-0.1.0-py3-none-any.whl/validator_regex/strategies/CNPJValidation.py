import regex
from validator_regex.strategies.ValidationStrategy import ValidationStrategy


class CNPJValidation(ValidationStrategy):
    """
    Estratégia de validação para valores de CNPJ.

    Esta classe implementa a interface `ValidationStrategy` e utiliza expressões
    regulares para validar se uma string representa corretamente um valor de
    CNPJ.

    Attributes:
        pattern (Pattern): Expressão regular pré-compilada usada para validar
            o formato CNPJ.
    """

    pattern = regex.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")

    def validate(self, text: str) -> bool:
        """
        Valida se o texto fornecido representa um valor de CNPJ.

        Args:
            text (str): Texto que se deseja validar, por exemplo,
            "12.569.987/0211-95".

        Returns:
            bool:
                - `True` se o texto corresponder ao CNPJ válido.
                - `False` caso contrário.
        """
        return bool(self.pattern.match(text))
