import regex
from validator_regex.strategies.ValidationStrategy import ValidationStrategy


class TimeValidation(ValidationStrategy):
    """
    Estratégia de validação para valores de hora.

    Esta classe implementa a interface `ValidationStrategy` e utiliza expressões
    regulares para validar se uma string representa corretamente um valor de
    hora.

    Attributes:
        pattern (Pattern): Expressão regular pré-compilada usada para validar
        o formato hora.
    """

    pattern = regex.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$")

    def validate(self, text: str) -> bool:
        """
        Valida se o texto fornecido representa um valor de hora.

        Args:
            text (str): Texto que se deseja validar, por exemplo,
            "23:44" ou "23:44:44".

        Returns:
            bool:
                - `True` se o texto corresponder a uma hora válida.
                - `False` caso contrário.
        """
        return bool(self.pattern.match(text))
