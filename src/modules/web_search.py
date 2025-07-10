from typing import Dict, Any, List
from flask import current_app
import requests
import json
import re

class WebSearchModule:
    """Módulo para pesquisa web e respostas gerais"""
    
    def __init__(self):
        self.question_types = {
            'what': ['o que', 'que', 'qual'],
            'how': ['como', 'de que forma', 'de que maneira'],
            'when': ['quando', 'que horas', 'que dia'],
            'where': ['onde', 'em que lugar', 'aonde'],
            'why': ['por que', 'porque', 'qual motivo'],
            'who': ['quem', 'que pessoa']
        }
        
        self.common_topics = {
            'weather': ['tempo', 'clima', 'chuva', 'sol', 'temperatura'],
            'time': ['horas', 'horario', 'fuso', 'tempo'],
            'location': ['fica', 'localiza', 'endereco', 'onde'],
            'definition': ['significa', 'definicao', 'conceito'],
            'calculation': ['calcular', 'quanto', 'resultado'],
            'translation': ['traduzir', 'traducao', 'significa em']
        }
    
    def process_message(self, nlp_result: Dict[str, Any], user, conversa) -> Dict[str, Any]:
        """Processa mensagem de pesquisa geral"""
        try:
            text = nlp_result.get('text', '')
            
            # Identifica tipo de pergunta
            question_type = self._identify_question_type(text)
            topic = self._identify_topic(text)
            
            # Processa baseado no tipo
            if topic == 'weather':
                return self._handle_weather_query(text)
            elif topic == 'time':
                return self._handle_time_query(text)
            elif topic == 'definition':
                return self._handle_definition_query(text)
            elif topic == 'calculation':
                return self._handle_calculation_query(text)
            else:
                return self._handle_general_search(text, question_type)
                
        except Exception as e:
            current_app.logger.error(f'Erro no módulo de pesquisa: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao realizar pesquisa.',
                'error': str(e)
            }
    
    def _identify_question_type(self, text: str) -> str:
        """Identifica tipo de pergunta"""
        text_lower = text.lower()
        
        for q_type, keywords in self.question_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return q_type
        
        return 'general'
    
    def _identify_topic(self, text: str) -> str:
        """Identifica tópico da pergunta"""
        text_lower = text.lower()
        
        for topic, keywords in self.common_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return 'general'
    
    def _handle_weather_query(self, text: str) -> Dict[str, Any]:
        """Trata consultas sobre tempo/clima"""
        # Extrai localização se mencionada
        location = self._extract_location(text)
        
        if not location:
            location = "Luanda"  # Padrão
        
        # Dados simulados (integraria com API real como OpenWeatherMap)
        weather_data = self._get_mock_weather_data(location)
        
        text_response = f"🌤️ *TEMPO EM {location.upper()}*\n\n"
        text_response += f"🌡️ *Temperatura:* {weather_data['temperature']}°C\n"
        text_response += f"☁️ *Condição:* {weather_data['condition']}\n"
        text_response += f"💧 *Umidade:* {weather_data['humidity']}%\n"
        text_response += f"💨 *Vento:* {weather_data['wind']} km/h\n"
        text_response += f"🌅 *Nascer do sol:* {weather_data['sunrise']}\n"
        text_response += f"🌇 *Pôr do sol:* {weather_data['sunset']}\n\n"
        text_response += f"📅 *Previsão para amanhã:*\n"
        text_response += f"🌡️ {weather_data['tomorrow']['temp']}°C - {weather_data['tomorrow']['condition']}\n\n"
        text_response += "💡 *Fonte:* Serviço meteorológico (simulado)"
        
        buttons = [
            {'id': 'weather_week', 'title': '📅 Semana'},
            {'id': 'weather_other_city', 'title': '🌍 Outra Cidade'},
            {'id': 'weather_alerts', 'title': '⚠️ Alertas'}
        ]
        
        return {
            'success': True,
            'text': text_response,
            'buttons': buttons
        }
    
    def _handle_time_query(self, text: str) -> Dict[str, Any]:
        """Trata consultas sobre horário/fuso"""
        from datetime import datetime
        import pytz
        
        # Extrai país/cidade se mencionado
        location = self._extract_location(text)
        
        if location:
            # Mapeia para fusos horários
            timezone_map = {
                'china': 'Asia/Shanghai',
                'japao': 'Asia/Tokyo',
                'brasil': 'America/Sao_Paulo',
                'portugal': 'Europe/Lisbon',
                'eua': 'America/New_York',
                'reino unido': 'Europe/London',
                'franca': 'Europe/Paris',
                'alemanha': 'Europe/Berlin'
            }
            
            tz_name = timezone_map.get(location.lower())
            if tz_name:
                try:
                    tz = pytz.timezone(tz_name)
                    local_time = datetime.now(tz)
                    
                    text_response = f"🕐 *HORÁRIO EM {location.upper()}*\n\n"
                    text_response += f"⏰ *Hora atual:* {local_time.strftime('%H:%M:%S')}\n"
                    text_response += f"📅 *Data:* {local_time.strftime('%d/%m/%Y')}\n"
                    text_response += f"🌍 *Fuso horário:* {tz_name}\n\n"
                    
                    # Compara com Angola
                    angola_tz = pytz.timezone('Africa/Luanda')
                    angola_time = datetime.now(angola_tz)
                    diff = (local_time.utcoffset() - angola_time.utcoffset()).total_seconds() / 3600
                    
                    if diff > 0:
                        text_response += f"🔄 *Diferença:* +{diff:.0f}h em relação a Angola"
                    elif diff < 0:
                        text_response += f"🔄 *Diferença:* {diff:.0f}h em relação a Angola"
                    else:
                        text_response += f"🔄 *Mesmo fuso horário* que Angola"
                    
                    return {
                        'success': True,
                        'text': text_response
                    }
                except:
                    pass
        
        # Horário local (Angola)
        now = datetime.now()
        text_response = f"🕐 *HORÁRIO ATUAL*\n\n"
        text_response += f"⏰ *Luanda:* {now.strftime('%H:%M:%S')}\n"
        text_response += f"📅 *Data:* {now.strftime('%d/%m/%Y')}\n"
        text_response += f"📍 *Fuso:* WAT (UTC+1)\n\n"
        text_response += "💡 Para outros países, especifique o local\n"
        text_response += "Exemplo: 'Que horas são na China?'"
        
        return {
            'success': True,
            'text': text_response
        }
    
    def _handle_definition_query(self, text: str) -> Dict[str, Any]:
        """Trata consultas de definição"""
        # Extrai termo a ser definido
        term = self._extract_definition_term(text)
        
        if not term:
            return {
                'success': True,
                'text': "O que você gostaria que eu definisse?\n\nExemplo: 'O que significa blockchain?'"
            }
        
        # Definições simuladas (integraria com API de dicionário)
        definitions = {
            'blockchain': 'Tecnologia de registro distribuído que mantém uma lista crescente de registros (blocos) vinculados e protegidos por criptografia.',
            'inteligencia artificial': 'Campo da ciência da computação que se concentra na criação de sistemas capazes de realizar tarefas que normalmente requerem inteligência humana.',
            'bitcoin': 'Criptomoeda descentralizada que funciona sem autoridade central ou bancos, usando tecnologia blockchain.',
            'covid': 'Doença infecciosa causada pelo coronavírus SARS-CoV-2, identificada pela primeira vez em 2019.',
            'sustentabilidade': 'Capacidade de satisfazer as necessidades presentes sem comprometer a capacidade das gerações futuras.'
        }
        
        definition = definitions.get(term.lower())
        
        if definition:
            text_response = f"📚 *DEFINIÇÃO: {term.upper()}*\n\n"
            text_response += f"💡 {definition}\n\n"
            text_response += "🔍 Quer saber mais sobre algum aspecto específico?"
        else:
            text_response = f"🤔 Não encontrei uma definição para '{term}' na minha base.\n\n"
            text_response += "💡 Posso ajudar com:\n"
            text_response += "• Termos tecnológicos\n"
            text_response += "• Conceitos financeiros\n"
            text_response += "• Definições gerais\n\n"
            text_response += "Tente reformular ou pergunte sobre outro termo."
        
        return {
            'success': True,
            'text': text_response
        }
    
    def _handle_calculation_query(self, text: str) -> Dict[str, Any]:
        """Trata consultas de cálculo"""
        # Extrai expressão matemática
        expression = self._extract_math_expression(text)
        
        if not expression:
            return {
                'success': True,
                'text': "Que cálculo você quer fazer?\n\nExemplos:\n• '2 + 2'\n• '10% de 1000'\n• 'raiz de 16'"
            }
        
        try:
            # Processa expressões simples
            result = self._calculate_expression(expression)
            
            text_response = f"🧮 *CÁLCULO*\n\n"
            text_response += f"📝 *Expressão:* {expression}\n"
            text_response += f"✅ *Resultado:* {result}\n\n"
            text_response += "💡 Posso fazer cálculos básicos, percentuais e conversões simples."
            
            return {
                'success': True,
                'text': text_response
            }
            
        except:
            return {
                'success': True,
                'text': f"❌ Não consegui calcular '{expression}'.\n\nTente uma expressão mais simples."
            }
    
    def _handle_general_search(self, text: str, question_type: str) -> Dict[str, Any]:
        """Trata pesquisas gerais"""
        # Respostas simuladas para perguntas comuns
        common_answers = {
            'capital de angola': 'A capital de Angola é Luanda.',
            'presidente de angola': 'O atual Presidente de Angola é João Lourenço.',
            'moeda de angola': 'A moeda oficial de Angola é o Kwanza (AOA).',
            'populacao de angola': 'Angola tem aproximadamente 35 milhões de habitantes.',
            'lingua oficial de angola': 'A língua oficial de Angola é o Português.'
        }
        
        # Busca resposta direta
        text_lower = text.lower()
        for question, answer in common_answers.items():
            if question in text_lower:
                text_response = f"💡 *RESPOSTA*\n\n{answer}\n\n"
                text_response += "🔍 Precisa de mais informações sobre este tópico?"
                
                return {
                    'success': True,
                    'text': text_response
                }
        
        # Resposta genérica para outras perguntas
        text_response = f"🔍 *PESQUISA: {text}*\n\n"
        text_response += "Desculpe, não tenho informações específicas sobre essa consulta no momento.\n\n"
        text_response += "💡 *Posso ajudar com:*\n"
        text_response += "• Informações sobre Angola\n"
        text_response += "• Definições de termos\n"
        text_response += "• Cálculos simples\n"
        text_response += "• Horários mundiais\n"
        text_response += "• Previsão do tempo\n\n"
        text_response += "Tente reformular sua pergunta ou seja mais específico."
        
        buttons = [
            {'id': 'search_help', 'title': '❓ Como Pesquisar'},
            {'id': 'popular_topics', 'title': '📋 Tópicos Populares'},
            {'id': 'other_services', 'title': '🔧 Outros Serviços'}
        ]
        
        return {
            'success': True,
            'text': text_response,
            'buttons': buttons
        }
    
    def _extract_location(self, text: str) -> str:
        """Extrai localização do texto"""
        locations = [
            'luanda', 'benguela', 'huambo', 'lobito', 'cabinda',
            'china', 'japao', 'brasil', 'portugal', 'eua', 'reino unido',
            'franca', 'alemanha', 'espanha', 'italia'
        ]
        
        text_lower = text.lower()
        for location in locations:
            if location in text_lower:
                return location
        
        return None
    
    def _extract_definition_term(self, text: str) -> str:
        """Extrai termo para definição"""
        patterns = [
            r'(?:o que (?:é|significa)|que (?:é|significa)|significa) (.+?)(?:\?|$)',
            r'definicao de (.+?)(?:\?|$)',
            r'conceito de (.+?)(?:\?|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_math_expression(self, text: str) -> str:
        """Extrai expressão matemática"""
        # Padrões matemáticos simples
        patterns = [
            r'(\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?%\s*de\s*\d+(?:\.\d+)?)',
            r'(raiz\s*de\s*\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        return None
    
    def _calculate_expression(self, expression: str) -> str:
        """Calcula expressão matemática simples"""
        expression = expression.lower().replace(' ', '')
        
        # Percentual
        if '%' in expression and 'de' in expression:
            parts = expression.split('%de')
            if len(parts) == 2:
                percent = float(parts[0])
                value = float(parts[1])
                result = (percent / 100) * value
                return f"{result:,.2f}"
        
        # Raiz quadrada
        if 'raizde' in expression:
            number = float(expression.replace('raizde', ''))
            result = number ** 0.5
            return f"{result:,.2f}"
        
        # Operações básicas
        try:
            # Remove caracteres perigosos e avalia
            safe_expr = re.sub(r'[^0-9+\-*/.()]', '', expression)
            result = eval(safe_expr)
            return f"{result:,.2f}" if isinstance(result, float) else str(result)
        except:
            raise ValueError("Expressão inválida")
    
    def _get_mock_weather_data(self, location: str) -> Dict[str, Any]:
        """Dados simulados de tempo"""
        return {
            'temperature': 28,
            'condition': 'Parcialmente nublado',
            'humidity': 75,
            'wind': 12,
            'sunrise': '06:15',
            'sunset': '18:30',
            'tomorrow': {
                'temp': 30,
                'condition': 'Ensolarado'
            }
        }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        return True

