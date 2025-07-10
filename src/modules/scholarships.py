from typing import Dict, Any, List
from flask import current_app
import requests
import json

class ScholarshipsModule:
    """Módulo para buscar bolsas de estudo"""
    
    def __init__(self):
        self.areas = {
            'engenharia': ['engenharia', 'engenheiro', 'tecnico'],
            'medicina': ['medicina', 'medico', 'saude', 'enfermagem'],
            'direito': ['direito', 'advogado', 'juridico'],
            'economia': ['economia', 'economista', 'financas'],
            'educacao': ['educacao', 'pedagogia', 'professor'],
            'informatica': ['informatica', 'computacao', 'programacao', 'ti'],
            'administracao': ['administracao', 'gestao', 'negocios'],
            'psicologia': ['psicologia', 'psicologo'],
            'arquitetura': ['arquitetura', 'arquiteto'],
            'jornalismo': ['jornalismo', 'comunicacao', 'media']
        }
        
        self.levels = {
            'graduacao': ['graduacao', 'licenciatura', 'bacharelado'],
            'mestrado': ['mestrado', 'master'],
            'doutorado': ['doutorado', 'phd', 'doutor'],
            'pos_graduacao': ['pos graduacao', 'especializacao'],
            'tecnico': ['tecnico', 'profissionalizante']
        }
        
        self.countries = {
            'portugal': ['portugal', 'portugues', 'lisboa', 'porto'],
            'brasil': ['brasil', 'brasileiro', 'sao paulo', 'rio'],
            'eua': ['eua', 'estados unidos', 'america', 'americano'],
            'canada': ['canada', 'canadense'],
            'alemanha': ['alemanha', 'alemao', 'berlin'],
            'franca': ['franca', 'frances', 'paris'],
            'reino_unido': ['reino unido', 'inglaterra', 'londres'],
            'china': ['china', 'chines', 'beijing'],
            'africa_sul': ['africa do sul', 'sul africano']
        }
    
    def process_message(self, nlp_result: Dict[str, Any], user, conversa) -> Dict[str, Any]:
        """Processa mensagem sobre bolsas de estudo"""
        try:
            text = nlp_result.get('text', '')
            
            # Extrai critérios de busca
            criteria = self._extract_search_criteria(text)
            
            # Busca bolsas
            scholarships = self._search_scholarships(criteria)
            
            return self._format_scholarships_response(scholarships, criteria)
            
        except Exception as e:
            current_app.logger.error(f'Erro no módulo de bolsas: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao buscar bolsas de estudo.',
                'error': str(e)
            }
    
    def _extract_search_criteria(self, text: str) -> Dict[str, Any]:
        """Extrai critérios de busca"""
        criteria = {}
        text_lower = text.lower()
        
        # Área de estudo
        for area, keywords in self.areas.items():
            if any(keyword in text_lower for keyword in keywords):
                criteria['area'] = area
                break
        
        # Nível
        for level, keywords in self.levels.items():
            if any(keyword in text_lower for keyword in keywords):
                criteria['level'] = level
                break
        
        # País
        for country, keywords in self.countries.items():
            if any(keyword in text_lower for keyword in keywords):
                criteria['country'] = country
                break
        
        return criteria
    
    def _search_scholarships(self, criteria: Dict) -> List[Dict]:
        """Busca bolsas (simulado - integraria com APIs reais)"""
        # Simulação de dados de bolsas
        mock_scholarships = [
            {
                'title': 'Bolsa de Mestrado em Engenharia - Portugal',
                'institution': 'Universidade do Porto',
                'country': 'Portugal',
                'level': 'Mestrado',
                'area': 'Engenharia',
                'value': 'Mensalidade + 700€/mês',
                'deadline': '2024-03-15',
                'requirements': 'Licenciatura em Engenharia, IELTS 6.5',
                'link': 'https://sigarra.up.pt/up/pt/web_page.inicial'
            },
            {
                'title': 'Programa Chevening - Reino Unido',
                'institution': 'Governo Britânico',
                'country': 'Reino Unido',
                'level': 'Mestrado',
                'area': 'Todas as áreas',
                'value': 'Curso completo + subsistência',
                'deadline': '2024-11-02',
                'requirements': 'Graduação, 2 anos experiência, inglês fluente',
                'link': 'https://www.chevening.org/'
            },
            {
                'title': 'Bolsa Erasmus+ Angola',
                'institution': 'União Europeia',
                'country': 'Europa',
                'level': 'Graduação/Mestrado',
                'area': 'Diversas',
                'value': 'Variável por país',
                'deadline': '2024-02-01',
                'requirements': 'Estudante universitário angolano',
                'link': 'https://erasmus-plus.ec.europa.eu/'
            }
        ]
        
        # Filtra baseado nos critérios
        filtered = mock_scholarships
        
        if criteria.get('area'):
            area = criteria['area']
            filtered = [s for s in filtered if area.lower() in s['area'].lower() or s['area'] == 'Todas as áreas' or s['area'] == 'Diversas']
        
        if criteria.get('level'):
            level = criteria['level']
            filtered = [s for s in filtered if level.lower() in s['level'].lower()]
        
        if criteria.get('country'):
            country = criteria['country']
            country_map = {
                'portugal': 'Portugal',
                'reino_unido': 'Reino Unido',
                'brasil': 'Brasil'
            }
            target_country = country_map.get(country, country.title())
            filtered = [s for s in filtered if target_country in s['country'] or s['country'] == 'Europa']
        
        return filtered[:10]  # Máximo 10 resultados
    
    def _format_scholarships_response(self, scholarships: List[Dict], criteria: Dict) -> Dict[str, Any]:
        """Formata resposta com bolsas encontradas"""
        if not scholarships:
            return self._handle_no_scholarships_found(criteria)
        
        # Monta critérios de busca
        criteria_text = []
        if criteria.get('area'):
            criteria_text.append(f"Área: {criteria['area']}")
        if criteria.get('level'):
            criteria_text.append(f"Nível: {criteria['level']}")
        if criteria.get('country'):
            criteria_text.append(f"País: {criteria['country']}")
        
        criteria_str = " | ".join(criteria_text) if criteria_text else "Todas as áreas"
        
        text = f"🎓 *BOLSAS DE ESTUDO ENCONTRADAS*\n\n"
        text += f"🔍 *Critérios:* {criteria_str}\n"
        text += f"📊 *Resultados:* {len(scholarships)} bolsa(s)\n\n"
        
        list_items = []
        
        for i, scholarship in enumerate(scholarships, 1):
            # Monta texto da bolsa
            sch_text = f"*{scholarship['title']}*\n"
            sch_text += f"🏫 {scholarship['institution']}\n"
            sch_text += f"🌍 {scholarship['country']}\n"
            sch_text += f"🎯 {scholarship['level']} em {scholarship['area']}\n"
            sch_text += f"💰 {scholarship['value']}\n"
            sch_text += f"📅 Prazo: {scholarship['deadline']}\n"
            sch_text += f"📋 {scholarship['requirements']}\n"
            sch_text += f"🔗 {scholarship['link']}"
            
            text += f"{i}. {sch_text}\n\n"
            
            # Adiciona à lista interativa
            list_items.append({
                'id': f'scholarship_{i}',
                'title': scholarship['title'],
                'description': f"🏫 {scholarship['institution']} | 📅 {scholarship['deadline']}"
            })
        
        text += "💡 *Dicas:*\n"
        text += "• Verifique os requisitos cuidadosamente\n"
        text += "• Prepare documentação com antecedência\n"
        text += "• Candidate-se a múltiplas bolsas\n"
        text += "• Busque orientação acadêmica"
        
        buttons = [
            {'id': 'search_again', 'title': '🔍 Nova Busca'},
            {'id': 'filter_scholarships', 'title': '🔧 Filtrar'},
            {'id': 'scholarship_tips', 'title': '💡 Dicas'}
        ]
        
        return {
            'success': True,
            'text': text,
            'list_items': list_items if len(list_items) <= 10 else None,
            'buttons': buttons
        }
    
    def _handle_no_scholarships_found(self, criteria: Dict) -> Dict[str, Any]:
        """Trata caso onde não foram encontradas bolsas"""
        text = "😔 Não encontrei bolsas com esses critérios no momento.\n\n"
        text += "💡 *Sugestões:*\n"
        text += "• Amplie os critérios de busca\n"
        text += "• Tente áreas relacionadas\n"
        text += "• Considere outros países\n"
        text += "• Verifique novamente em alguns dias\n\n"
        text += "Quer tentar uma nova busca?"
        
        buttons = [
            {'id': 'broaden_search', 'title': '🔍 Ampliar Busca'},
            {'id': 'all_scholarships', 'title': '📋 Ver Todas'},
            {'id': 'scholarship_alerts', 'title': '🔔 Criar Alerta'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons
        }
    
    def get_scholarship_tips(self) -> Dict[str, Any]:
        """Retorna dicas para bolsas de estudo"""
        text = "💡 *DICAS PARA BOLSAS DE ESTUDO*\n\n"
        text += "📋 *PREPARAÇÃO:*\n"
        text += "• Pesquise com antecedência (6-12 meses)\n"
        text += "• Mantenha boas notas acadêmicas\n"
        text += "• Desenvolva atividades extracurriculares\n"
        text += "• Aprenda idiomas (inglês, português, etc.)\n\n"
        text += "📄 *DOCUMENTAÇÃO:*\n"
        text += "• Histórico escolar traduzido\n"
        text += "• Certificados de idiomas (IELTS, TOEFL)\n"
        text += "• Cartas de recomendação\n"
        text += "• Carta de motivação personalizada\n"
        text += "• Currículo atualizado\n\n"
        text += "🎯 *CANDIDATURA:*\n"
        text += "• Leia todos os requisitos\n"
        text += "• Candidate-se a múltiplas bolsas\n"
        text += "• Respeite prazos rigorosamente\n"
        text += "• Personalize cada aplicação\n"
        text += "• Prepare-se para entrevistas\n\n"
        text += "🔗 *RECURSOS ÚTEIS:*\n"
        text += "• Portal Camões (Portugal)\n"
        text += "• Chevening (Reino Unido)\n"
        text += "• Fulbright (EUA)\n"
        text += "• DAAD (Alemanha)\n"
        text += "• Campus France (França)"
        
        return {
            'success': True,
            'text': text
        }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        return True

