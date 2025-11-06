from abc import ABC, abstractmethod


class ValidationStrategy(ABC):
    """
    Define a interface abstrata para estratégias de validação de texto.

    O padrão de projeto Strategy permite que múltiplas formas de validação
    (como e-mail, CPF, CNPJ, moeda, hora, etc.) possam ser trocadas
    dinamicamente sem modificar o código cliente.
    """

    @abstractmethod
    def validate(self, text: str) -> bool:
        """
        Método abstrato para validação de texto.

        Args:
            text (str): Texto a ser validado.

        Returns:
            bool: Retorna True se o texto for válido de acordo com a
            estratégia; caso contrário, retorna False.
        """
        pass
