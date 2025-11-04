from pydantic import BaseModel

class OperationRequest(BaseModel):
    """
    Modelo de dados para representar uma requisição de operação matemática.

    Atributos:
        a (float): O primeiro número da operação.
        b (float): O segundo número da operação.
    """
    a: float
    b: float

class OperationResponse(BaseModel):
    """
    Modelo de dados para representar a resposta de uma operação matemática.

    Atributos:
        result (float): O resultado da operação matemática realizada.
    """
    result: float
  