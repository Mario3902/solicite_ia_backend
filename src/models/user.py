from . import db
from datetime import datetime

class User(db.Model):
    """Modelo para usuários do sistema"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    prestadores = db.relationship('PrestadorServico', backref='usuario', lazy=True)
    produtos = db.relationship('Produto', backref='usuario', lazy=True)
    conexoes = db.relationship('ConexaoPessoal', backref='usuario', lazy=True)
    achados_perdidos = db.relationship('AchadoPerdido', backref='usuario', lazy=True)
    reclamacoes = db.relationship('Reclamacao', backref='usuario', lazy=True)
    conversas = db.relationship('Conversa', backref='usuario', lazy=True)

    def __repr__(self):
        return f'<User {self.whatsapp_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'whatsapp_id': self.whatsapp_id,
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
            'ativo': self.ativo
        }
    
    def atualizar_ultimo_acesso(self):
        """Atualiza o timestamp do último acesso"""
        self.ultimo_acesso = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def buscar_ou_criar(whatsapp_id, nome=None, telefone=None):
        """Busca usuário existente ou cria novo"""
        usuario = User.query.filter_by(whatsapp_id=whatsapp_id).first()
        
        if not usuario:
            usuario = User(
                whatsapp_id=whatsapp_id,
                nome=nome,
                telefone=telefone
            )
            db.session.add(usuario)
            db.session.commit()
        else:
            # Atualiza informações se fornecidas
            if nome and not usuario.nome:
                usuario.nome = nome
            if telefone and not usuario.telefone:
                usuario.telefone = telefone
            usuario.atualizar_ultimo_acesso()
        
        return usuario

