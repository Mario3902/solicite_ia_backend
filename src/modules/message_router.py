from typing import Dict, Any
from flask import current_app
from src.models import User, Conversa
from src.modules.service_providers import ServiceProvidersModule
from src.modules.marketplace import MarketplaceModule
from src.modules.personal_connections import PersonalConnectionsModule
from src.modules.lost_found import LostFoundModule
from src.modules.complaints import ComplaintsModule
from src.modules.scholarships import ScholarshipsModule
from src.modules.financial_market import FinancialMarketModule
from src.modules.web_search import WebSearchModule

class MessageRouter:
    """Roteador de mensagens para direcionar para módulos específicos"""
    
    def __init__(self):
        self.modules = {
            'cadastro_prestador': ServiceProvidersModule(),
            'busca_prestador': ServiceProvidersModule(),
            'venda_produto': MarketplaceModule(),
            'busca_produto': MarketplaceModule(),
            'conexao_pessoal': PersonalConnectionsModule(),
            'achado_perdido': LostFoundModule(),
            'reclamacao': ComplaintsModule(),
            'bolsa_estudo': ScholarshipsModule(),
            'mercado_financeiro': FinancialMarketModule(),
            'pesquisa_geral': WebSearchModule()
        }
    
    def route_message(self, nlp_result: Dict[str, Any], user: User, conversa: Conversa) -> Dict[str, Any]:
        """Roteia mensagem para o módulo apropriado"""
        try:
            intent = nlp_result.get('intent')
            command_type = nlp_result.get('command_type')
            
            # Mensagens de saudação e cortesia
            if intent in ['saudacao', 'agradecimento', 'despedida']:
                return self._handle_courtesy_message(intent, nlp_result, user)
            
            # Mensagens de ajuda
            if intent == 'ajuda' or 'ajuda' in nlp_result.get('text', '').lower():
                return self._handle_help_message(user)
            
            # Mensagens desconhecidas ou com baixa confiança
            if intent == 'unknown' or nlp_result.get('confidence', 0) < 0.5:
                return self._handle_unknown_message(nlp_result, user)
            
            # Roteia para módulo específico
            module = self.modules.get(command_type)
            if module:
                return module.process_message(nlp_result, user, conversa)
            else:
                current_app.logger.warning(f'Módulo não encontrado para comando: {command_type}')
                return self._handle_unknown_message(nlp_result, user)
                
        except Exception as e:
            current_app.logger.error(f'Erro no roteamento de mensagem: {str(e)}')
            return {
                'success': False,
                'text': 'Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes.',
                'error': str(e)
            }
    
    def _handle_courtesy_message(self, intent: str, nlp_result: Dict, user: User) -> Dict[str, Any]:
        """Trata mensagens de cortesia"""
        responses = {
            'saudacao': [
                f"Olá! 👋 Bem-vindo ao Solicite IA! Sou seu assistente virtual e estou aqui para ajudar.",
                "Como posso ajudá-lo hoje? Posso ajudar com:",
                "",
                "🔧 *Serviços* - Encontrar ou cadastrar prestadores",
                "🛒 *Marketplace* - Comprar ou vender produtos", 
                "💕 *Conexões* - Conhecer pessoas para amizade ou namoro",
                "🔍 *Achados e Perdidos* - Registrar itens perdidos/encontrados",
                "📢 *Reclamações* - Denunciar problemas com empresas",
                "🎓 *Bolsas de Estudo* - Encontrar oportunidades educacionais",
                "💰 *Mercado Financeiro* - Cotações e informações",
                "🌐 *Pesquisa* - Buscar informações gerais",
                "",
                "Digite sua solicitação ou envie uma foto para começar!"
            ],
            'agradecimento': [
                "De nada! 😊 Fico feliz em ajudar!",
                "",
                "Se precisar de mais alguma coisa, é só falar. Estou sempre aqui para você!"
            ],
            'despedida': [
                "Até logo! 👋 Foi um prazer ajudá-lo.",
                "",
                "Volte sempre que precisar. O Solicite IA está sempre disponível para você! 🤖"
            ]
        }
        
        response_text = "\n".join(responses.get(intent, ["Olá! Como posso ajudá-lo?"]))
        
        return {
            'success': True,
            'text': response_text,
            'type': 'courtesy'
        }
    
    def _handle_help_message(self, user: User) -> Dict[str, Any]:
        """Trata mensagens de ajuda"""
        help_text = """
🤖 *SOLICITE IA - GUIA DE USO*

*SERVIÇOS DISPONÍVEIS:*

🔧 *PRESTADORES DE SERVIÇOS*
• Cadastrar: "Sou eletricista em Luanda"
• Buscar: "Procuro canalizador em Cacuaco"

🛒 *MARKETPLACE*
• Vender: "Vendo bicicleta usada, 80.000kz"
• Comprar: "Procuro iPhone usado"

💕 *CONEXÕES PESSOAIS*
• Cadastrar: "Homem, 30 anos, solteiro, Luanda"
• Buscar: "Procuro mulher para namoro"

🔍 *ACHADOS E PERDIDOS*
• Perdido: "Perdi carteira na Marginal"
• Encontrado: "Encontrei cão na Maianga"

📢 *RECLAMAÇÕES*
• Reclamar: "Problema com Unitel cobrança indevida"

🎓 *BOLSAS DE ESTUDO*
• Buscar: "Bolsa para mestrado em Portugal"

💰 *MERCADO FINANCEIRO*
• Cotações: "Preço do Bitcoin"
• Câmbio: "Dólar hoje"

🌐 *PESQUISA GERAL*
• Perguntar: "Qual o fuso horário da China?"

*DICAS:*
• Seja específico nas suas solicitações
• Inclua localização quando relevante
• Envie fotos para melhor resultado
• Use linguagem natural e simples

Precisa de ajuda específica? Digite sua dúvida!
        """
        
        return {
            'success': True,
            'text': help_text.strip(),
            'type': 'help'
        }
    
    def _handle_unknown_message(self, nlp_result: Dict, user: User) -> Dict[str, Any]:
        """Trata mensagens não compreendidas"""
        text = nlp_result.get('text', '')
        
        # Tenta dar sugestões baseadas em palavras-chave
        suggestions = []
        
        if any(word in text.lower() for word in ['serviço', 'trabalho', 'profissional']):
            suggestions.append("🔧 Para serviços: 'Procuro eletricista em Luanda' ou 'Sou pintor em Benguela'")
        
        if any(word in text.lower() for word in ['vender', 'comprar', 'produto']):
            suggestions.append("🛒 Para marketplace: 'Vendo carro Toyota' ou 'Procuro telefone usado'")
        
        if any(word in text.lower() for word in ['namoro', 'amizade', 'relacionamento']):
            suggestions.append("💕 Para conexões: 'Homem, 25 anos, solteiro' ou 'Procuro mulher para namoro'")
        
        if any(word in text.lower() for word in ['perdi', 'encontrei', 'perdido']):
            suggestions.append("🔍 Para achados: 'Perdi carteira no Kinaxixi' ou 'Encontrei cão na Maianga'")
        
        if any(word in text.lower() for word in ['reclamar', 'problema', 'empresa']):
            suggestions.append("📢 Para reclamações: 'Problema com empresa X por motivo Y'")
        
        response_text = "Desculpe, não compreendi sua solicitação. 🤔\n\n"
        
        if suggestions:
            response_text += "*Talvez você queira:*\n\n"
            response_text += "\n".join(suggestions)
            response_text += "\n\n"
        
        response_text += "💡 *Exemplos de comandos:*\n"
        response_text += "• 'Procuro eletricista em Luanda'\n"
        response_text += "• 'Vendo iPhone 12, 150.000kz'\n"
        response_text += "• 'Homem, 30 anos, solteiro'\n"
        response_text += "• 'Perdi carteira na Marginal'\n"
        response_text += "• 'Problema com Unitel'\n\n"
        response_text += "Digite 'ajuda' para ver todos os comandos disponíveis."
        
        buttons = [
            {'id': 'help', 'title': '📋 Ver Ajuda'},
            {'id': 'services', 'title': '🔧 Serviços'},
            {'id': 'marketplace', 'title': '🛒 Marketplace'}
        ]
        
        return {
            'success': True,
            'text': response_text,
            'buttons': buttons,
            'type': 'clarification'
        }
    
    def get_module_status(self) -> Dict[str, bool]:
        """Retorna status de todos os módulos"""
        status = {}
        
        for module_name, module in self.modules.items():
            try:
                # Tenta chamar método de status se existir
                if hasattr(module, 'get_status'):
                    status[module_name] = module.get_status()
                else:
                    status[module_name] = True  # Assume que está funcionando
            except Exception as e:
                current_app.logger.error(f'Erro ao verificar status do módulo {module_name}: {str(e)}')
                status[module_name] = False
        
        return status
    
    def handle_button_response(self, button_id: str, user: User) -> Dict[str, Any]:
        """Trata respostas de botões interativos"""
        button_handlers = {
            'help': lambda: self._handle_help_message(user),
            'services': lambda: {
                'success': True,
                'text': "🔧 *SERVIÇOS DISPONÍVEIS*\n\nPara cadastrar: 'Sou [profissão] em [local]'\nPara buscar: 'Procuro [profissão] em [local]'\n\nExemplo: 'Procuro eletricista em Luanda'"
            },
            'marketplace': lambda: {
                'success': True,
                'text': "🛒 *MARKETPLACE*\n\nPara vender: 'Vendo [produto], [preço]'\nPara comprar: 'Procuro [produto]'\n\nExemplo: 'Vendo iPhone 12, 150.000kz'"
            }
        }
        
        handler = button_handlers.get(button_id)
        if handler:
            return handler()
        else:
            return {
                'success': False,
                'text': 'Opção não reconhecida. Digite sua solicitação.'
            }

