from typing import Dict, Any, List
from flask import current_app
from src.models import db, User, PrestadorServico, Conversa
import json

class ServiceProvidersModule:
    """Módulo para gerenciar prestadores de serviços"""
    
    def __init__(self):
        self.specialties = {
            'eletricista': ['eletricista', 'eletrico', 'instalacao eletrica', 'fiacao'],
            'canalizador': ['canalizador', 'encanador', 'canos', 'agua', 'torneira'],
            'pintor': ['pintor', 'pintura', 'tinta', 'parede'],
            'mecanico': ['mecanico', 'carro', 'automovel', 'motor'],
            'cabeleireira': ['cabeleireira', 'cabelo', 'penteado', 'corte'],
            'costureira': ['costureira', 'costura', 'roupa', 'alfaiate'],
            'soldador': ['soldador', 'solda', 'ferro', 'metal'],
            'carpinteiro': ['carpinteiro', 'madeira', 'movel', 'porta'],
            'pedreiro': ['pedreiro', 'construcao', 'obra', 'tijolo'],
            'jardineiro': ['jardineiro', 'jardim', 'plantas', 'grama'],
            'domestica': ['domestica', 'limpeza', 'casa', 'empregada'],
            'seguranca': ['seguranca', 'guarda', 'vigilante', 'porteiro'],
            'professor': ['professor', 'ensino', 'aulas', 'explicacoes'],
            'motorista': ['motorista', 'condutor', 'transporte', 'taxi']
        }
    
    def process_message(self, nlp_result: Dict[str, Any], user: User, conversa: Conversa) -> Dict[str, Any]:
        """Processa mensagem relacionada a prestadores de serviços"""
        try:
            command_type = nlp_result.get('command_type')
            
            if command_type == 'cadastro_prestador':
                return self._handle_provider_registration(nlp_result, user, conversa)
            elif command_type == 'busca_prestador':
                return self._handle_provider_search(nlp_result, user, conversa)
            else:
                return {
                    'success': False,
                    'text': 'Comando não reconhecido para prestadores de serviços.'
                }
                
        except Exception as e:
            current_app.logger.error(f'Erro no módulo de prestadores: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao processar solicitação de serviços.',
                'error': str(e)
            }
    
    def _handle_provider_registration(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata cadastro de prestador de serviços"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai especialidade do texto
        specialty = self._extract_specialty(text)
        if not specialty:
            return {
                'success': True,
                'text': "Qual é sua especialidade/profissão?\n\nExemplos: eletricista, canalizador, pintor, mecânico, cabeleireira, etc.",
                'requires_followup': True
            }
        
        # Extrai localização
        location = self._extract_location(entities, text)
        if not location:
            return {
                'success': True,
                'text': f"Entendi que você é {specialty}. Em que região você atende?\n\nExemplo: Luanda, Cacuaco, Viana, etc.",
                'requires_followup': True
            }
        
        # Verifica se já existe cadastro
        existing = PrestadorServico.query.filter_by(
            usuario_id=user.id,
            especialidade=specialty
        ).first()
        
        if existing:
            return {
                'success': True,
                'text': f"Você já está cadastrado como {specialty} em {existing.localizacao}.\n\nDeseja atualizar suas informações?",
                'buttons': [
                    {'id': 'update_provider', 'title': '✏️ Atualizar'},
                    {'id': 'view_provider', 'title': '👁️ Ver Perfil'},
                    {'id': 'new_specialty', 'title': '➕ Nova Especialidade'}
                ]
            }
        
        # Solicita informações adicionais
        return self._request_additional_info(specialty, location, user)
    
    def _request_additional_info(self, specialty: str, location: str, user: User) -> Dict[str, Any]:
        """Solicita informações adicionais para completar cadastro"""
        text = f"Perfeito! Vou cadastrar você como *{specialty}* em *{location}*.\n\n"
        text += "Para completar seu perfil, preciso de mais algumas informações:\n\n"
        text += "📱 *Contato* (WhatsApp/Telefone)\n"
        text += "💰 *Preço* (faixa de valores)\n"
        text += "📝 *Descrição* dos seus serviços\n"
        text += "🕐 *Disponibilidade* (horários)\n\n"
        text += "Pode enviar tudo numa mensagem ou uma informação por vez.\n\n"
        text += "*Exemplo:*\n"
        text += "Contato: 923456789\n"
        text += "Preço: 5.000 a 15.000 kz\n"
        text += "Faço instalações elétricas residenciais e comerciais\n"
        text += "Disponível segunda a sábado, 8h às 17h"
        
        # Salva dados temporários na conversa
        temp_data = {
            'specialty': specialty,
            'location': location,
            'step': 'collecting_info'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        return {
            'success': True,
            'text': text,
            'requires_followup': True
        }
    
    def _handle_provider_search(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata busca por prestadores de serviços"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai especialidade procurada
        specialty = self._extract_specialty(text)
        if not specialty:
            return {
                'success': True,
                'text': "Que tipo de profissional você está procurando?\n\nExemplos: eletricista, canalizador, pintor, mecânico, cabeleireira, etc.",
                'requires_followup': True
            }
        
        # Extrai localização
        location = self._extract_location(entities, text)
        
        # Busca prestadores
        providers = self._search_providers(specialty, location)
        
        if not providers:
            return self._handle_no_providers_found(specialty, location)
        
        return self._format_providers_response(providers, specialty, location)
    
    def _search_providers(self, specialty: str, location: str = None) -> List[PrestadorServico]:
        """Busca prestadores por especialidade e localização"""
        query = PrestadorServico.query.filter(
            PrestadorServico.ativo == True,
            PrestadorServico.especialidade.ilike(f'%{specialty}%')
        )
        
        if location:
            query = query.filter(PrestadorServico.localizacao.ilike(f'%{location}%'))
        
        return query.order_by(
            PrestadorServico.avaliacao_media.desc(),
            PrestadorServico.verificado.desc(),
            PrestadorServico.data_cadastro.desc()
        ).limit(10).all()
    
    def _format_providers_response(self, providers: List[PrestadorServico], specialty: str, location: str) -> Dict[str, Any]:
        """Formata resposta com lista de prestadores"""
        location_text = f" em {location}" if location else ""
        text = f"🔍 Encontrei {len(providers)} {specialty}(s){location_text}:\n\n"
        
        list_items = []
        
        for i, provider in enumerate(providers, 1):
            # Monta texto do prestador
            provider_text = f"*{provider.nome}*\n"
            provider_text += f"📍 {provider.localizacao}\n"
            
            if provider.avaliacao_media > 0:
                stars = "⭐" * int(provider.avaliacao_media)
                provider_text += f"{stars} ({provider.avaliacao_media:.1f})\n"
            
            if provider.verificado:
                provider_text += "✅ Verificado\n"
            
            if provider.preco_minimo and provider.preco_maximo:
                provider_text += f"💰 {provider.preco_minimo:,.0f} - {provider.preco_maximo:,.0f} kz\n"
            
            if provider.disponibilidade:
                provider_text += f"🕐 {provider.disponibilidade}\n"
            
            provider_text += f"📱 {provider.contato}"
            
            text += f"{i}. {provider_text}\n\n"
            
            # Adiciona à lista interativa
            list_items.append({
                'id': f'provider_{provider.id}',
                'title': f"{provider.nome} - {provider.localizacao}",
                'description': f"⭐ {provider.avaliacao_media:.1f} | {provider.contato}"
            })
        
        text += "💡 *Dica:* Sempre confirme disponibilidade e preços antes de contratar!"
        
        buttons = [
            {'id': 'search_again', 'title': '🔍 Nova Busca'},
            {'id': 'register_provider', 'title': '➕ Cadastrar-me'},
            {'id': 'filter_results', 'title': '🔧 Filtrar'}
        ]
        
        return {
            'success': True,
            'text': text,
            'list_items': list_items if len(list_items) <= 10 else None,
            'buttons': buttons
        }
    
    def _handle_no_providers_found(self, specialty: str, location: str) -> Dict[str, Any]:
        """Trata caso onde não foram encontrados prestadores"""
        location_text = f" em {location}" if location else ""
        
        text = f"😔 Não encontrei {specialty}(s){location_text} no momento.\n\n"
        text += "💡 *Sugestões:*\n"
        text += "• Tente uma região próxima\n"
        text += "• Verifique a grafia da profissão\n"
        text += "• Cadastre-se se você é prestador\n\n"
        text += "Posso ajudar com outra busca?"
        
        buttons = [
            {'id': 'search_nearby', 'title': '📍 Região Próxima'},
            {'id': 'register_provider', 'title': '➕ Sou Prestador'},
            {'id': 'other_search', 'title': '🔍 Outra Busca'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons
        }
    
    def _extract_specialty(self, text: str) -> str:
        """Extrai especialidade do texto"""
        text_lower = text.lower()
        
        for specialty, keywords in self.specialties.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return specialty
        
        # Busca por padrões específicos
        import re
        
        # Padrão "sou [profissão]"
        match = re.search(r'sou\s+([a-zA-Z]+)', text_lower)
        if match:
            return match.group(1)
        
        # Padrão "trabalho como [profissão]"
        match = re.search(r'trabalho\s+como\s+([a-zA-Z]+)', text_lower)
        if match:
            return match.group(1)
        
        # Padrão "procuro [profissão]"
        match = re.search(r'procur[ao]\s+([a-zA-Z]+)', text_lower)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_location(self, entities: Dict, text: str) -> str:
        """Extrai localização das entidades ou texto"""
        # Primeiro tenta das entidades extraídas
        locations = entities.get('localizacao', [])
        if locations:
            return locations[0]
        
        # Busca no texto diretamente
        import re
        
        # Padrões de localização
        location_patterns = [
            r'em\s+([a-zA-Z\s]+?)(?:\s|$|,|\.|!|\?)',
            r'na\s+([a-zA-Z\s]+?)(?:\s|$|,|\.|!|\?)',
            r'no\s+([a-zA-Z\s]+?)(?:\s|$|,|\.|!|\?)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text.lower())
            if match:
                location = match.group(1).strip()
                if len(location) > 2:  # Evita palavras muito pequenas
                    return location.title()
        
        return None
    
    def complete_registration(self, provider_data: Dict, user: User) -> Dict[str, Any]:
        """Completa o cadastro do prestador"""
        try:
            provider = PrestadorServico(
                usuario_id=user.id,
                nome=provider_data.get('nome', user.nome or 'Prestador'),
                especialidade=provider_data['especialidade'],
                localizacao=provider_data['localizacao'],
                contato=provider_data.get('contato', user.telefone or ''),
                descricao=provider_data.get('descricao'),
                preco_minimo=provider_data.get('preco_minimo'),
                preco_maximo=provider_data.get('preco_maximo'),
                disponibilidade=provider_data.get('disponibilidade'),
                whatsapp_contato=user.whatsapp_id
            )
            
            db.session.add(provider)
            db.session.commit()
            
            text = f"✅ *Cadastro realizado com sucesso!*\n\n"
            text += f"👤 *Nome:* {provider.nome}\n"
            text += f"🔧 *Especialidade:* {provider.especialidade}\n"
            text += f"📍 *Localização:* {provider.localizacao}\n"
            text += f"📱 *Contato:* {provider.contato}\n\n"
            text += "Seu perfil já está disponível para clientes!\n\n"
            text += "💡 *Dicas para mais clientes:*\n"
            text += "• Mantenha seu perfil atualizado\n"
            text += "• Responda rapidamente aos contatos\n"
            text += "• Peça avaliações aos clientes satisfeitos"
            
            return {
                'success': True,
                'text': text
            }
            
        except Exception as e:
            current_app.logger.error(f'Erro ao completar cadastro: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao finalizar cadastro. Tente novamente.',
                'error': str(e)
            }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        try:
            # Testa conexão com banco
            PrestadorServico.query.limit(1).all()
            return True
        except:
            return False

