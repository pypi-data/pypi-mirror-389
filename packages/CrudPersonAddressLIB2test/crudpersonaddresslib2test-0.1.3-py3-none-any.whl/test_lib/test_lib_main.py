import pytest


# 1. Importe seus DTOs (Data Transfer Objects)
#    (Lembre-se da Solução 2 para isso funcionar!)
from model.dto import * 
from model.models import *

def test_person_create():
    """
    Testa a criação de PersonCreate apenas com nome (address_id é opcional).
    Seu model 'PersonBase' exige 'name', e 'PersonCreate' adiciona 'address_id' opcional.
    """
    person = PersonCreate(name="Matheus")
    
    assert person.name == "Matheus"
    assert person.address_id is None

def test_address_create():

    address = AddressCreate(
        logradouro = "Rua santosfutebolclube",
        numero = 7,
        estado = "RJ",
        cidade = "RJ",
        bairro = "Botafogo" 
    )

    assert address.numero == 7
    assert address.estado == "RJ"


def test_person_with_address():
    
    address = AddressCreate(
        logradouro = "Rua santosfutebolclube",
        numero = 11,
        estado = "SP",
        cidade = "Santos",
        bairro = "Baixada Santista" 
    )

    person = PersonCreate(name="Matheusss", address_id=1)

    assert address.cidade == "Santos"
    assert address.bairro == "Baixada Santista"
    
    assert person.name == "Matheusss"
    assert person.address_id == 1


def test_address_update():

    addressUpdate = AddressUpdate(numero = 999)

    assert addressUpdate.numero == 999
    assert addressUpdate.estado is None
    assert addressUpdate.logradouro is None
    assert addressUpdate.cidade is None