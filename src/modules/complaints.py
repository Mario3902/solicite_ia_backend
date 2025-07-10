from typing import Dict, Any, List
from flask import current_app
from src.models import db, User, Reclamacao, Conversa
import json
import re
from datetime import datetime, date

class ComplaintsModule:
    """Módulo para gerenciar reclamações e denúncias"""
    
    def __init__(self):
        self.company_categories = {
            'telecomunicacoes': ['unitel', 'movicel', 'africell', 'operadora', 'telefone', 'internet'],
            'banco': ['bai', 'bic', 'banco', 'bancario', 'cartao', 'credito', 'conta'],
            'energia': ['ende', 'energia', 'eletricidade', 'luz', 'corrente'],
            'agua': ['epal', 'agua', 'saneamento', 'torneira', 'canos'],
            'transporte': ['transporte', 'taxi', 'autocarro', 'onibus', 'mototaxi'],
            'educacao': ['escola', 'universidade', 'faculdade', 'ensino', 'educacao'],
            'saude': ['hospital', 'clinica', 'medico', 'saude', 'medicamento'],
            'comercio': ['loja', 'supermercado', 'shopping', 'comercio', 'vendas'],
            'servicos': ['servico', 'atendimento', 'empresa', 'negocio'],
            'governo': ['governo', 'ministerio', 'municipal', 'estado', 'publico']
        }
        
        self.complaint_types = {
            'atendimento': ['atendimento', 'mau atendimento', 'grosseria', 'descortesia'],
            'produto': ['produto', 'defeito', 'qualidade', 'mercadoria'],
            'servico': ['servico', 'prestacao', 'execucao', 'trabalho'],
            'cobranca': ['cobranca', 'fatura', 'conta', 'preco', 'valor'],
            'entrega': ['entrega', 'atraso', 'prazo', 'demora'],
            'contrato': ['contrato', 'acordo', 'clausula', 'termo'],
            'discriminacao': ['discriminacao', 'preconceito', 'racismo', 'machismo'],
            'fraude': ['fraude', 'golpe', 'enganacao', 'roubo']
        }
        
        self.urgency_keywords = ['urgente', 'grave', 'serio', 'importante', 'critico']
    
    def process_message(self, nlp_result: Dict[str, Any], user: User, conversa: Conversa) -> Dict[str, Any]:
        """Processa mensagem relacionada a reclamações"""
        try:
            text = nlp_result.get('text', '')
            
            # Extrai informações da reclamação
            complaint_info = self._extract_complaint_info(text, nlp_result.get('entities', {}))
            
            if not complaint_info.get('empresa'):
                return self._request_company_info(user, conversa)
            
            if not complaint_info.get('motivo'):
                return self._request_complaint_reason(complaint_info, user, conversa)
            
            # Solicita detalhes completos
            return self._request_complaint_details(complaint_info, user, conversa)
                
        except Exception as e:
            current_app.logger.error(f'Erro no módulo de reclamações: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao processar reclamação.',
                'error': str(e)
            }
    
    def _extract_complaint_info(self, text: str, entities: Dict) -> Dict[str, Any]:
        """Extrai informações da reclamação"""
        info = {}
        
        # Extrai empresa
        info['empresa'] = self._extract_company(text)
        
        # Extrai categoria da empresa
        info['categoria_empresa'] = self._extract_company_category(text)
        
        # Extrai tipo de reclamação
        info['tipo_reclamacao'] = self._extract_complaint_type(text)
        
        # Extrai motivo
        info['motivo'] = self._extract_complaint_reason(text)
        
        # Extrai valor envolvido
        prices = entities.get('preco', [])
        if prices:
            info['valor_envolvido'] = self._parse_price(prices[0])
        
        # Verifica se é urgente
        info['urgente'] = self._is_urgent(text)
        
        # Verifica se quer anonimato
        info['anonimo'] = self._wants_anonymity(text)
        
        return info
    
    def _extract_company(self, text: str) -> str:
        """Extrai nome da empresa"""
        # Padrões para extrair empresa
        patterns = [
            r'reclamar?\s+(?:da|do|contra)?\s*([^,\.]+?)(?:\s+por|\s+pelo|,|\.|$)',
            r'problema\s+com\s+(?:a|o)?\s*([^,\.]+?)(?:\s+por|,|\.|$)',
            r'empresa\s*:?\s*([^,\.]+?)(?:,|\.|$)',
            r'(?:unitel|movicel|africell|bai|bic|ende|epal)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if pattern.endswith(r'\b'):  # Empresas específicas
                    return match.group(0)
                else:
                    company = match.group(1).strip()
                    # Remove palavras desnecessárias
                    company = re.sub(r'\b(a|o|da|do|com|por|pelo)\b', '', company, flags=re.IGNORECASE).strip()
                    if len(company) > 2:
                        return company
        
        return None
    
    def _extract_company_category(self, text: str) -> str:
        """Extrai categoria da empresa"""
        text_lower = text.lower()
        
        for category, keywords in self.company_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return 'servicos'  # Padrão
    
    def _extract_complaint_type(self, text: str) -> str:
        """Extrai tipo de reclamação"""
        text_lower = text.lower()
        
        for comp_type, keywords in self.complaint_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return comp_type
        
        return 'servico'  # Padrão
    
    def _extract_complaint_reason(self, text: str) -> str:
        """Extrai motivo da reclamação"""
        # Padrões para extrair motivo
        patterns = [
            r'por\s+(.+?)(?:,|\.|$)',
            r'motivo\s*:?\s*(.+?)(?:,|\.|$)',
            r'porque\s+(.+?)(?:,|\.|$)',
            r'problema\s+(?:com|de|da|do)\s+[^,]+?\s+(.+?)(?:,|\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reason = match.group(1).strip()
                if len(reason) > 5:
                    return reason
        
        return None
    
    def _parse_price(self, price_str: str) -> float:
        """Converte string de preço para float"""
        try:
            price_clean = re.sub(r'[^\d,.]', '', price_str)
            if ',' in price_clean and '.' not in price_clean:
                price_clean = price_clean.replace(',', '.')
            elif ',' in price_clean and '.' in price_clean:
                price_clean = price_clean.replace('.', '').replace(',', '.')
            return float(price_clean)
        except:
            return 0.0
    
    def _is_urgent(self, text: str) -> bool:
        """Verifica se é urgente"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.urgency_keywords)
    
    def _wants_anonymity(self, text: str) -> bool:
        """Verifica se quer anonimato"""
        anonymity_keywords = ['anonimo', 'anonima', 'sem nome', 'confidencial', 'secreto']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in anonymity_keywords)
    
    def _request_company_info(self, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita informações da empresa"""
        text = "📢 *REGISTRAR RECLAMAÇÃO*\n\n"
        text += "Qual empresa você quer reclamar?\n\n"
        text += "*Exemplos:*\n"
        text += "• Unitel\n"
        text += "• BAI (Banco)\n"
        text += "• ENDE (Energia)\n"
        text += "• Shoprite\n"
        text += "• Hospital Américo Boavida\n\n"
        text += "Digite o nome da empresa:"
        
        # Salva contexto
        temp_data = {
            'step': 'collecting_company'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        return {
            'success': True,
            'text': text,
            'requires_followup': True
        }
    
    def _request_complaint_reason(self, complaint_info: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita motivo da reclamação"""
        empresa = complaint_info.get('empresa', 'empresa')
        
        text = f"📢 *Reclamação: {empresa}*\n\n"
        text += "Qual o motivo da sua reclamação?\n\n"
        text += "*Tipos comuns:*\n"
        text += "• Mau atendimento\n"
        text += "• Cobrança indevida\n"
        text += "• Produto com defeito\n"
        text += "• Serviço não prestado\n"
        text += "• Atraso na entrega\n"
        text += "• Discriminação\n\n"
        text += "Descreva brevemente o problema:"
        
        # Salva contexto
        temp_data = {
            'complaint_info': complaint_info,
            'step': 'collecting_reason'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        return {
            'success': True,
            'text': text,
            'requires_followup': True
        }
    
    def _request_complaint_details(self, complaint_info: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita detalhes completos da reclamação"""
        empresa = complaint_info.get('empresa', 'empresa')
        motivo = complaint_info.get('motivo', 'problema')
        
        text = f"📢 *Reclamação: {empresa}*\n"
        text += f"🔍 *Motivo:* {motivo}\n\n"
        text += "Para registrar sua reclamação, preciso de mais detalhes:\n\n"
        text += "📝 *Descrição completa* do problema\n"
        text += "📅 *Quando* aconteceu\n"
        text += "📍 *Onde* aconteceu (se aplicável)\n"
        text += "💰 *Valor envolvido* (se houver)\n"
        text += "📋 *Número de protocolo* (se tiver)\n"
        text += "📸 *Evidências* (fotos, documentos)\n"
        text += "🔒 *Quer anonimato?*\n"
        text += "🎯 *Busca solução* ou só quer denunciar?\n\n"
        text += "*Exemplo:*\n"
        text += "Fui cobrado 50.000kz a mais na fatura\n"
        text += "Aconteceu em dezembro de 2024\n"
        text += "Protocolo: 123456\n"
        text += "Quero solução e reembolso\n"
        text += "Pode divulgar meu nome"
        
        # Salva contexto
        temp_data = {
            'complaint_info': complaint_info,
            'step': 'collecting_details'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        buttons = [
            {'id': 'anonymous_yes', 'title': '🔒 Anônimo'},
            {'id': 'anonymous_no', 'title': '👤 Com Nome'},
            {'id': 'urgent_yes', 'title': '🚨 Urgente'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons,
            'requires_followup': True
        }
    
    def search_complaints(self, search_criteria: Dict) -> List[Reclamacao]:
        """Busca reclamações baseado nos critérios"""
        query = Reclamacao.query.filter(
            Reclamacao.ativa == True,
            Reclamacao.publica == True
        )
        
        # Aplica filtros
        if search_criteria.get('empresa'):
            query = query.filter(Reclamacao.empresa.ilike(f'%{search_criteria["empresa"]}%'))
        
        if search_criteria.get('tipo'):
            query = query.filter(Reclamacao.tipo_reclamacao == search_criteria['tipo'])
        
        if search_criteria.get('status'):
            query = query.filter(Reclamacao.status == search_criteria['status'])
        
        if search_criteria.get('categoria'):
            query = query.filter(Reclamacao.categoria_empresa == search_criteria['categoria'])
        
        return query.order_by(
            Reclamacao.urgente.desc(),
            Reclamacao.data_reclamacao.desc()
        ).limit(20).all()
    
    def get_company_statistics(self, empresa: str) -> Dict[str, Any]:
        """Retorna estatísticas de uma empresa"""
        return Reclamacao.estatisticas_empresa(empresa)
    
    def complete_complaint_registration(self, complaint_data: Dict, user: User) -> Dict[str, Any]:
        """Completa o registro da reclamação"""
        try:
            complaint = Reclamacao(
                usuario_id=user.id,
                empresa=complaint_data['empresa'],
                categoria_empresa=complaint_data.get('categoria_empresa', 'servicos'),
                tipo_reclamacao=complaint_data.get('tipo_reclamacao', 'servico'),
                motivo=complaint_data['motivo'],
                detalhes=complaint_data.get('detalhes', ''),
                valor_envolvido=complaint_data.get('valor_envolvido'),
                numero_protocolo=complaint_data.get('numero_protocolo'),
                data_problema=complaint_data.get('data_problema'),
                local_problema=complaint_data.get('local_problema'),
                evidencias=complaint_data.get('evidencias'),
                anonimo=complaint_data.get('anonimo', False),
                urgente=complaint_data.get('urgente', False),
                busca_solucao=complaint_data.get('busca_solucao', True),
                aceita_contato_empresa=complaint_data.get('aceita_contato_empresa', True),
                publica=complaint_data.get('publica', True),
                prioridade='alta' if complaint_data.get('urgente') else 'normal'
            )
            
            db.session.add(complaint)
            db.session.commit()
            
            # Gera número de protocolo interno
            protocol_number = f"SOL{complaint.id:06d}"
            
            text = f"✅ *Reclamação registrada com sucesso!*\n\n"
            text += f"📋 *Protocolo:* {protocol_number}\n"
            text += f"🏢 *Empresa:* {complaint.empresa}\n"
            text += f"🔍 *Motivo:* {complaint.motivo}\n"
            text += f"📅 *Data:* {complaint.data_reclamacao.strftime('%d/%m/%Y %H:%M')}\n"
            text += f"📊 *Status:* {complaint.status.title()}\n\n"
            
            if complaint.anonimo:
                text += "🔒 *Reclamação anônima* - seus dados não serão divulgados\n\n"
            
            if complaint.urgente:
                text += "🚨 *Marcada como urgente* - será priorizada\n\n"
            
            text += "*Próximos passos:*\n"
            text += "• Sua reclamação será analisada\n"
            text += "• A empresa será notificada\n"
            text += "• Você receberá atualizações sobre o andamento\n"
            text += "• Pode acompanhar o status a qualquer momento\n\n"
            text += f"💡 *Guarde o protocolo:* {protocol_number}"
            
            # Busca estatísticas da empresa
            stats = self.get_company_statistics(complaint.empresa)
            if stats:
                text += f"\n\n📊 *Estatísticas da {complaint.empresa}:*\n"
                text += f"• Total de reclamações: {stats['total_reclamacoes']}\n"
                text += f"• Taxa de resolução: {stats['taxa_resolucao']:.1f}%\n"
                if stats['tempo_medio_resolucao_horas'] > 0:
                    text += f"• Tempo médio de resolução: {stats['tempo_medio_resolucao_horas']:.1f}h\n"
            
            return {
                'success': True,
                'text': text,
                'protocol': protocol_number,
                'complaint_id': complaint.id
            }
            
        except Exception as e:
            current_app.logger.error(f'Erro ao registrar reclamação: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao finalizar reclamação. Tente novamente.',
                'error': str(e)
            }
    
    def format_complaints_list(self, complaints: List[Reclamacao], title: str = "Reclamações") -> Dict[str, Any]:
        """Formata lista de reclamações"""
        if not complaints:
            return {
                'success': True,
                'text': f"📋 *{title}*\n\nNenhuma reclamação encontrada.",
                'buttons': [
                    {'id': 'new_complaint', 'title': '📢 Nova Reclamação'},
                    {'id': 'search_company', 'title': '🔍 Buscar Empresa'}
                ]
            }
        
        text = f"📋 *{title}* ({len(complaints)} encontrada(s)):\n\n"
        
        list_items = []
        
        for i, complaint in enumerate(complaints, 1):
            # Incrementa visualização
            complaint.incrementar_visualizacao()
            
            # Status emoji
            status_emoji = {
                'pendente': '⏳',
                'em_andamento': '🔄',
                'resolvida': '✅',
                'rejeitada': '❌'
            }.get(complaint.status, '📋')
            
            # Monta texto da reclamação
            comp_text = f"*{complaint.empresa}*\n"
            comp_text += f"🔍 {complaint.motivo}\n"
            comp_text += f"{status_emoji} {complaint.status.replace('_', ' ').title()}\n"
            comp_text += f"📅 {complaint.data_reclamacao.strftime('%d/%m/%Y')}\n"
            
            if complaint.urgente:
                comp_text += "🚨 Urgente\n"
            
            if complaint.anonimo:
                comp_text += "🔒 Anônimo\n"
            
            if complaint.valor_envolvido:
                comp_text += f"💰 {complaint.valor_envolvido:,.0f} kz\n"
            
            comp_text += f"👁️ {complaint.visualizacoes} visualizações"
            
            if complaint.likes > 0:
                comp_text += f" | 👍 {complaint.likes} apoios"
            
            text += f"{i}. {comp_text}\n\n"
            
            # Adiciona à lista interativa
            list_items.append({
                'id': f'complaint_{complaint.id}',
                'title': f"{complaint.empresa} - {complaint.motivo[:30]}...",
                'description': f"{status_emoji} {complaint.status} | 📅 {complaint.data_reclamacao.strftime('%d/%m')}"
            })
        
        text += "💡 *Dica:* Selecione uma reclamação para ver detalhes completos."
        
        buttons = [
            {'id': 'new_complaint', 'title': '📢 Nova Reclamação'},
            {'id': 'filter_complaints', 'title': '🔧 Filtrar'},
            {'id': 'company_stats', 'title': '📊 Estatísticas'}
        ]
        
        return {
            'success': True,
            'text': text,
            'list_items': list_items if len(list_items) <= 10 else None,
            'buttons': buttons
        }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        try:
            Reclamacao.query.limit(1).all()
            return True
        except:
            return False

