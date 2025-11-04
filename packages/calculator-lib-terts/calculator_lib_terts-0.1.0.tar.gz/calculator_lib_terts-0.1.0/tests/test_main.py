from fastapi.testclient import TestClient
from app.main import app

import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

client = TestClient(app)

def test_add():
    response = client.post("/add", json={"a": 10, "b": 5})
    assert response.status_code == 200
    assert response.json() == {"result": 15}

def test_subtract():
    response = client.post("/subtract", json={"a": 10, "b": 5})
    assert response.status_code == 200
    assert response.json() == {"result": 5}

def test_multiply():
    response = client.post("/multiply", json={"a": 10, "b": 5})
    assert response.status_code == 200
    assert response.json() == {"result": 50}

def test_divide():
    response = client.post("/divide", json={"a": 10, "b": 5})
    assert response.status_code == 200
    assert response.json() == {"result": 2}

def test_divide_by_zero():
    response = client.post("/divide", json={"a": 10, "b": 0})
    assert response.status_code == 400
    assert response.json()["detail"] == "Divisão por zero não é permitida."
