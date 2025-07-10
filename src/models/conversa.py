from . import db
from datetime import datetime

class Conversa(db.Model):
    """Modelo para histórico de conversas"""
    __tablename__ = 'conversas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mensagem_usuario = db.Column(db.Text, nullable=False)
    resposta_ia = db.Column(db.Text)
    tipo_comando = db.Column(db.String(100), index=True)  # cadastro, busca, venda, etc.
    categoria = db.Column(db.String(100))  # prestador, produto, conexao, etc.
    intencao_detectada = db.Column(db.String(200))
    entidades_extraidas = db.Column(db.Text)  # JSON com entidades identificadas
    contexto_conversa = db.Column(db.Text)  # JSON com contexto da conversa
    imagem_recebida = db.Column(db.String(500))  # URL da imagem se enviada
    imagem_processada = db.Column(db.Boolean, default=False)
    resultado_processamento = db.Column(db.Text)  # JSON com resultado do processamento
    sucesso_comando = db.Column(db.Boolean, default=True)
    erro_detalhes = db.Column(db.Text)
    tempo_resposta_ms = db.Column(db.Integer)
    feedback_usuario = db.Column(db.String(20))  # positivo, negativo, neutro
    comentario_feedback = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sessao_id = db.Column(db.String(100))  # Para agrupar conversas da mesma sessão
    ip_origem = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    def __repr__(self):
        return f'<Conversa {self.usuario_id} - {self.tipo_comando}>'

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'mensagem_usuario': self.mensagem_usuario,
            'resposta_ia': self.resposta_ia,
            'tipo_comando': self.tipo_comando,
            'categoria': self.categoria,
            'intencao_detectada': self.intencao_detectada,
            'entidades_extraidas': self.entidades_extraidas,
            'contexto_conversa': self.contexto_conversa,
            'imagem_recebida': self.imagem_recebida,
            'imagem_processada': self.imagem_processada,
            'resultado_processamento': self.resultado_processamento,
            'sucesso_comando': self.sucesso_comando,
            'erro_detalhes': self.erro_detalhes,
            'tempo_resposta_ms': self.tempo_resposta_ms,
            'feedback_usuario': self.feedback_usuario,
            'comentario_feedback': self.comentario_feedback,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'sessao_id': self.sessao_id
        }
    
    @staticmethod
    def buscar_historico_usuario(usuario_id, limite=50):
        """Busca histórico de conversas de um usuário"""
        return Conversa.query.filter_by(usuario_id=usuario_id)\
                           .order_by(Conversa.timestamp.desc())\
                           .limit(limite).all()
    
    @staticmethod
    def buscar_por_tipo_comando(tipo_comando, data_inicio=None, data_fim=None):
        """Busca conversas por tipo de comando"""
        query = Conversa.query.filter_by(tipo_comando=tipo_comando)
        
        if data_inicio:
            query = query.filter(Conversa.timestamp >= data_inicio)
        
        if data_fim:
            query = query.filter(Conversa.timestamp <= data_fim)
        
        return query.order_by(Conversa.timestamp.desc()).all()
    
    @staticmethod
    def estatisticas_uso(data_inicio=None, data_fim=None):
        """Retorna estatísticas de uso do sistema"""
        query = Conversa.query
        
        if data_inicio:
            query = query.filter(Conversa.timestamp >= data_inicio)
        
        if data_fim:
            query = query.filter(Conversa.timestamp <= data_fim)
        
        conversas = query.all()
        
        if not conversas:
            return {}
        
        total_conversas = len(conversas)
        comandos_sucesso = len([c for c in conversas if c.sucesso_comando])
        
        # Conta tipos de comando
        tipos_comando = {}
        for conversa in conversas:
            if conversa.tipo_comando:
                tipos_comando[conversa.tipo_comando] = tipos_comando.get(conversa.tipo_comando, 0) + 1
        
        # Calcula tempo médio de resposta
        tempos_resposta = [c.tempo_resposta_ms for c in conversas if c.tempo_resposta_ms]
        tempo_medio = sum(tempos_resposta) / len(tempos_resposta) if tempos_resposta else 0
        
        # Conta feedback
        feedback_positivo = len([c for c in conversas if c.feedback_usuario == 'positivo'])
        feedback_negativo = len([c for c in conversas if c.feedback_usuario == 'negativo'])
        
        return {
            'total_conversas': total_conversas,
            'taxa_sucesso': (comandos_sucesso / total_conversas * 100) if total_conversas > 0 else 0,
            'tempo_medio_resposta_ms': round(tempo_medio, 2),
            'tipos_comando_mais_usados': sorted(tipos_comando.items(), key=lambda x: x[1], reverse=True)[:10],
            'feedback_positivo': feedback_positivo,
            'feedback_negativo': feedback_negativo,
            'taxa_satisfacao': (feedback_positivo / (feedback_positivo + feedback_negativo) * 100) if (feedback_positivo + feedback_negativo) > 0 else 0
        }
    
    def adicionar_feedback(self, feedback, comentario=None):
        """Adiciona feedback do usuário"""
        self.feedback_usuario = feedback
        if comentario:
            self.comentario_feedback = comentario
        db.session.commit()
    
    def marcar_erro(self, detalhes_erro):
        """Marca a conversa como erro"""
        self.sucesso_comando = False
        self.erro_detalhes = detalhes_erro
        db.session.commit()
    
    def definir_tempo_resposta(self, tempo_ms):
        """Define o tempo de resposta em milissegundos"""
        self.tempo_resposta_ms = tempo_ms
        db.session.commit()

