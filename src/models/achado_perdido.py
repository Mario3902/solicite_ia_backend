from . import db
from datetime import datetime, date

class AchadoPerdido(db.Model):
    """Modelo para achados e perdidos"""
    __tablename__ = 'achados_perdidos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, index=True)  # 'perdido' ou 'encontrado'
    categoria = db.Column(db.String(100), nullable=False, index=True)  # documento, animal, objeto, etc.
    objeto = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    cor = db.Column(db.String(50))
    tamanho = db.Column(db.String(50))
    caracteristicas_especiais = db.Column(db.Text)
    local = db.Column(db.String(300), nullable=False, index=True)
    local_detalhado = db.Column(db.Text)  # Descrição mais detalhada do local
    data_ocorrencia = db.Column(db.Date, nullable=False)
    hora_aproximada = db.Column(db.String(20))
    imagem_url = db.Column(db.String(500))
    imagens_adicionais = db.Column(db.Text)  # JSON com URLs das imagens
    recompensa = db.Column(db.Numeric(10, 2))
    contato_preferido = db.Column(db.String(20))  # whatsapp, telefone, email
    informacoes_contato = db.Column(db.String(200))
    urgente = db.Column(db.Boolean, default=False)
    documento_tipo = db.Column(db.String(100))  # Para documentos: BI, passaporte, carteira, etc.
    documento_numero = db.Column(db.String(100))  # Número parcial do documento (últimos dígitos)
    animal_especie = db.Column(db.String(50))  # Para animais: cão, gato, etc.
    animal_raca = db.Column(db.String(100))
    animal_nome = db.Column(db.String(100))
    animal_idade = db.Column(db.String(20))
    animal_castrado = db.Column(db.Boolean)
    animal_chip = db.Column(db.Boolean)
    visualizacoes = db.Column(db.Integer, default=0)
    compartilhamentos = db.Column(db.Integer, default=0)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolvido = db.Column(db.Boolean, default=False)
    data_resolucao = db.Column(db.DateTime)
    ativo = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<AchadoPerdido {self.tipo} - {self.objeto}>'

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'objeto': self.objeto,
            'descricao': self.descricao,
            'marca': self.marca,
            'modelo': self.modelo,
            'cor': self.cor,
            'tamanho': self.tamanho,
            'caracteristicas_especiais': self.caracteristicas_especiais,
            'local': self.local,
            'local_detalhado': self.local_detalhado,
            'data_ocorrencia': self.data_ocorrencia.isoformat() if self.data_ocorrencia else None,
            'hora_aproximada': self.hora_aproximada,
            'imagem_url': self.imagem_url,
            'imagens_adicionais': self.imagens_adicionais,
            'recompensa': float(self.recompensa) if self.recompensa else None,
            'contato_preferido': self.contato_preferido,
            'informacoes_contato': self.informacoes_contato,
            'urgente': self.urgente,
            'documento_tipo': self.documento_tipo,
            'documento_numero': self.documento_numero,
            'animal_especie': self.animal_especie,
            'animal_raca': self.animal_raca,
            'animal_nome': self.animal_nome,
            'animal_idade': self.animal_idade,
            'animal_castrado': self.animal_castrado,
            'animal_chip': self.animal_chip,
            'visualizacoes': self.visualizacoes,
            'compartilhamentos': self.compartilhamentos,
            'data_registro': self.data_registro.isoformat() if self.data_registro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'resolvido': self.resolvido,
            'data_resolucao': self.data_resolucao.isoformat() if self.data_resolucao else None,
            'ativo': self.ativo
        }
    
    @staticmethod
    def buscar_itens(tipo=None, categoria=None, objeto=None, local=None, data_inicio=None, data_fim=None):
        """Busca itens perdidos/encontrados com filtros opcionais"""
        query = AchadoPerdido.query.filter(
            AchadoPerdido.ativo == True,
            AchadoPerdido.resolvido == False
        )
        
        if tipo:
            query = query.filter(AchadoPerdido.tipo == tipo)
        
        if categoria:
            query = query.filter(AchadoPerdido.categoria.ilike(f'%{categoria}%'))
        
        if objeto:
            query = query.filter(
                db.or_(
                    AchadoPerdido.objeto.ilike(f'%{objeto}%'),
                    AchadoPerdido.descricao.ilike(f'%{objeto}%'),
                    AchadoPerdido.marca.ilike(f'%{objeto}%'),
                    AchadoPerdido.modelo.ilike(f'%{objeto}%')
                )
            )
        
        if local:
            query = query.filter(
                db.or_(
                    AchadoPerdido.local.ilike(f'%{local}%'),
                    AchadoPerdido.local_detalhado.ilike(f'%{local}%')
                )
            )
        
        if data_inicio:
            query = query.filter(AchadoPerdido.data_ocorrencia >= data_inicio)
        
        if data_fim:
            query = query.filter(AchadoPerdido.data_ocorrencia <= data_fim)
        
        return query.order_by(
            AchadoPerdido.urgente.desc(),
            AchadoPerdido.data_registro.desc()
        ).all()
    
    @staticmethod
    def buscar_correspondencias(item_perdido):
        """Busca possíveis correspondências para um item perdido"""
        if item_perdido.tipo != 'perdido':
            return []
        
        # Busca itens encontrados similares
        query = AchadoPerdido.query.filter(
            AchadoPerdido.tipo == 'encontrado',
            AchadoPerdido.ativo == True,
            AchadoPerdido.resolvido == False,
            AchadoPerdido.categoria == item_perdido.categoria
        )
        
        # Filtros por características similares
        if item_perdido.cor:
            query = query.filter(AchadoPerdido.cor.ilike(f'%{item_perdido.cor}%'))
        
        if item_perdido.marca:
            query = query.filter(AchadoPerdido.marca.ilike(f'%{item_perdido.marca}%'))
        
        if item_perdido.modelo:
            query = query.filter(AchadoPerdido.modelo.ilike(f'%{item_perdido.modelo}%'))
        
        # Filtro por proximidade de local (busca textual simples)
        if item_perdido.local:
            palavras_local = item_perdido.local.split()
            for palavra in palavras_local:
                if len(palavra) > 3:  # Ignora palavras muito pequenas
                    query = query.filter(AchadoPerdido.local.ilike(f'%{palavra}%'))
        
        return query.order_by(AchadoPerdido.data_registro.desc()).limit(10).all()
    
    def incrementar_visualizacao(self):
        """Incrementa o contador de visualizações"""
        self.visualizacoes += 1
        db.session.commit()
    
    def incrementar_compartilhamento(self):
        """Incrementa o contador de compartilhamentos"""
        self.compartilhamentos += 1
        db.session.commit()
    
    def marcar_como_resolvido(self):
        """Marca o item como resolvido"""
        self.resolvido = True
        self.data_resolucao = datetime.utcnow()
        db.session.commit()

