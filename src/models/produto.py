from . import db
from datetime import datetime

class Produto(db.Model):
    """Modelo para produtos do marketplace"""
    __tablename__ = 'produtos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome = db.Column(db.String(200), nullable=False, index=True)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(100), nullable=False, index=True)
    subcategoria = db.Column(db.String(100))
    condicao = db.Column(db.String(50))  # novo, usado, seminovo
    localizacao = db.Column(db.String(200), nullable=False, index=True)
    imagem_url = db.Column(db.String(500))
    imagens_adicionais = db.Column(db.Text)  # JSON com URLs das imagens
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    cor = db.Column(db.String(50))
    tamanho = db.Column(db.String(50))
    peso = db.Column(db.String(50))
    dimensoes = db.Column(db.String(100))
    aceita_troca = db.Column(db.Boolean, default=False)
    negociavel = db.Column(db.Boolean, default=True)
    entrega_disponivel = db.Column(db.Boolean, default=False)
    custo_entrega = db.Column(db.Numeric(10, 2))
    visualizacoes = db.Column(db.Integer, default=0)
    favoritos = db.Column(db.Integer, default=0)
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    vendido = db.Column(db.Boolean, default=False)
    promovido = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Produto {self.nome} - {self.preco}>'

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': float(self.preco) if self.preco else None,
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'condicao': self.condicao,
            'localizacao': self.localizacao,
            'imagem_url': self.imagem_url,
            'imagens_adicionais': self.imagens_adicionais,
            'marca': self.marca,
            'modelo': self.modelo,
            'cor': self.cor,
            'tamanho': self.tamanho,
            'peso': self.peso,
            'dimensoes': self.dimensoes,
            'aceita_troca': self.aceita_troca,
            'negociavel': self.negociavel,
            'entrega_disponivel': self.entrega_disponivel,
            'custo_entrega': float(self.custo_entrega) if self.custo_entrega else None,
            'visualizacoes': self.visualizacoes,
            'favoritos': self.favoritos,
            'data_publicacao': self.data_publicacao.isoformat() if self.data_publicacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'ativo': self.ativo,
            'vendido': self.vendido,
            'promovido': self.promovido
        }
    
    @staticmethod
    def buscar_produtos(termo=None, categoria=None, localizacao=None, preco_min=None, preco_max=None, condicao=None):
        """Busca produtos com filtros opcionais"""
        query = Produto.query.filter(
            Produto.ativo == True,
            Produto.vendido == False
        )
        
        if termo:
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(f'%{termo}%'),
                    Produto.descricao.ilike(f'%{termo}%'),
                    Produto.marca.ilike(f'%{termo}%'),
                    Produto.modelo.ilike(f'%{termo}%')
                )
            )
        
        if categoria:
            query = query.filter(Produto.categoria.ilike(f'%{categoria}%'))
        
        if localizacao:
            query = query.filter(Produto.localizacao.ilike(f'%{localizacao}%'))
        
        if preco_min:
            query = query.filter(Produto.preco >= preco_min)
        
        if preco_max:
            query = query.filter(Produto.preco <= preco_max)
        
        if condicao:
            query = query.filter(Produto.condicao.ilike(f'%{condicao}%'))
        
        return query.order_by(Produto.data_publicacao.desc()).all()
    
    def incrementar_visualizacao(self):
        """Incrementa o contador de visualizações"""
        self.visualizacoes += 1
        db.session.commit()
    
    def incrementar_favorito(self):
        """Incrementa o contador de favoritos"""
        self.favoritos += 1
        db.session.commit()
    
    def marcar_como_vendido(self):
        """Marca o produto como vendido"""
        self.vendido = True
        self.ativo = False
        db.session.commit()

