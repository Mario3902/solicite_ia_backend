import re
import json
import logging
from typing import Dict, List, Optional, Any
from flask import current_app
import openai

class NLPProcessor:
    """Processador de linguagem natural para interpretar comandos dos usuários"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
        
        # Padrões de comando para detecção rápida
        self.command_patterns = {
            'cadastro_prestador': [
                r'cadastrar?\s+servi[çc]o',
                r'sou\s+(.*?)\s+em\s+(.*)',
                r'trabalho\s+como\s+(.*)',
                r'ofere[çc]o\s+servi[çc]os?\s+de\s+(.*)',
                r'prestador\s+de\s+(.*)'
            ],
            'busca_prestador': [
                r'procur[ao]\s+(.*?)\s+em\s+(.*)',
                r'preciso\s+de\s+um[a]?\s+(.*)',
                r'quero\s+contratar\s+(.*)',
                r'buscar?\s+(.*?)\s+(canalizador|eletricista|pintor|cabeleireira|mecanico)',
                r'ver\s+(.*?)\s+disponivel'
            ],
            'venda_produto': [
                r'vender?\s+(.*)',
                r'tenho\s+para\s+venda\s+(.*)',
                r'estou\s+vendendo\s+(.*)',
                r'produto\s+para\s+venda',
                r'anunciar\s+(.*)'
            ],
            'busca_produto': [
                r'comprar?\s+(.*)',
                r'procur[ao]\s+para\s+comprar\s+(.*)',
                r'quero\s+comprar\s+(.*)',
                r'buscar?\s+produto\s+(.*)',
                r'tem\s+para\s+venda\s+(.*)'
            ],
            'conexao_pessoal': [
                r'relacionamento',
                r'procur[ao]\s+(homem|mulher|pessoa)',
                r'namoro',
                r'amizade',
                r'conhecer\s+pessoas',
                r'solteiro[a]?',
                r'casamento'
            ],
            'achado_perdido': [
                r'perdi\s+(.*)',
                r'encontrei\s+(.*)',
                r'achei\s+(.*)',
                r'perdido\s+(.*)',
                r'encontrado\s+(.*)',
                r'sumiu\s+(.*)'
            ],
            'reclamacao': [
                r'reclamar?\s+(.*)',
                r'denunciar?\s+(.*)',
                r'problema\s+com\s+(.*)',
                r'insatisfeito\s+com\s+(.*)',
                r'empresa\s+(.*)\s+problema'
            ],
            'bolsa_estudo': [
                r'bolsa\s+de\s+estudo',
                r'bolsa\s+para\s+(.*)',
                r'estudar\s+em\s+(.*)',
                r'curso\s+gratuito',
                r'faculdade\s+gratuita',
                r'mestrado\s+em\s+(.*)'
            ],
            'mercado_financeiro': [
                r'a[çc][ãa]o\s+(.*)',
                r'criptomoeda\s+(.*)',
                r'bitcoin',
                r'dolar',
                r'euro',
                r'cambio',
                r'bolsa\s+de\s+valores'
            ],
            'pesquisa_geral': [
                r'pesquisar?\s+(.*)',
                r'qual\s+(.*)',
                r'como\s+(.*)',
                r'onde\s+(.*)',
                r'quando\s+(.*)',
                r'por\s+que\s+(.*)'
            ]
        }
        
        # Entidades comuns para extração
        self.entity_patterns = {
            'localizacao': [
                r'em\s+(luanda|benguela|huambo|lobito|cabinda|namibe|malanje|uige|zaire|cuando\s+cubango|cunene|huila|lunda\s+norte|lunda\s+sul|moxico|bengo|bie)',
                r'em\s+(cacuaco|viana|cazenga|sambizanga|maianga|ingombota|rangel|kilamba|talatona|zango)',
                r'na\s+(marginal|baixa|cidade\s+alta|miramar|alvalade|maianga)'
            ],
            'preco': [
                r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:kz|kwanza|akz)',
                r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:usd|dolar|dollar)',
                r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(?:eur|euro)'
            ],
            'telefone': [
                r'(\+244\s*)?([9][0-9]{8})',
                r'(\+244\s*)?([2][0-9]{8})'
            ],
            'email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            'idade': [
                r'(\d{1,2})\s*anos?',
                r'idade\s*:?\s*(\d{1,2})'
            ]
        }
    
    def process_message(self, text: str, image_url: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Processa mensagem e retorna análise completa"""
        try:
            result = {
                'text': text,
                'image_url': image_url,
                'user_id': user_id,
                'intent': None,
                'command_type': None,
                'category': None,
                'entities': {},
                'confidence': 0.0,
                'requires_clarification': False,
                'suggested_actions': [],
                'context': {}
            }
            
            if not text and not image_url:
                result['intent'] = 'unknown'
                result['requires_clarification'] = True
                return result
            
            # Normaliza texto
            normalized_text = self._normalize_text(text)
            
            # Detecção rápida de padrões
            quick_detection = self._quick_pattern_detection(normalized_text)
            if quick_detection:
                result.update(quick_detection)
            
            # Extração de entidades
            entities = self._extract_entities(normalized_text)
            result['entities'] = entities
            
            # Se não detectou padrão, usa OpenAI para análise mais profunda
            if not result['intent'] or result['confidence'] < 0.7:
                ai_analysis = self._analyze_with_openai(text, entities)
                if ai_analysis:
                    result.update(ai_analysis)
            
            # Processamento de imagem se fornecida
            if image_url:
                image_analysis = self._analyze_image(image_url)
                if image_analysis:
                    result['image_analysis'] = image_analysis
                    # Ajusta intent baseado na imagem
                    self._adjust_intent_with_image(result, image_analysis)
            
            # Determina ações sugeridas
            result['suggested_actions'] = self._get_suggested_actions(result)
            
            return result
            
        except Exception as e:
            current_app.logger.error(f'Erro no processamento NLP: {str(e)}')
            return {
                'text': text,
                'intent': 'error',
                'command_type': 'error',
                'entities': {},
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para processamento"""
        if not text:
            return ""
        
        # Converte para minúsculas
        text = text.lower()
        
        # Remove acentos
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e',
            'í': 'i', 'î': 'i',
            'ó': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'û': 'u',
            'ç': 'c'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove caracteres especiais extras
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _quick_pattern_detection(self, text: str) -> Optional[Dict[str, Any]]:
        """Detecção rápida usando padrões regex"""
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = 0.8  # Alta confiança para padrões específicos
                    
                    # Determina categoria baseada no tipo de comando
                    category = self._get_category_from_command(command_type)
                    
                    return {
                        'intent': command_type,
                        'command_type': command_type,
                        'category': category,
                        'confidence': confidence,
                        'matched_pattern': pattern,
                        'matched_groups': match.groups() if match.groups() else []
                    }
        
        return None
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrai entidades do texto"""
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            entities[entity_type] = []
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Flatten se necessário (para grupos de captura)
                    flat_matches = []
                    for match in matches:
                        if isinstance(match, tuple):
                            flat_matches.extend([m for m in match if m])
                        else:
                            flat_matches.append(match)
                    
                    entities[entity_type].extend(flat_matches)
            
            # Remove duplicatas
            entities[entity_type] = list(set(entities[entity_type]))
        
        # Remove entidades vazias
        entities = {k: v for k, v in entities.items() if v}
        
        return entities
    
    def _analyze_with_openai(self, text: str, entities: Dict) -> Optional[Dict[str, Any]]:
        """Análise mais profunda usando OpenAI"""
        try:
            prompt = f"""
            Analise a seguinte mensagem de um usuário do sistema Solicite IA (Angola) e determine:
            
            Mensagem: "{text}"
            Entidades detectadas: {json.dumps(entities, ensure_ascii=False)}
            
            Determine:
            1. Intenção principal (cadastro_prestador, busca_prestador, venda_produto, busca_produto, conexao_pessoal, achado_perdido, reclamacao, bolsa_estudo, mercado_financeiro, pesquisa_geral, saudacao, despedida, agradecimento, unknown)
            2. Categoria específica (se aplicável)
            3. Confiança (0.0 a 1.0)
            4. Se requer esclarecimento
            5. Contexto adicional
            
            Responda APENAS em JSON válido:
            {{
                "intent": "tipo_da_intencao",
                "category": "categoria_especifica",
                "confidence": 0.0,
                "requires_clarification": false,
                "context": {{
                    "missing_info": [],
                    "suggestions": []
                }}
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em análise de intenções para o sistema Solicite IA em Angola. Responda sempre em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            result['command_type'] = result.get('intent')
            
            return result
            
        except Exception as e:
            current_app.logger.error(f'Erro na análise OpenAI: {str(e)}')
            return None
    
    def _analyze_image(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Analisa imagem para determinar contexto"""
        try:
            # Aqui seria implementada a análise de imagem
            # Por enquanto, retorna análise básica
            return {
                'type': 'unknown',
                'confidence': 0.5,
                'description': 'Imagem recebida para análise'
            }
            
        except Exception as e:
            current_app.logger.error(f'Erro na análise de imagem: {str(e)}')
            return None
    
    def _adjust_intent_with_image(self, result: Dict, image_analysis: Dict):
        """Ajusta intenção baseada na análise da imagem"""
        image_type = image_analysis.get('type', 'unknown')
        
        # Se detectou produto na imagem e texto não é claro
        if image_type == 'product' and result['confidence'] < 0.7:
            result['intent'] = 'venda_produto'
            result['command_type'] = 'venda_produto'
            result['category'] = 'produto'
            result['confidence'] = max(result['confidence'], 0.7)
        
        # Se detectou pessoa na imagem
        elif image_type == 'person' and result['confidence'] < 0.7:
            result['intent'] = 'conexao_pessoal'
            result['command_type'] = 'conexao_pessoal'
            result['category'] = 'pessoa'
            result['confidence'] = max(result['confidence'], 0.6)
        
        # Se detectou documento
        elif image_type == 'document':
            if 'perdido' in result.get('text', '').lower():
                result['intent'] = 'achado_perdido'
                result['command_type'] = 'achado_perdido'
                result['category'] = 'documento'
    
    def _get_category_from_command(self, command_type: str) -> str:
        """Determina categoria baseada no tipo de comando"""
        category_map = {
            'cadastro_prestador': 'prestador',
            'busca_prestador': 'prestador',
            'venda_produto': 'produto',
            'busca_produto': 'produto',
            'conexao_pessoal': 'pessoa',
            'achado_perdido': 'item',
            'reclamacao': 'empresa',
            'bolsa_estudo': 'educacao',
            'mercado_financeiro': 'financeiro',
            'pesquisa_geral': 'informacao'
        }
        
        return category_map.get(command_type, 'geral')
    
    def _get_suggested_actions(self, result: Dict) -> List[str]:
        """Determina ações sugeridas baseadas na análise"""
        actions = []
        intent = result.get('intent')
        entities = result.get('entities', {})
        
        if intent == 'cadastro_prestador':
            if not entities.get('localizacao'):
                actions.append('solicitar_localizacao')
            if not entities.get('telefone'):
                actions.append('solicitar_contato')
        
        elif intent == 'busca_prestador':
            if not entities.get('localizacao'):
                actions.append('sugerir_localizacao')
            actions.append('mostrar_resultados')
        
        elif intent == 'venda_produto':
            if not entities.get('preco'):
                actions.append('solicitar_preco')
            if not entities.get('localizacao'):
                actions.append('solicitar_localizacao')
        
        elif intent == 'conexao_pessoal':
            actions.append('solicitar_dados_perfil')
        
        elif intent == 'reclamacao':
            actions.append('solicitar_detalhes_empresa')
            actions.append('solicitar_detalhes_problema')
        
        elif result.get('requires_clarification'):
            actions.append('solicitar_esclarecimento')
        
        return actions

