import regex
from validator_regex.strategies.ValidationStrategy import ValidationStrategy


class NameValidation(ValidationStrategy):
    """
    Estratégia de validação para valores de nomes.

    Esta classe implementa a interface `ValidationStrategy` e utiliza expressões
    regulares para validar se uma string representa corretamente um valor de
    nome.

    Attributes:
        pattern (Pattern): Expressão regular pré-compilada usada para validar
        o formato nome.
    """

    pattern = regex.compile(r"^(?:(?:[A-ZÀ-Ý][a-zà-ÿ]+)(?:['\- ][A-ZÀ-Ýa-zà-ÿ]+)*)$")

    def validate(self, text: str) -> bool:
        """
        Valida se o texto fornecido representa um valor de nome.

        Args:
            text (str): Texto que se deseja validar, por exemplo,
            "Carlos da Costa".

        Returns:
            bool:
                - `True` se o texto corresponder a um nome válido.
                - `False` caso contrário.
        """
        return bool(self.pattern.match(text))
