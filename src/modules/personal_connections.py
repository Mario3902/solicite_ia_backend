from typing import Dict, Any, List
from flask import current_app
from src.models import db, User, ConexaoPessoal, Conversa
import json
import re

class PersonalConnectionsModule:
    """Módulo para gerenciar conexões pessoais e relacionamentos"""
    
    def __init__(self):
        self.interests = {
            'amizade': ['amizade', 'amigo', 'amiga', 'conhecer pessoas', 'fazer amigos'],
            'namoro': ['namoro', 'namorar', 'relacionamento', 'parceiro', 'parceira'],
            'casamento': ['casamento', 'casar', 'matrimonio', 'esposo', 'esposa'],
            'networking': ['networking', 'profissional', 'negocios', 'trabalho', 'carreira']
        }
        
        self.physical_types = {
            'atletico': ['atletico', 'musculoso', 'forte', 'academia'],
            'magro': ['magro', 'esbelto', 'fino'],
            'normal': ['normal', 'medio', 'comum'],
            'plus_size': ['plus size', 'gordinho', 'cheio', 'robusto']
        }
    
    def process_message(self, nlp_result: Dict[str, Any], user: User, conversa: Conversa) -> Dict[str, Any]:
        """Processa mensagem relacionada a conexões pessoais"""
        try:
            text = nlp_result.get('text', '')
            
            # Verifica se é cadastro ou busca
            if self._is_registration(text):
                return self._handle_connection_registration(nlp_result, user, conversa)
            else:
                return self._handle_connection_search(nlp_result, user, conversa)
                
        except Exception as e:
            current_app.logger.error(f'Erro no módulo de conexões: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao processar solicitação de conexões.',
                'error': str(e)
            }
    
    def _is_registration(self, text: str) -> bool:
        """Determina se é um cadastro ou busca"""
        registration_indicators = [
            'sou', 'tenho', 'anos', 'idade', 'meu nome',
            'me chamo', 'trabalho como', 'profissao'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in registration_indicators)
    
    def _handle_connection_registration(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata cadastro de perfil pessoal"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai informações básicas
        profile_info = self._extract_profile_info(text, entities)
        
        # Verifica se já tem perfil
        existing = ConexaoPessoal.query.filter_by(usuario_id=user.id).first()
        if existing:
            return {
                'success': True,
                'text': f"Você já tem um perfil cadastrado como {existing.nome}.\n\nDeseja atualizar suas informações?",
                'buttons': [
                    {'id': 'update_profile', 'title': '✏️ Atualizar'},
                    {'id': 'view_profile', 'title': '👁️ Ver Perfil'},
                    {'id': 'search_connections', 'title': '🔍 Buscar Pessoas'}
                ]
            }
        
        # Solicita informações obrigatórias
        missing_info = self._check_required_info(profile_info)
        if missing_info:
            return self._request_missing_info(missing_info, profile_info, user, conversa)
        
        # Solicita informações adicionais
        return self._request_additional_profile_info(profile_info, user, conversa)
    
    def _extract_profile_info(self, text: str, entities: Dict) -> Dict[str, Any]:
        """Extrai informações do perfil"""
        info = {}
        
        # Extrai gênero
        info['gender'] = self._extract_gender(text)
        
        # Extrai idade
        ages = entities.get('idade', [])
        if ages:
            try:
                info['age'] = int(ages[0])
            except:
                pass
        
        # Extrai interesse
        info['interest'] = self._extract_interest(text)
        
        # Extrai localização
        locations = entities.get('localizacao', [])
        if locations:
            info['location'] = locations[0]
        
        # Extrai estado civil
        info['marital_status'] = self._extract_marital_status(text)
        
        # Extrai tipo físico
        info['physical_type'] = self._extract_physical_type(text)
        
        # Extrai profissão
        info['profession'] = self._extract_profession(text)
        
        return info
    
    def _extract_gender(self, text: str) -> str:
        """Extrai gênero do texto"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['homem', 'masculino', 'rapaz', 'senhor']):
            return 'masculino'
        elif any(word in text_lower for word in ['mulher', 'feminino', 'rapariga', 'senhora', 'dama']):
            return 'feminino'
        
        return None
    
    def _extract_interest(self, text: str) -> str:
        """Extrai tipo de interesse"""
        text_lower = text.lower()
        
        for interest, keywords in self.interests.items():
            if any(keyword in text_lower for keyword in keywords):
                return interest
        
        return 'amizade'  # Padrão
    
    def _extract_marital_status(self, text: str) -> str:
        """Extrai estado civil"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['solteiro', 'solteira', 'single']):
            return 'solteiro'
        elif any(word in text_lower for word in ['casado', 'casada', 'esposo', 'esposa']):
            return 'casado'
        elif any(word in text_lower for word in ['divorciado', 'divorciada', 'separado', 'separada']):
            return 'divorciado'
        elif any(word in text_lower for word in ['viuvo', 'viuva']):
            return 'viuvo'
        
        return 'solteiro'  # Padrão
    
    def _extract_physical_type(self, text: str) -> str:
        """Extrai tipo físico"""
        text_lower = text.lower()
        
        for phys_type, keywords in self.physical_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return phys_type
        
        return None
    
    def _extract_profession(self, text: str) -> str:
        """Extrai profissão"""
        patterns = [
            r'trabalho\s+como\s+([^,\.]+)',
            r'sou\s+([^,\.]+?)(?:\s+e\s|\s*,|\s*\.)',
            r'profissao\s*:?\s*([^,\.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                profession = match.group(1).strip()
                if len(profession) > 2 and profession.lower() not in ['homem', 'mulher', 'anos']:
                    return profession
        
        return None
    
    def _check_required_info(self, profile_info: Dict) -> List[str]:
        """Verifica informações obrigatórias faltantes"""
        missing = []
        
        if not profile_info.get('gender'):
            missing.append('genero')
        
        if not profile_info.get('age'):
            missing.append('idade')
        
        if not profile_info.get('interest'):
            missing.append('interesse')
        
        if not profile_info.get('location'):
            missing.append('localizacao')
        
        return missing
    
    def _request_missing_info(self, missing_info: List[str], profile_info: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita informações faltantes"""
        if 'genero' in missing_info:
            text = "Para criar seu perfil, preciso saber: você é homem ou mulher?"
            buttons = [
                {'id': 'gender_male', 'title': '👨 Homem'},
                {'id': 'gender_female', 'title': '👩 Mulher'}
            ]
        elif 'idade' in missing_info:
            text = "Qual é sua idade?\n\nExemplo: '25 anos' ou 'tenho 30 anos'"
            buttons = None
        elif 'interesse' in missing_info:
            text = "Que tipo de conexão você busca?"
            buttons = [
                {'id': 'interest_friendship', 'title': '👫 Amizade'},
                {'id': 'interest_dating', 'title': '💕 Namoro'},
                {'id': 'interest_marriage', 'title': '💍 Casamento'},
                {'id': 'interest_networking', 'title': '🤝 Networking'}
            ]
        elif 'localizacao' in missing_info:
            text = "Em que região você está?\n\nExemplo: 'Luanda', 'Maianga', 'Cacuaco'"
            buttons = None
        else:
            text = "Preciso de mais informações para criar seu perfil."
            buttons = None
        
        # Salva dados temporários
        temp_data = {
            'profile_info': profile_info,
            'missing_info': missing_info,
            'step': 'collecting_required'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons,
            'requires_followup': True
        }
    
    def _request_additional_profile_info(self, profile_info: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita informações adicionais do perfil"""
        gender = profile_info.get('gender', 'pessoa')
        age = profile_info.get('age', '')
        interest = profile_info.get('interest', 'conexões')
        location = profile_info.get('location', '')
        
        text = f"✅ Informações básicas registradas:\n"
        text += f"👤 {gender.title()}, {age} anos\n"
        text += f"💕 Interesse: {interest}\n"
        text += f"📍 Localização: {location}\n\n"
        text += "Para completar seu perfil, pode adicionar (opcional):\n\n"
        text += "📝 *Descrição* pessoal\n"
        text += "💼 *Profissão*\n"
        text += "🎓 *Escolaridade*\n"
        text += "🏃 *Tipo físico*\n"
        text += "📏 *Altura*\n"
        text += "🎯 *Hobbies/Interesses*\n"
        text += "⛪ *Religião*\n"
        text += "👶 *Filhos* (tem/quer)\n\n"
        text += "Pode enviar tudo numa mensagem ou pular para finalizar.\n\n"
        text += "*Exemplo:*\n"
        text += "Sou professor, ensino superior, 1.75m, atlético\n"
        text += "Gosto de futebol, cinema e viajar\n"
        text += "Cristão, não tenho filhos mas quero"
        
        # Salva dados temporários
        temp_data = {
            'profile_info': profile_info,
            'step': 'collecting_additional'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        buttons = [
            {'id': 'complete_profile', 'title': '✅ Finalizar Perfil'},
            {'id': 'add_photo', 'title': '📸 Adicionar Foto'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons,
            'requires_followup': True
        }
    
    def _handle_connection_search(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata busca por conexões"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai critérios de busca
        search_criteria = self._extract_search_criteria(text, entities)
        
        # Busca conexões
        connections = self._search_connections(search_criteria, user.id)
        
        if not connections:
            return self._handle_no_connections_found(search_criteria)
        
        return self._format_connections_response(connections, search_criteria)
    
    def _extract_search_criteria(self, text: str, entities: Dict) -> Dict[str, Any]:
        """Extrai critérios de busca"""
        criteria = {}
        
        # Gênero procurado
        criteria['gender'] = self._extract_target_gender(text)
        
        # Interesse
        criteria['interest'] = self._extract_interest(text)
        
        # Idade
        ages = entities.get('idade', [])
        if ages:
            try:
                criteria['age'] = int(ages[0])
            except:
                pass
        
        # Localização
        locations = entities.get('localizacao', [])
        if locations:
            criteria['location'] = locations[0]
        
        # Tipo físico
        criteria['physical_type'] = self._extract_physical_type(text)
        
        return criteria
    
    def _extract_target_gender(self, text: str) -> str:
        """Extrai gênero procurado"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['procuro homem', 'quero homem', 'homem para']):
            return 'masculino'
        elif any(word in text_lower for word in ['procuro mulher', 'quero mulher', 'mulher para']):
            return 'feminino'
        
        return None
    
    def _search_connections(self, criteria: Dict, exclude_user_id: int) -> List[ConexaoPessoal]:
        """Busca conexões baseado nos critérios"""
        query = ConexaoPessoal.query.filter(
            ConexaoPessoal.ativo == True,
            ConexaoPessoal.usuario_id != exclude_user_id
        )
        
        # Aplica filtros
        if criteria.get('gender'):
            query = query.filter(ConexaoPessoal.genero == criteria['gender'])
        
        if criteria.get('interest'):
            # Busca interesses compatíveis
            compatible_interests = self._get_compatible_interests(criteria['interest'])
            query = query.filter(ConexaoPessoal.interesse.in_(compatible_interests))
        
        if criteria.get('age'):
            # Busca idade próxima (±5 anos)
            age = criteria['age']
            query = query.filter(
                ConexaoPessoal.idade.between(age - 5, age + 5)
            )
        
        if criteria.get('location'):
            query = query.filter(ConexaoPessoal.localizacao.ilike(f'%{criteria["location"]}%'))
        
        if criteria.get('physical_type'):
            query = query.filter(ConexaoPessoal.categoria_fisica.ilike(f'%{criteria["physical_type"]}%'))
        
        return query.order_by(
            ConexaoPessoal.verificado.desc(),
            ConexaoPessoal.ultimo_acesso.desc()
        ).limit(10).all()
    
    def _get_compatible_interests(self, interest: str) -> List[str]:
        """Retorna interesses compatíveis"""
        compatibility = {
            'amizade': ['amizade', 'networking'],
            'namoro': ['namoro', 'casamento'],
            'casamento': ['casamento', 'namoro'],
            'networking': ['networking', 'amizade']
        }
        
        return compatibility.get(interest, [interest])
    
    def _format_connections_response(self, connections: List[ConexaoPessoal], criteria: Dict) -> Dict[str, Any]:
        """Formata resposta com lista de conexões"""
        text = f"💕 Encontrei {len(connections)} pessoa(s) que pode(m) interessar:\n\n"
        
        list_items = []
        
        for i, connection in enumerate(connections, 1):
            # Incrementa visualização
            connection.incrementar_visualizacao()
            
            # Monta texto da conexão (sem dados sensíveis)
            conn_text = f"*{connection.nome}*\n"
            conn_text += f"👤 {connection.genero.title()}, {connection.idade} anos\n"
            conn_text += f"📍 {connection.localizacao}\n"
            conn_text += f"💕 Interesse: {connection.interesse}\n"
            
            if connection.profissao:
                conn_text += f"💼 {connection.profissao}\n"
            
            if connection.categoria_fisica:
                conn_text += f"🏃 {connection.categoria_fisica}\n"
            
            if connection.altura:
                conn_text += f"📏 {connection.altura}\n"
            
            if connection.verificado:
                conn_text += "✅ Perfil verificado\n"
            
            if connection.bio:
                bio_short = connection.bio[:100] + "..." if len(connection.bio) > 100 else connection.bio
                conn_text += f"📝 {bio_short}\n"
            
            conn_text += f"👁️ {connection.visualizacoes} visualizações"
            
            text += f"{i}. {conn_text}\n\n"
            
            # Adiciona à lista interativa
            list_items.append({
                'id': f'connection_{connection.id}',
                'title': f"{connection.nome}, {connection.idade} anos",
                'description': f"📍 {connection.localizacao} | 💕 {connection.interesse}"
            })
        
        text += "💡 *Para conectar:* Selecione um perfil para ver mais detalhes e entrar em contato."
        
        buttons = [
            {'id': 'search_again', 'title': '🔍 Nova Busca'},
            {'id': 'create_profile', 'title': '➕ Criar Perfil'},
            {'id': 'filter_results', 'title': '🔧 Filtrar'}
        ]
        
        return {
            'success': True,
            'text': text,
            'list_items': list_items if len(list_items) <= 10 else None,
            'buttons': buttons
        }
    
    def _handle_no_connections_found(self, criteria: Dict) -> Dict[str, Any]:
        """Trata caso onde não foram encontradas conexões"""
        text = "😔 Não encontrei pessoas com esse perfil no momento.\n\n"
        text += "💡 *Sugestões:*\n"
        text += "• Amplie os critérios de busca\n"
        text += "• Tente uma região próxima\n"
        text += "• Crie seu perfil para ser encontrado\n"
        text += "• Volte mais tarde, novos perfis são adicionados diariamente\n\n"
        text += "Quer criar seu perfil?"
        
        buttons = [
            {'id': 'create_profile', 'title': '➕ Criar Perfil'},
            {'id': 'broaden_search', 'title': '🔍 Ampliar Busca'},
            {'id': 'search_again', 'title': '🔄 Tentar Novamente'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons
        }
    
    def complete_profile_registration(self, profile_data: Dict, user: User) -> Dict[str, Any]:
        """Completa o cadastro do perfil"""
        try:
            profile = ConexaoPessoal(
                usuario_id=user.id,
                nome=profile_data.get('nome', user.nome or 'Usuário'),
                idade=profile_data['idade'],
                genero=profile_data['genero'],
                estado_civil=profile_data.get('estado_civil', 'solteiro'),
                interesse=profile_data['interesse'],
                categoria_fisica=profile_data.get('categoria_fisica'),
                altura=profile_data.get('altura'),
                profissao=profile_data.get('profissao'),
                escolaridade=profile_data.get('escolaridade'),
                localizacao=profile_data['localizacao'],
                bio=profile_data.get('bio'),
                interesses_hobbies=profile_data.get('interesses_hobbies'),
                religiao=profile_data.get('religiao'),
                fumante=profile_data.get('fumante'),
                bebe=profile_data.get('bebe'),
                tem_filhos=profile_data.get('tem_filhos'),
                quer_filhos=profile_data.get('quer_filhos'),
                imagem_url=profile_data.get('imagem_url')
            )
            
            db.session.add(profile)
            db.session.commit()
            
            text = f"✅ *Perfil criado com sucesso!*\n\n"
            text += f"👤 *Nome:* {profile.nome}\n"
            text += f"🎂 *Idade:* {profile.idade} anos\n"
            text += f"👫 *Gênero:* {profile.genero}\n"
            text += f"💕 *Interesse:* {profile.interesse}\n"
            text += f"📍 *Localização:* {profile.localizacao}\n\n"
            text += "Seu perfil já está disponível para outras pessoas!\n\n"
            text += "💡 *Dicas:*\n"
            text += "• Adicione uma foto para mais visualizações\n"
            text += "• Mantenha seu perfil atualizado\n"
            text += "• Seja respeitoso nas conversas\n"
            text += "• Use o sistema com responsabilidade"
            
            return {
                'success': True,
                'text': text
            }
            
        except Exception as e:
            current_app.logger.error(f'Erro ao criar perfil: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao finalizar perfil. Tente novamente.',
                'error': str(e)
            }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        try:
            ConexaoPessoal.query.limit(1).all()
            return True
        except:
            return False

