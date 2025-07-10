from . import db
from datetime import datetime

class Reclamacao(db.Model):
    """Modelo para reclamações e denúncias"""
    __tablename__ = 'reclamacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa = db.Column(db.String(200), nullable=False, index=True)
    categoria_empresa = db.Column(db.String(100))  # telecomunicações, banco, varejo, etc.
    tipo_reclamacao = db.Column(db.String(100), nullable=False)  # atendimento, produto, serviço, cobrança
    motivo = db.Column(db.String(300), nullable=False)
    detalhes = db.Column(db.Text, nullable=False)
    valor_envolvido = db.Column(db.Numeric(10, 2))
    numero_protocolo = db.Column(db.String(100))  # Protocolo da empresa
    data_problema = db.Column(db.Date)
    local_problema = db.Column(db.String(200))
    evidencias = db.Column(db.Text)  # JSON com URLs de imagens/documentos
    anonimo = db.Column(db.Boolean, default=False)
    urgente = db.Column(db.Boolean, default=False)
    busca_solucao = db.Column(db.Boolean, default=True)  # Se busca solução ou só quer denunciar
    aceita_contato_empresa = db.Column(db.Boolean, default=True)
    data_reclamacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pendente', index=True)  # pendente, em_andamento, resolvida, rejeitada
    prioridade = db.Column(db.String(20), default='normal')  # baixa, normal, alta, crítica
    canal_origem = db.Column(db.String(50), default='whatsapp')
    resposta_empresa = db.Column(db.Text)
    data_resposta = db.Column(db.DateTime)
    usuario_resposta = db.Column(db.String(200))  # Nome do responsável da empresa
    satisfacao_resposta = db.Column(db.Integer)  # 1-5 estrelas
    comentario_satisfacao = db.Column(db.Text)
    data_resolucao = db.Column(db.DateTime)
    tempo_resolucao_horas = db.Column(db.Integer)
    visualizacoes = db.Column(db.Integer, default=0)
    compartilhamentos = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)  # Apoio de outros usuários
    seguindo = db.Column(db.Integer, default=0)  # Usuários acompanhando o caso
    publica = db.Column(db.Boolean, default=True)  # Se aparece em listagens públicas
    notificar_atualizacoes = db.Column(db.Boolean, default=True)
    ativa = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Reclamacao {self.empresa} - {self.motivo}>'

    def to_dict(self, incluir_dados_usuario=False):
        data = {
            'id': self.id,
            'empresa': self.empresa,
            'categoria_empresa': self.categoria_empresa,
            'tipo_reclamacao': self.tipo_reclamacao,
            'motivo': self.motivo,
            'detalhes': self.detalhes,
            'valor_envolvido': float(self.valor_envolvido) if self.valor_envolvido else None,
            'numero_protocolo': self.numero_protocolo,
            'data_problema': self.data_problema.isoformat() if self.data_problema else None,
            'local_problema': self.local_problema,
            'evidencias': self.evidencias,
            'anonimo': self.anonimo,
            'urgente': self.urgente,
            'busca_solucao': self.busca_solucao,
            'data_reclamacao': self.data_reclamacao.isoformat() if self.data_reclamacao else None,
            'status': self.status,
            'prioridade': self.prioridade,
            'canal_origem': self.canal_origem,
            'resposta_empresa': self.resposta_empresa,
            'data_resposta': self.data_resposta.isoformat() if self.data_resposta else None,
            'usuario_resposta': self.usuario_resposta,
            'satisfacao_resposta': self.satisfacao_resposta,
            'comentario_satisfacao': self.comentario_satisfacao,
            'data_resolucao': self.data_resolucao.isoformat() if self.data_resolucao else None,
            'tempo_resolucao_horas': self.tempo_resolucao_horas,
            'visualizacoes': self.visualizacoes,
            'compartilhamentos': self.compartilhamentos,
            'likes': self.likes,
            'seguindo': self.seguindo,
            'publica': self.publica,
            'ativa': self.ativa
        }
        
        # Só inclui dados do usuário se não for anônimo e autorizado
        if incluir_dados_usuario and not self.anonimo:
            data['usuario_id'] = self.usuario_id
        
        return data
    
    @staticmethod
    def buscar_reclamacoes(empresa=None, tipo=None, status=None, data_inicio=None, data_fim=None, apenas_publicas=True):
        """Busca reclamações com filtros opcionais"""
        query = Reclamacao.query.filter(Reclamacao.ativa == True)
        
        if apenas_publicas:
            query = query.filter(Reclamacao.publica == True)
        
        if empresa:
            query = query.filter(Reclamacao.empresa.ilike(f'%{empresa}%'))
        
        if tipo:
            query = query.filter(Reclamacao.tipo_reclamacao.ilike(f'%{tipo}%'))
        
        if status:
            query = query.filter(Reclamacao.status == status)
        
        if data_inicio:
            query = query.filter(Reclamacao.data_reclamacao >= data_inicio)
        
        if data_fim:
            query = query.filter(Reclamacao.data_reclamacao <= data_fim)
        
        return query.order_by(
            Reclamacao.urgente.desc(),
            Reclamacao.data_reclamacao.desc()
        ).all()
    
    @staticmethod
    def estatisticas_empresa(empresa):
        """Retorna estatísticas de reclamações de uma empresa"""
        reclamacoes = Reclamacao.query.filter(
            Reclamacao.empresa.ilike(f'%{empresa}%'),
            Reclamacao.ativa == True,
            Reclamacao.publica == True
        ).all()
        
        if not reclamacoes:
            return None
        
        total = len(reclamacoes)
        resolvidas = len([r for r in reclamacoes if r.status == 'resolvida'])
        pendentes = len([r for r in reclamacoes if r.status == 'pendente'])
        
        # Calcula tempo médio de resolução
        tempos_resolucao = [r.tempo_resolucao_horas for r in reclamacoes if r.tempo_resolucao_horas]
        tempo_medio = sum(tempos_resolucao) / len(tempos_resolucao) if tempos_resolucao else 0
        
        # Calcula satisfação média
        satisfacoes = [r.satisfacao_resposta for r in reclamacoes if r.satisfacao_resposta]
        satisfacao_media = sum(satisfacoes) / len(satisfacoes) if satisfacoes else 0
        
        return {
            'empresa': empresa,
            'total_reclamacoes': total,
            'resolvidas': resolvidas,
            'pendentes': pendentes,
            'taxa_resolucao': (resolvidas / total * 100) if total > 0 else 0,
            'tempo_medio_resolucao_horas': round(tempo_medio, 1),
            'satisfacao_media': round(satisfacao_media, 1),
            'total_likes': sum([r.likes for r in reclamacoes]),
            'total_visualizacoes': sum([r.visualizacoes for r in reclamacoes])
        }
    
    def incrementar_visualizacao(self):
        """Incrementa o contador de visualizações"""
        self.visualizacoes += 1
        db.session.commit()
    
    def incrementar_like(self):
        """Incrementa o contador de likes (apoio)"""
        self.likes += 1
        db.session.commit()
    
    def adicionar_resposta(self, resposta, usuario_resposta=None):
        """Adiciona resposta da empresa"""
        self.resposta_empresa = resposta
        self.data_resposta = datetime.utcnow()
        self.usuario_resposta = usuario_resposta
        self.status = 'em_andamento'
        db.session.commit()
    
    def marcar_como_resolvida(self, satisfacao=None, comentario=None):
        """Marca a reclamação como resolvida"""
        self.status = 'resolvida'
        self.data_resolucao = datetime.utcnow()
        
        # Calcula tempo de resolução
        if self.data_reclamacao:
            delta = self.data_resolucao - self.data_reclamacao
            self.tempo_resolucao_horas = int(delta.total_seconds() / 3600)
        
        if satisfacao:
            self.satisfacao_resposta = satisfacao
        
        if comentario:
            self.comentario_satisfacao = comentario
        
        db.session.commit()

