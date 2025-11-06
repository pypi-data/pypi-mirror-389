import regex
from validator_regex.strategies.ValidationStrategy import ValidationStrategy


class BRLCurrencyValidation(ValidationStrategy):
    """
    Estratégia de validação para valores monetários no formato brasileiro (BRL).

    Esta classe implementa a interface `ValidationStrategy` e utiliza expressões
    regulares para validar se uma string representa corretamente um valor monetário
    no padrão brasileiro, com símbolo "R$", separador de milhar com ponto (.) e
    separador decimal com vírgula (,).

    Attributes:
        pattern (Pattern): Expressão regular pré-compilada usada para validar
            o formato monetário brasileiro (BRL).
    """

    pattern = regex.compile(r"^R\$\s?\d{1,3}(\.\d{3})*(,\d{2})?$")

    def validate(self, text: str) -> bool:
        """
        Valida se o texto fornecido representa um valor monetário no formato BRL.

        Args:
            text (str): Texto que se deseja validar, por exemplo, "R$ 1.444,50".

        Returns:
            bool:
                - `True` se o texto corresponder ao formato BRL válido.
                - `False` caso contrário.
        """
        return bool(self.pattern.match(text))
