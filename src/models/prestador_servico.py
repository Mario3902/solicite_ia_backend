from . import db
from datetime import datetime

class PrestadorServico(db.Model):
    """Modelo para prestadores de serviços"""
    __tablename__ = 'prestadores_servicos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(100), nullable=False, index=True)
    descricao = db.Column(db.Text)
    localizacao = db.Column(db.String(200), nullable=False, index=True)
    contato = db.Column(db.String(100), nullable=False)
    whatsapp_contato = db.Column(db.String(20))
    imagem_url = db.Column(db.String(500))
    preco_minimo = db.Column(db.Numeric(10, 2))
    preco_maximo = db.Column(db.Numeric(10, 2))
    disponibilidade = db.Column(db.String(200))  # Ex: "Segunda a Sexta, 8h-18h"
    avaliacao_media = db.Column(db.Float, default=0.0)
    total_avaliacoes = db.Column(db.Integer, default=0)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    verificado = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<PrestadorServico {self.nome} - {self.especialidade}>'

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nome': self.nome,
            'especialidade': self.especialidade,
            'descricao': self.descricao,
            'localizacao': self.localizacao,
            'contato': self.contato,
            'whatsapp_contato': self.whatsapp_contato,
            'imagem_url': self.imagem_url,
            'preco_minimo': float(self.preco_minimo) if self.preco_minimo else None,
            'preco_maximo': float(self.preco_maximo) if self.preco_maximo else None,
            'disponibilidade': self.disponibilidade,
            'avaliacao_media': self.avaliacao_media,
            'total_avaliacoes': self.total_avaliacoes,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo,
            'verificado': self.verificado
        }
    
    @staticmethod
    def buscar_por_especialidade(especialidade, localizacao=None):
        """Busca prestadores por especialidade e opcionalmente por localização"""
        query = PrestadorServico.query.filter(
            PrestadorServico.especialidade.ilike(f'%{especialidade}%'),
            PrestadorServico.ativo == True
        )
        
        if localizacao:
            query = query.filter(PrestadorServico.localizacao.ilike(f'%{localizacao}%'))
        
        return query.order_by(PrestadorServico.avaliacao_media.desc()).all()
    
    @staticmethod
    def buscar_por_localizacao(localizacao):
        """Busca prestadores por localização"""
        return PrestadorServico.query.filter(
            PrestadorServico.localizacao.ilike(f'%{localizacao}%'),
            PrestadorServico.ativo == True
        ).order_by(PrestadorServico.avaliacao_media.desc()).all()
    
    def adicionar_avaliacao(self, nota):
        """Adiciona uma nova avaliação e recalcula a média"""
        if 1 <= nota <= 5:
            total_pontos = self.avaliacao_media * self.total_avaliacoes
            self.total_avaliacoes += 1
            self.avaliacao_media = (total_pontos + nota) / self.total_avaliacoes
            db.session.commit()
            return True
        return False

