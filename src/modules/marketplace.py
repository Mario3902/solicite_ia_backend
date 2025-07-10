from typing import Dict, Any, List
from flask import current_app
from src.models import db, User, Produto, Conversa
import json
import re

class MarketplaceModule:
    """Módulo para gerenciar marketplace (compra e venda)"""
    
    def __init__(self):
        self.categories = {
            'eletronicos': ['telefone', 'celular', 'smartphone', 'iphone', 'samsung', 'computador', 'laptop', 'tablet', 'tv', 'televisao', 'radio', 'som'],
            'veiculos': ['carro', 'automovel', 'moto', 'motocicleta', 'bicicleta', 'bike', 'toyota', 'honda', 'nissan', 'hyundai'],
            'casa_jardim': ['movel', 'sofa', 'cama', 'mesa', 'cadeira', 'geladeira', 'fogao', 'microondas', 'maquina', 'eletrodomestico'],
            'roupas_acessorios': ['roupa', 'camisa', 'calca', 'vestido', 'sapato', 'tenis', 'bolsa', 'relogio', 'oculos', 'joia'],
            'esportes_lazer': ['bola', 'futebol', 'basquete', 'tenis', 'academia', 'bicicleta', 'patins', 'jogo', 'livro'],
            'bebes_criancas': ['bebe', 'crianca', 'brinquedo', 'carrinho', 'berco', 'cadeirinha', 'fralda', 'roupa infantil'],
            'animais': ['cao', 'cachorro', 'gato', 'passaro', 'peixe', 'animal', 'pet', 'racao', 'gaiola'],
            'servicos': ['curso', 'aula', 'treinamento', 'consultoria', 'design', 'fotografia', 'evento']
        }
        
        self.conditions = ['novo', 'usado', 'seminovo', 'para pecas']
    
    def process_message(self, nlp_result: Dict[str, Any], user: User, conversa: Conversa) -> Dict[str, Any]:
        """Processa mensagem relacionada ao marketplace"""
        try:
            command_type = nlp_result.get('command_type')
            
            if command_type == 'venda_produto':
                return self._handle_product_sale(nlp_result, user, conversa)
            elif command_type == 'busca_produto':
                return self._handle_product_search(nlp_result, user, conversa)
            else:
                return {
                    'success': False,
                    'text': 'Comando não reconhecido para marketplace.'
                }
                
        except Exception as e:
            current_app.logger.error(f'Erro no módulo marketplace: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao processar solicitação do marketplace.',
                'error': str(e)
            }
    
    def _handle_product_sale(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata venda de produtos"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai informações do produto
        product_info = self._extract_product_info(text, entities)
        
        if not product_info.get('name'):
            return {
                'success': True,
                'text': "Que produto você quer vender?\n\nExemplo: 'Vendo iPhone 12, usado, 150.000kz'",
                'requires_followup': True
            }
        
        if not product_info.get('price'):
            return {
                'success': True,
                'text': f"Qual o preço do(a) {product_info['name']}?\n\nExemplo: '50.000kz' ou '50.000 kwanzas'",
                'requires_followup': True
            }
        
        # Solicita informações adicionais se necessário
        return self._request_product_details(product_info, user, conversa)
    
    def _extract_product_info(self, text: str, entities: Dict) -> Dict[str, Any]:
        """Extrai informações do produto do texto"""
        info = {}
        
        # Extrai nome do produto
        info['name'] = self._extract_product_name(text)
        
        # Extrai preço
        prices = entities.get('preco', [])
        if prices:
            info['price'] = self._parse_price(prices[0])
        
        # Extrai localização
        locations = entities.get('localizacao', [])
        if locations:
            info['location'] = locations[0]
        
        # Extrai condição
        info['condition'] = self._extract_condition(text)
        
        # Extrai categoria
        info['category'] = self._extract_category(text)
        
        # Extrai marca/modelo
        info['brand'] = self._extract_brand(text)
        
        return info
    
    def _extract_product_name(self, text: str) -> str:
        """Extrai nome do produto"""
        # Padrões para extrair produto
        patterns = [
            r'vend[eo]\s+([^,]+?)(?:,|\s+por|\s+\d)',
            r'tenho\s+para\s+venda\s+([^,]+?)(?:,|$)',
            r'estou\s+vendendo\s+([^,]+?)(?:,|$)',
            r'produto\s*:\s*([^,]+?)(?:,|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                product = match.group(1).strip()
                # Remove palavras desnecessárias
                product = re.sub(r'\b(um|uma|o|a|meu|minha)\b', '', product, flags=re.IGNORECASE).strip()
                if len(product) > 2:
                    return product
        
        return None
    
    def _extract_condition(self, text: str) -> str:
        """Extrai condição do produto"""
        text_lower = text.lower()
        
        for condition in self.conditions:
            if condition in text_lower:
                return condition
        
        # Padrões específicos
        if any(word in text_lower for word in ['novo', 'lacrado', 'na caixa']):
            return 'novo'
        elif any(word in text_lower for word in ['usado', 'segunda mao']):
            return 'usado'
        elif 'seminovo' in text_lower:
            return 'seminovo'
        
        return 'usado'  # Padrão
    
    def _extract_category(self, text: str) -> str:
        """Extrai categoria do produto"""
        text_lower = text.lower()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return 'outros'
    
    def _extract_brand(self, text: str) -> str:
        """Extrai marca do produto"""
        brands = [
            'iphone', 'samsung', 'huawei', 'xiaomi', 'lg', 'sony',
            'toyota', 'honda', 'nissan', 'hyundai', 'volkswagen',
            'nike', 'adidas', 'puma', 'apple', 'microsoft'
        ]
        
        text_lower = text.lower()
        for brand in brands:
            if brand in text_lower:
                return brand.title()
        
        return None
    
    def _parse_price(self, price_str: str) -> float:
        """Converte string de preço para float"""
        try:
            # Remove caracteres não numéricos exceto vírgula e ponto
            price_clean = re.sub(r'[^\d,.]', '', price_str)
            
            # Substitui vírgula por ponto se for decimal
            if ',' in price_clean and '.' not in price_clean:
                price_clean = price_clean.replace(',', '.')
            elif ',' in price_clean and '.' in price_clean:
                # Remove pontos de milhares e mantém vírgula decimal
                price_clean = price_clean.replace('.', '').replace(',', '.')
            
            return float(price_clean)
        except:
            return 0.0
    
    def _request_product_details(self, product_info: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Solicita detalhes adicionais do produto"""
        name = product_info.get('name', 'produto')
        price = product_info.get('price', 0)
        
        text = f"📦 *Anúncio: {name}*\n"
        text += f"💰 *Preço:* {price:,.0f} kz\n\n"
        text += "Para completar seu anúncio, preciso de mais informações:\n\n"
        text += "📝 *Descrição* detalhada\n"
        text += "📍 *Localização* para entrega\n"
        text += "📱 *Contato* (se diferente do WhatsApp)\n"
        text += "🚚 *Entrega* disponível? Custo?\n"
        text += "🔄 *Aceita troca?*\n"
        text += "📸 *Foto* do produto (opcional)\n\n"
        text += "Pode enviar tudo numa mensagem ou uma informação por vez.\n\n"
        text += "*Exemplo:*\n"
        text += "iPhone 12 Pro Max, 256GB, cor azul, sem riscos\n"
        text += "Localização: Maianga, Luanda\n"
        text += "Entrega: 2.000kz em Luanda\n"
        text += "Aceita troca por iPhone 13"
        
        # Salva dados temporários
        temp_data = {
            'product_info': product_info,
            'step': 'collecting_details'
        }
        conversa.contexto_conversa = json.dumps(temp_data)
        db.session.commit()
        
        return {
            'success': True,
            'text': text,
            'requires_followup': True
        }
    
    def _handle_product_search(self, nlp_result: Dict, user: User, conversa: Conversa) -> Dict[str, Any]:
        """Trata busca por produtos"""
        text = nlp_result.get('text', '')
        entities = nlp_result.get('entities', {})
        
        # Extrai termo de busca
        search_term = self._extract_search_term(text)
        if not search_term:
            return {
                'success': True,
                'text': "O que você está procurando para comprar?\n\nExemplo: 'iPhone usado' ou 'carro Toyota'",
                'requires_followup': True
            }
        
        # Extrai filtros
        filters = self._extract_search_filters(text, entities)
        
        # Busca produtos
        products = self._search_products(search_term, filters)
        
        if not products:
            return self._handle_no_products_found(search_term, filters)
        
        return self._format_products_response(products, search_term)
    
    def _extract_search_term(self, text: str) -> str:
        """Extrai termo de busca"""
        patterns = [
            r'procur[ao]\s+([^,]+?)(?:,|$|\s+em|\s+por)',
            r'quero\s+comprar\s+([^,]+?)(?:,|$)',
            r'comprar?\s+([^,]+?)(?:,|$)',
            r'buscar?\s+([^,]+?)(?:,|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                term = match.group(1).strip()
                # Remove palavras desnecessárias
                term = re.sub(r'\b(um|uma|o|a|para)\b', '', term, flags=re.IGNORECASE).strip()
                if len(term) > 2:
                    return term
        
        return None
    
    def _extract_search_filters(self, text: str, entities: Dict) -> Dict[str, Any]:
        """Extrai filtros de busca"""
        filters = {}
        
        # Localização
        locations = entities.get('localizacao', [])
        if locations:
            filters['location'] = locations[0]
        
        # Preço
        prices = entities.get('preco', [])
        if prices:
            filters['max_price'] = self._parse_price(prices[0])
        
        # Condição
        condition = self._extract_condition(text)
        if condition != 'usado':  # Se não for o padrão
            filters['condition'] = condition
        
        # Categoria
        category = self._extract_category(text)
        if category != 'outros':
            filters['category'] = category
        
        return filters
    
    def _search_products(self, search_term: str, filters: Dict) -> List[Produto]:
        """Busca produtos no banco de dados"""
        query = Produto.query.filter(
            Produto.ativo == True,
            Produto.vendido == False
        )
        
        # Busca por termo
        if search_term:
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(f'%{search_term}%'),
                    Produto.descricao.ilike(f'%{search_term}%'),
                    Produto.marca.ilike(f'%{search_term}%'),
                    Produto.modelo.ilike(f'%{search_term}%')
                )
            )
        
        # Aplica filtros
        if filters.get('location'):
            query = query.filter(Produto.localizacao.ilike(f'%{filters["location"]}%'))
        
        if filters.get('max_price'):
            query = query.filter(Produto.preco <= filters['max_price'])
        
        if filters.get('condition'):
            query = query.filter(Produto.condicao.ilike(f'%{filters["condition"]}%'))
        
        if filters.get('category'):
            query = query.filter(Produto.categoria == filters['category'])
        
        return query.order_by(
            Produto.promovido.desc(),
            Produto.data_publicacao.desc()
        ).limit(10).all()
    
    def _format_products_response(self, products: List[Produto], search_term: str) -> Dict[str, Any]:
        """Formata resposta com lista de produtos"""
        text = f"🛒 Encontrei {len(products)} produto(s) para '{search_term}':\n\n"
        
        list_items = []
        
        for i, product in enumerate(products, 1):
            # Incrementa visualização
            product.incrementar_visualizacao()
            
            # Monta texto do produto
            product_text = f"*{product.nome}*\n"
            product_text += f"💰 {product.preco:,.0f} kz"
            
            if product.negociavel:
                product_text += " (negociável)"
            
            product_text += f"\n📍 {product.localizacao}\n"
            product_text += f"📦 {product.condicao.title()}\n"
            
            if product.marca:
                product_text += f"🏷️ {product.marca}\n"
            
            if product.entrega_disponivel:
                entrega_text = "🚚 Entrega disponível"
                if product.custo_entrega:
                    entrega_text += f" (+{product.custo_entrega:,.0f} kz)"
                product_text += entrega_text + "\n"
            
            if product.aceita_troca:
                product_text += "🔄 Aceita troca\n"
            
            # Contato do vendedor
            seller = User.query.get(product.usuario_id)
            if seller:
                product_text += f"📱 Contato: {seller.whatsapp_id}"
            
            text += f"{i}. {product_text}\n\n"
            
            # Adiciona à lista interativa
            price_text = f"{product.preco:,.0f} kz"
            if product.negociavel:
                price_text += " (neg.)"
            
            list_items.append({
                'id': f'product_{product.id}',
                'title': f"{product.nome} - {price_text}",
                'description': f"📍 {product.localizacao} | 📦 {product.condicao}"
            })
        
        text += "💡 *Dica:* Entre em contato diretamente com o vendedor para negociar!"
        
        buttons = [
            {'id': 'search_again', 'title': '🔍 Nova Busca'},
            {'id': 'sell_product', 'title': '💰 Vender Produto'},
            {'id': 'filter_results', 'title': '🔧 Filtrar'}
        ]
        
        return {
            'success': True,
            'text': text,
            'list_items': list_items if len(list_items) <= 10 else None,
            'buttons': buttons
        }
    
    def _handle_no_products_found(self, search_term: str, filters: Dict) -> Dict[str, Any]:
        """Trata caso onde não foram encontrados produtos"""
        text = f"😔 Não encontrei '{search_term}' no momento.\n\n"
        text += "💡 *Sugestões:*\n"
        text += "• Tente termos similares\n"
        text += "• Amplie a região de busca\n"
        text += "• Verifique a grafia\n"
        text += "• Cadastre um alerta para ser notificado\n\n"
        text += "Quer anunciar seu produto?"
        
        buttons = [
            {'id': 'search_similar', 'title': '🔍 Busca Similar'},
            {'id': 'sell_product', 'title': '💰 Vender Produto'},
            {'id': 'create_alert', 'title': '🔔 Criar Alerta'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons
        }
    
    def complete_product_listing(self, product_data: Dict, user: User) -> Dict[str, Any]:
        """Completa o cadastro do produto"""
        try:
            product = Produto(
                usuario_id=user.id,
                nome=product_data['nome'],
                descricao=product_data.get('descricao'),
                preco=product_data['preco'],
                categoria=product_data.get('categoria', 'outros'),
                condicao=product_data.get('condicao', 'usado'),
                localizacao=product_data.get('localizacao', 'Luanda'),
                marca=product_data.get('marca'),
                modelo=product_data.get('modelo'),
                cor=product_data.get('cor'),
                aceita_troca=product_data.get('aceita_troca', False),
                negociavel=product_data.get('negociavel', True),
                entrega_disponivel=product_data.get('entrega_disponivel', False),
                custo_entrega=product_data.get('custo_entrega'),
                imagem_url=product_data.get('imagem_url')
            )
            
            db.session.add(product)
            db.session.commit()
            
            text = f"✅ *Produto anunciado com sucesso!*\n\n"
            text += f"📦 *Produto:* {product.nome}\n"
            text += f"💰 *Preço:* {product.preco:,.0f} kz\n"
            text += f"📍 *Localização:* {product.localizacao}\n"
            text += f"📦 *Condição:* {product.condicao}\n\n"
            text += "Seu anúncio já está disponível para compradores!\n\n"
            text += "💡 *Dicas para vender mais rápido:*\n"
            text += "• Adicione fotos do produto\n"
            text += "• Seja honesto sobre a condição\n"
            text += "• Responda rapidamente aos interessados\n"
            text += "• Mantenha preço competitivo"
            
            return {
                'success': True,
                'text': text
            }
            
        except Exception as e:
            current_app.logger.error(f'Erro ao cadastrar produto: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao finalizar anúncio. Tente novamente.',
                'error': str(e)
            }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        try:
            Produto.query.limit(1).all()
            return True
        except:
            return False

