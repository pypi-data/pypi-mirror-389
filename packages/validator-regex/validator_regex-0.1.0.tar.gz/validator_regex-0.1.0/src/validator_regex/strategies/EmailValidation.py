import regex
from validator_regex.strategies.ValidationStrategy import ValidationStrategy


class EmailValidation(ValidationStrategy):
    """
    Estratégia de validação para valores de email.

    Esta classe implementa a interface `ValidationStrategy` e utiliza expressões
    regulares para validar se uma string representa corretamente um valor de
    email.

    Attributes:
        pattern (Pattern): Expressão regular pré-compilada usada para validar
        o formato email.
    """

    pattern = regex.compile(
        r"^(?:[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+"
        r"(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"
        r"|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21"
        r"\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b"
        r"\x0c\x0e-\x7f])*\")@"
        r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*"
        r"[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}"
        r"|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?"
        r"[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?"
        r"[0-9][0-9]?|[a-zA-Z0-9-]*"
        r"[a-zA-Z0-9]:"
        r"(?:[\x01-\x08\x0b\x0c\x0e-\x1f"
        r"\x21-\x5a\x53-\x7f]"
        r"|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)])$"
    )

    def validate(self, text: str) -> bool:
        """
        Valida se o texto fornecido representa um valor de email.

        Args:
            text (str): Texto que se deseja validar, por exemplo,
            "carlos@gmail.com".

        Returns:
            bool:
                - `True` se o texto corresponder a um email válido.
                - `False` caso contrário.
        """
        return bool(self.pattern.match(text))
