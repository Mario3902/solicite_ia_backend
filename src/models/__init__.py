from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Importa todos os modelos
from .user import User
from .prestador_servico import PrestadorServico
from .produto import Produto
from .conexao_pessoal import ConexaoPessoal
from .achado_perdido import AchadoPerdido
from .reclamacao import Reclamacao
from .conversa import Conversa

__all__ = [
    'db',
    'User',
    'PrestadorServico', 
    'Produto',
    'ConexaoPessoal',
    'AchadoPerdido',
    'Reclamacao',
    'Conversa'
]

