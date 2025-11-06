from validator_regex.strategies.ValidationStrategy import ValidationStrategy


class ValidatorContext:
    """
    Define o contexto para execução de estratégias de validação.

    A ideia é permitir que diferentes tipos de validação (e-mail, CPF,
    CNPJ, hora, etc.) possam ser alternados em tempo de execução sem
    alterar a estrutura do código cliente.

    Args:
        strategy (ValidationStrategy): Estratégia de validação que será
            utilizada para processar o texto.

    Attributes:
        _strategy (ValidationStrategy): Armazena a estratégia de validação
            atualmente configurada no contexto.
    """

    def __init__(self, strategy: ValidationStrategy) -> None:
        """
        Inicializa o contexto com uma estratégia de validação específica.

        Args:
            strategy (ValidationStrategy): Estratégia de validação inicial
                a ser utilizada.
        """
        self._strategy = strategy

    def set_strategy(self, strategy: ValidationStrategy) -> None:
        """
        Altera dinamicamente a estratégia de validação utilizada.

        Args:
            strategy (ValidationStrategy): Nova estratégia de validação
                a ser aplicada.
        """
        self._strategy = strategy

    def validate(self, text: str) -> bool:
        """
        Executa a validação do texto utilizando a estratégia atual.

        Args:
            text (str): Texto a ser validado.

        Returns:
            bool: Retorna True se o texto for válido de acordo com a
            estratégia; caso contrário, retorna False.
        """
        return self._strategy.validate(text)
