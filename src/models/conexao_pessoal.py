from . import db
from datetime import datetime

class ConexaoPessoal(db.Model):
    """Modelo para conexões pessoais e relacionamentos"""
    __tablename__ = 'conexoes_pessoais'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    idade = db.Column(db.Integer)
    genero = db.Column(db.String(20))  # masculino, feminino, outro
    estado_civil = db.Column(db.String(50))  # solteiro, casado, divorciado, viúvo
    interesse = db.Column(db.String(100), nullable=False)  # amizade, namoro, casamento, networking
    categoria_fisica = db.Column(db.String(100))  # atlético, magro, normal, plus size, etc.
    altura = db.Column(db.String(20))
    profissao = db.Column(db.String(100))
    escolaridade = db.Column(db.String(100))
    localizacao = db.Column(db.String(200), nullable=False, index=True)
    bio = db.Column(db.Text)
    interesses_hobbies = db.Column(db.Text)  # JSON com lista de interesses
    imagem_url = db.Column(db.String(500))
    imagens_adicionais = db.Column(db.Text)  # JSON com URLs das imagens
    religiao = db.Column(db.String(100))
    fumante = db.Column(db.Boolean)
    bebe = db.Column(db.Boolean)
    tem_filhos = db.Column(db.Boolean)
    quer_filhos = db.Column(db.Boolean)
    idade_minima_interesse = db.Column(db.Integer)
    idade_maxima_interesse = db.Column(db.Integer)
    distancia_maxima = db.Column(db.Integer)  # em km
    verificado = db.Column(db.Boolean, default=False)
    premium = db.Column(db.Boolean, default=False)
    visualizacoes = db.Column(db.Integer, default=0)
    likes_recebidos = db.Column(db.Integer, default=0)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<ConexaoPessoal {self.nome} - {self.interesse}>'

    def to_dict(self, incluir_contato=False):
        data = {
            'id': self.id,
            'nome': self.nome,
            'idade': self.idade,
            'genero': self.genero,
            'estado_civil': self.estado_civil,
            'interesse': self.interesse,
            'categoria_fisica': self.categoria_fisica,
            'altura': self.altura,
            'profissao': self.profissao,
            'escolaridade': self.escolaridade,
            'localizacao': self.localizacao,
            'bio': self.bio,
            'interesses_hobbies': self.interesses_hobbies,
            'imagem_url': self.imagem_url,
            'religiao': self.religiao,
            'fumante': self.fumante,
            'bebe': self.bebe,
            'tem_filhos': self.tem_filhos,
            'quer_filhos': self.quer_filhos,
            'verificado': self.verificado,
            'premium': self.premium,
            'visualizacoes': self.visualizacoes,
            'likes_recebidos': self.likes_recebidos,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
            'ativo': self.ativo
        }
        
        # Só inclui informações de contato se autorizado
        if incluir_contato:
            data['usuario_id'] = self.usuario_id
        
        return data
    
    @staticmethod
    def buscar_conexoes(interesse=None, genero=None, idade_min=None, idade_max=None, localizacao=None, categoria_fisica=None):
        """Busca conexões com filtros opcionais"""
        query = ConexaoPessoal.query.filter(ConexaoPessoal.ativo == True)
        
        if interesse:
            query = query.filter(ConexaoPessoal.interesse.ilike(f'%{interesse}%'))
        
        if genero:
            query = query.filter(ConexaoPessoal.genero.ilike(f'%{genero}%'))
        
        if idade_min:
            query = query.filter(ConexaoPessoal.idade >= idade_min)
        
        if idade_max:
            query = query.filter(ConexaoPessoal.idade <= idade_max)
        
        if localizacao:
            query = query.filter(ConexaoPessoal.localizacao.ilike(f'%{localizacao}%'))
        
        if categoria_fisica:
            query = query.filter(ConexaoPessoal.categoria_fisica.ilike(f'%{categoria_fisica}%'))
        
        return query.order_by(ConexaoPessoal.ultimo_acesso.desc()).all()
    
    def incrementar_visualizacao(self):
        """Incrementa o contador de visualizações"""
        self.visualizacoes += 1
        db.session.commit()
    
    def incrementar_like(self):
        """Incrementa o contador de likes"""
        self.likes_recebidos += 1
        db.session.commit()
    
    def atualizar_ultimo_acesso(self):
        """Atualiza o timestamp do último acesso"""
        self.ultimo_acesso = datetime.utcnow()
        db.session.commit()
    
    def compativel_com(self, outra_conexao):
        """Verifica compatibilidade básica entre duas conexões"""
        # Verifica se as idades estão dentro dos critérios
        if self.idade_minima_interesse and outra_conexao.idade < self.idade_minima_interesse:
            return False
        if self.idade_maxima_interesse and outra_conexao.idade > self.idade_maxima_interesse:
            return False
        
        # Verifica interesse mútuo
        interesses_compativeis = {
            'amizade': ['amizade', 'networking'],
            'namoro': ['namoro', 'casamento'],
            'casamento': ['namoro', 'casamento'],
            'networking': ['networking', 'amizade']
        }
        
        return outra_conexao.interesse in interesses_compativeis.get(self.interesse, [])

