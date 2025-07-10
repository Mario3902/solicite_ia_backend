from typing import Dict, Any, List
from flask import current_app
from src.models import db, User, AchadoPerdido, Conversa
import json
import re
from datetime import datetime, date

class LostFoundModule:
    """Módulo para gerenciar achados e perdidos"""
    
    def __init__(self):
        self.categories = {
            'documento': ['carteira', 'bi', 'passaporte', 'carta', 'conducao', 'identidade', 'cedula', 'documento'],
            'animal': ['cao', 'cachorro', 'gato', 'passaro', 'animal', 'pet', 'bicho'],
            'objeto_pessoal': ['chave', 'carteira', 'bolsa', 'mala', 'mochila', 'oculos', 'relogio'],
            'eletronico': ['telefone', 'celular', 'smartphone', 'tablet', 'laptop', 'computador', 'camera'],
            'veiculo': ['carro', 'moto', 'bicicleta', 'bike', 'automovel', 'motocicleta'],
            'joia': ['anel', 'colar', 'pulseira', 'brinco', 'joia', 'ouro', 'prata'],
            'roupa': ['camisa', 'calca', 'vestido', 'sapato', 'tenis', 'roupa', 'casaco'],
            'outros': ['outro', 'diversos', 'varios']
        }
        
        self.urgency_keywords = ['urgente', 'importante', 'preciso', 'desesperado', 'ajuda']
    
    def process_message(self, nlp_result: Dict[str, Any], user: User, conversa: Conversa) -> Dict[str, Any]:
        """Processa mensagem relacionada a achados e perdidos"""
        try:
            text = nlp_result.get('text', '')
            
            # Determina se é item perdido ou encontrado
            if self._is_lost_item(text):
                return self._handle_lost_item(nlp_result, user, conversa)
            elif self._is_found_item(text):
                return self._handle_found_item(nlp_result, user, conversa)
            else:
                return self._handle_general_inquiry(nlp_result, user, conversa)
                
        except Exception as e:
            current_app.logger.error(f'Erro no módulo achados e perdidos: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao processar solicitação de achados e perdidos.',
                'error': str(e)
            }
    
    def _is_lost_item(self, text: str) -> bool:
        """Determina se é um item perdido"""
        lost_indicators = ['perdi', 'perdeu', 'perdido', 'sumiu', 'desapareceu', 'nao encontro']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in lost_indicators)
    
    def _is_found_item(self, text: str) -> bool:
        """Determina se é um item encontrado"""
        found_indicators = ['encontrei', 'encontrado', 'achei', 'achado', 'encontrou']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in found_indicators)
    
    def _handle_lost_item(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata registro de item perdido"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai informações do item perdido
        item_info = self._extract_item_info(text, entities, 'perdido')
        
        if not item_info.get('object'):
            return {
                'success': True,
                'text': "O que você perdeu?\n\nExemplo: 'Perdi carteira na Marginal' ou 'Perdi cão pastor alemão'",
                'requires_followup': True
            }
        
        if not item_info.get('location'):
            return {
                'success': True,
                'text': f"Onde você perdeu {item_info['object']}?\n\nSeja o mais específico possível sobre o local.",
                'requires_followup': True
            }
        
        # Solicita informações adicionais
        return self._request_lost_item_details(item_info, user, conversa)
    
    def _handle_found_item(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata registro de item encontrado"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai informações do item encontrado
        item_info = self._extract_item_info(text, entities, 'encontrado')
        
        if not item_info.get('object'):
            return {
                'success': True,
                'text': "O que você encontrou?\n\nExemplo: 'Encontrei carteira na Marginal' ou 'Encontrei cão na Maianga'",
                'requires_followup': True
            }
        
        if not item_info.get('location'):
            return {
                'success': True,
                'text': f"Onde você encontrou {item_info['object']}?\n\nSeja específico sobre o local.",
                'requires_followup': True
            }
        
        # Solicita informações adicionais
        return self._request_found_item_details(item_info, user, conversa)
    
    def _extract_item_info(self, text: str, entities: Dict, tipo: str) -> Dict[str, Any]:
        """Extrai informações do item"""
        info = {'tipo': tipo}
        
        # Extrai objeto
        info['object'] = self._extract_object(text, tipo)
        
        # Extrai categoria
        info['category'] = self._extract_category(text)
        
        # Extrai localização
        locations = entities.get('localizacao', [])
        if locations:
            info['location'] = locations[0]
        else:
            info['location'] = self._extract_location_from_text(text)
        
        # Extrai características
        info['characteristics'] = self._extract_characteristics(text)
        
        # Verifica urgência
        info['urgent'] = self._is_urgent(text)
        
        # Extrai data (se mencionada)
        info['date'] = self._extract_date(text)
        
        return info
    
    def _extract_object(self, text: str, tipo: str) -> str:
        """Extrai o objeto perdido/encontrado"""
        # Padrões baseados no tipo
        if tipo == 'perdido':
            patterns = [
                r'perdi\s+(?:o|a|um|uma)?\s*([^,\.]+?)(?:\s+na|\s+no|\s+em|,|\.|$)',
                r'perdeu\s+(?:o|a|um|uma)?\s*([^,\.]+?)(?:\s+na|\s+no|\s+em|,|\.|$)',
                r'perdido\s*:?\s*([^,\.]+?)(?:\s+na|\s+no|\s+em|,|\.|$)'
            ]
        else:  # encontrado
            patterns = [
                r'encontrei\s+(?:o|a|um|uma)?\s*([^,\.]+?)(?:\s+na|\s+no|\s+em|,|\.|$)',
                r'achei\s+(?:o|a|um|uma)?\s*([^,\.]+?)(?:\s+na|\s+no|\s+em|,|\.|$)',
                r'encontrado\s*:?\s*([^,\.]+?)(?:\s+na|\s+no|\s+em|,|\.|$)'
            ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                obj = match.group(1).strip()
                # Remove palavras desnecessárias
                obj = re.sub(r'\b(meu|minha|o|a|um|uma)\b', '', obj, flags=re.IGNORECASE).strip()
                if len(obj) > 2:
                    return obj
        
        return None
    
    def _extract_category(self, text: str) -> str:
        """Extrai categoria do item"""
        text_lower = text.lower()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return 'outros'
    
    def _extract_location_from_text(self, text: str) -> str:
        """Extrai localização do texto"""
        patterns = [
            r'(?:na|no|em)\s+([^,\.]+?)(?:\s+no\s+dia|,|\.|$)',
            r'local\s*:?\s*([^,\.]+?)(?:,|\.|$)',
            r'(?:perdido|encontrado|perdi|encontrei|achei)\s+.*?(?:na|no|em)\s+([^,\.]+?)(?:,|\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 2:
                    return location
        
        return None
    
    def _extract_characteristics(self, text: str) -> Dict[str, str]:
        """Extrai características do item"""
        characteristics = {}
        
        # Cor
        colors = ['preto', 'branco', 'azul', 'vermelho', 'verde', 'amarelo', 'rosa', 'roxo', 'marrom', 'cinza']
        for color in colors:
            if color in text.lower():
                characteristics['cor'] = color
                break
        
        # Marca
        brands = ['samsung', 'iphone', 'apple', 'huawei', 'xiaomi', 'lg', 'sony', 'nokia']
        for brand in brands:
            if brand in text.lower():
                characteristics['marca'] = brand
                break
        
        # Tamanho
        sizes = ['pequeno', 'medio', 'grande', 'mini', 'gigante']
        for size in sizes:
            if size in text.lower():
                characteristics['tamanho'] = size
                break
        
        return characteristics
    
    def _is_urgent(self, text: str) -> bool:
        """Verifica se é urgente"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.urgency_keywords)
    
    def _extract_date(self, text: str) -> date:
        """Extrai data da ocorrência"""
        # Padrões de data
        date_patterns = [
            r'(?:hoje|hj)',
            r'(?:ontem)',
            r'(?:anteontem)',
            r'(\d{1,2})/(\d{1,2})',
            r'dia\s+(\d{1,2})'
        ]
        
        today = date.today()
        
        for pattern in date_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if 'hoje' in match.group(0) or 'hj' in match.group(0):
                    return today
                elif 'ontem' in match.group(0):
                    return date(today.year, today.month, today.day - 1)
                elif 'anteontem' in match.group(0):
                    return date(today.year, today.month, today.day - 2)
                elif '/' in match.group(0):
                    try:
                        day, month = int(match.group(1)), int(match.group(2))
                        return date(today.year, month, day)
                    except:
                        pass
                elif 'dia' in match.group(0):
                    try:
                        day = int(match.group(1))
                        return date(today.year, today.month, day)
                    except:
                        pass
        
        return today  # Padrão: hoje
    
    def _request_lost_item_details(self, item_info: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita detalhes do item perdido"""
        obj = item_info.get('object', 'item')
        location = item_info.get('location', 'local')
        
        text = f"📋 *Registrando item perdido*\n\n"
        text += f"🔍 *Item:* {obj}\n"
        text += f"📍 *Local:* {location}\n\n"
        text += "Para ajudar na busca, preciso de mais detalhes:\n\n"
        text += "📝 *Descrição* completa do item\n"
        text += "🎨 *Cor, marca, modelo* (se aplicável)\n"
        text += "📅 *Quando* perdeu (data/hora aproximada)\n"
        text += "📍 *Local específico* (rua, estabelecimento)\n"
        text += "💰 *Recompensa* (opcional)\n"
        text += "📱 *Contato* preferido\n"
        text += "📸 *Foto* do item (se tiver)\n\n"
        text += "*Exemplo:*\n"
        text += "Carteira de couro marrom, marca Polo\n"
        text += "Perdida ontem às 15h no Kinaxixi Shopping\n"
        text += "Recompensa: 10.000kz\n"
        text += "Contato: 923456789"
        
        # Salva dados temporários
        temp_data = {
            'item_info': item_info,
            'step': 'collecting_details'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        return {
            'success': True,
            'text': text,
            'requires_followup': True
        }
    
    def _request_found_item_details(self, item_info: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita detalhes do item encontrado"""
        obj = item_info.get('object', 'item')
        location = item_info.get('location', 'local')
        
        text = f"📋 *Registrando item encontrado*\n\n"
        text += f"✅ *Item:* {obj}\n"
        text += f"📍 *Local:* {location}\n\n"
        text += "Para ajudar o dono a encontrar, preciso de:\n\n"
        text += "📝 *Descrição* detalhada\n"
        text += "🎨 *Características* (cor, marca, etc.)\n"
        text += "📅 *Quando* encontrou\n"
        text += "📍 *Local exato* onde encontrou\n"
        text += "📱 *Como* entrar em contato com você\n"
        text += "📸 *Foto* do item (opcional)\n\n"
        text += "*Exemplo:*\n"
        text += "Carteira de couro marrom com documentos\n"
        text += "Encontrada hoje de manhã na Marginal\n"
        text += "Próximo ao Hotel Presidente\n"
        text += "Contato: 923456789"
        
        # Salva dados temporários
        temp_data = {
            'item_info': item_info,
            'step': 'collecting_details'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        return {
            'success': True,
            'text': text,
            'requires_followup': True
        }
    
    def _handle_general_inquiry(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata consulta geral sobre achados e perdidos"""
        text = "🔍 *ACHADOS E PERDIDOS*\n\n"
        text += "Como posso ajudar?\n\n"
        text += "📋 *Opções disponíveis:*\n"
        text += "• Registrar item perdido\n"
        text += "• Registrar item encontrado\n"
        text += "• Buscar itens perdidos\n"
        text += "• Ver itens encontrados\n\n"
        text += "*Exemplos de comandos:*\n"
        text += "• 'Perdi carteira na Marginal'\n"
        text += "• 'Encontrei cão na Maianga'\n"
        text += "• 'Procuro iPhone perdido'\n"
        text += "• 'Ver documentos encontrados'"
        
        buttons = [
            {'id': 'register_lost', 'title': '📋 Item Perdido'},
            {'id': 'register_found', 'title': '✅ Item Encontrado'},
            {'id': 'search_lost', 'title': '🔍 Buscar Perdidos'},
            {'id': 'view_found', 'title': '👁️ Ver Encontrados'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons
        }
    
    def search_items(self, search_criteria: Dict, user_id: int) -> List[AchadoPerdido]:
        """Busca itens baseado nos critérios"""
        query = AchadoPerdido.query.filter(
            AchadoPerdido.ativo == True,
            AchadoPerdido.resolvido == False
        )
        
        # Aplica filtros
        if search_criteria.get('tipo'):
            query = query.filter(AchadoPerdido.tipo == search_criteria['tipo'])
        
        if search_criteria.get('categoria'):
            query = query.filter(AchadoPerdido.categoria == search_criteria['categoria'])
        
        if search_criteria.get('objeto'):
            query = query.filter(
                db.or_(
                    AchadoPerdido.objeto.ilike(f'%{search_criteria["objeto"]}%'),
                    AchadoPerdido.descricao.ilike(f'%{search_criteria["objeto"]}%')
                )
            )
        
        if search_criteria.get('local'):
            query = query.filter(
                db.or_(
                    AchadoPerdido.local.ilike(f'%{search_criteria["local"]}%'),
                    AchadoPerdido.local_detalhado.ilike(f'%{search_criteria["local"]}%')
                )
            )
        
        return query.order_by(
            AchadoPerdido.urgente.desc(),
            AchadoPerdido.data_registro.desc()
        ).limit(20).all()
    
    def complete_item_registration(self, item_data: Dict, user: User) -> Dict[str, Any]:
        """Completa o registro do item"""
        try:
            item = AchadoPerdido(
                usuario_id=user.id,
                tipo=item_data['tipo'],
                categoria=item_data.get('categoria', 'outros'),
                objeto=item_data['objeto'],
                descricao=item_data.get('descricao'),
                marca=item_data.get('marca'),
                modelo=item_data.get('modelo'),
                cor=item_data.get('cor'),
                tamanho=item_data.get('tamanho'),
                caracteristicas_especiais=item_data.get('caracteristicas_especiais'),
                local=item_data['local'],
                local_detalhado=item_data.get('local_detalhado'),
                data_ocorrencia=item_data.get('data_ocorrencia', date.today()),
                hora_aproximada=item_data.get('hora_aproximada'),
                recompensa=item_data.get('recompensa'),
                contato_preferido=item_data.get('contato_preferido', 'whatsapp'),
                informacoes_contato=item_data.get('informacoes_contato', user.whatsapp_id),
                urgente=item_data.get('urgente', False),
                imagem_url=item_data.get('imagem_url')
            )
            
            db.session.add(item)
            db.session.commit()
            
            # Busca possíveis correspondências
            matches = []
            if item.tipo == 'perdido':
                matches = AchadoPerdido.buscar_correspondencias(item)
            
            text = f"✅ *Item {item.tipo} registrado!*\n\n"
            text += f"📋 *{item.objeto}*\n"
            text += f"📍 *Local:* {item.local}\n"
            text += f"📅 *Data:* {item.data_ocorrencia.strftime('%d/%m/%Y')}\n\n"
            
            if matches:
                text += f"🎯 *Encontrei {len(matches)} possível(is) correspondência(s)!*\n"
                text += "Verifique se algum destes itens é o seu:\n\n"
                
                for i, match in enumerate(matches[:3], 1):
                    text += f"{i}. {match.objeto} - {match.local}\n"
                    text += f"   📅 {match.data_ocorrencia.strftime('%d/%m/%Y')}\n"
                    text += f"   📱 {match.informacoes_contato}\n\n"
            
            text += "💡 *Seu registro será compartilhado automaticamente para ajudar na busca!*"
            
            return {
                'success': True,
                'text': text,
                'matches': [match.to_dict() for match in matches] if matches else []
            }
            
        except Exception as e:
            current_app.logger.error(f'Erro ao registrar item: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao finalizar registro. Tente novamente.',
                'error': str(e)
            }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        try:
            AchadoPerdido.query.limit(1).all()
            return True
        except:
            return False

