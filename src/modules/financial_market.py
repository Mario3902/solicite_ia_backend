from typing import Dict, Any, List
from flask import current_app
import requests
import json
from datetime import datetime

class FinancialMarketModule:
    """Módulo para informações do mercado financeiro"""
    
    def __init__(self):
        self.currencies = {
            'usd': ['dolar', 'dollar', 'usd'],
            'eur': ['euro', 'eur'],
            'gbp': ['libra', 'pound', 'gbp'],
            'brl': ['real', 'brasileiro', 'brl'],
            'zar': ['rand', 'sul africano', 'zar']
        }
        
        self.cryptocurrencies = {
            'bitcoin': ['bitcoin', 'btc'],
            'ethereum': ['ethereum', 'eth'],
            'cardano': ['cardano', 'ada'],
            'solana': ['solana', 'sol'],
            'dogecoin': ['dogecoin', 'doge']
        }
    
    def process_message(self, nlp_result: Dict[str, Any], user, conversa) -> Dict[str, Any]:
        """Processa mensagem sobre mercado financeiro"""
        try:
            text = nlp_result.get('text', '').lower()
            
            # Determina tipo de consulta
            if any(crypto in text for cryptos in self.cryptocurrencies.values() for crypto in cryptos):
                return self._handle_crypto_query(text)
            elif any(curr in text for currs in self.currencies.values() for curr in currs):
                return self._handle_currency_query(text)
            elif any(word in text for word in ['acao', 'acoes', 'bolsa', 'stock']):
                return self._handle_stock_query(text)
            else:
                return self._handle_general_market_info()
                
        except Exception as e:
            current_app.logger.error(f'Erro no módulo financeiro: {str(e)}')
            return {
                'success': False,
                'text': 'Erro ao buscar informações financeiras.',
                'error': str(e)
            }
    
    def _handle_crypto_query(self, text: str) -> Dict[str, Any]:
        """Trata consultas sobre criptomoedas"""
        # Identifica criptomoeda
        crypto = None
        for crypto_name, keywords in self.cryptocurrencies.items():
            if any(keyword in text for keyword in keywords):
                crypto = crypto_name
                break
        
        # Dados simulados (integraria com API real como CoinGecko)
        crypto_data = self._get_mock_crypto_data(crypto)
        
        if not crypto_data:
            return {
                'success': True,
                'text': "Qual criptomoeda você quer consultar?\n\nExemplos: Bitcoin, Ethereum, Cardano, Solana"
            }
        
        text_response = f"₿ *{crypto_data['name']} ({crypto_data['symbol'].upper()})*\n\n"
        text_response += f"💰 *Preço atual:* ${crypto_data['price']:,.2f}\n"
        text_response += f"📈 *24h:* {crypto_data['change_24h']:+.2f}%\n"
        text_response += f"📊 *7 dias:* {crypto_data['change_7d']:+.2f}%\n"
        text_response += f"💎 *Market Cap:* ${crypto_data['market_cap']:,.0f}\n"
        text_response += f"📊 *Volume 24h:* ${crypto_data['volume_24h']:,.0f}\n\n"
        text_response += f"🕐 *Atualizado:* {datetime.now().strftime('%H:%M')}\n\n"
        text_response += "💡 *Lembre-se:* Criptomoedas são investimentos de alto risco!"
        
        buttons = [
            {'id': 'other_crypto', 'title': '₿ Outra Crypto'},
            {'id': 'crypto_news', 'title': '📰 Notícias'},
            {'id': 'market_overview', 'title': '📊 Visão Geral'}
        ]
        
        return {
            'success': True,
            'text': text_response,
            'buttons': buttons
        }
    
    def _handle_currency_query(self, text: str) -> Dict[str, Any]:
        """Trata consultas sobre moedas"""
        # Identifica moeda
        currency = None
        for curr_code, keywords in self.currencies.items():
            if any(keyword in text for keyword in keywords):
                currency = curr_code
                break
        
        # Dados simulados (integraria com API real como ExchangeRate-API)
        currency_data = self._get_mock_currency_data(currency)
        
        if not currency_data:
            return {
                'success': True,
                'text': "Qual moeda você quer consultar?\n\nExemplos: Dólar, Euro, Real brasileiro, Libra"
            }
        
        text_response = f"💱 *{currency_data['name']} (AOA/{currency_data['code'].upper()})*\n\n"
        text_response += f"💰 *Taxa atual:* {currency_data['rate']:,.2f} AOA\n"
        text_response += f"📈 *Variação hoje:* {currency_data['change']:+.2f}%\n"
        text_response += f"📊 *Máxima hoje:* {currency_data['high']:,.2f} AOA\n"
        text_response += f"📉 *Mínima hoje:* {currency_data['low']:,.2f} AOA\n\n"
        text_response += f"🕐 *Atualizado:* {datetime.now().strftime('%H:%M')}\n\n"
        text_response += "💡 *Fonte:* Banco Nacional de Angola (simulado)"
        
        buttons = [
            {'id': 'other_currency', 'title': '💱 Outra Moeda'},
            {'id': 'currency_converter', 'title': '🔄 Conversor'},
            {'id': 'currency_history', 'title': '📈 Histórico'}
        ]
        
        return {
            'success': True,
            'text': text_response,
            'buttons': buttons
        }
    
    def _handle_stock_query(self, text: str) -> Dict[str, Any]:
        """Trata consultas sobre ações"""
        # Dados simulados da bolsa angolana
        stock_data = {
            'BODIVA': {'price': 1250.00, 'change': 2.5, 'volume': 15000},
            'BAI': {'price': 890.50, 'change': -1.2, 'volume': 8500},
            'SONANGOL': {'price': 2100.00, 'change': 0.8, 'volume': 12000}
        }
        
        text_response = "📈 *BOLSA DE VALORES - BODIVA*\n\n"
        
        for stock, data in stock_data.items():
            change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
            text_response += f"*{stock}*\n"
            text_response += f"💰 {data['price']:,.2f} AOA\n"
            text_response += f"{change_emoji} {data['change']:+.1f}%\n"
            text_response += f"📊 Volume: {data['volume']:,}\n\n"
        
        text_response += f"🕐 *Atualizado:* {datetime.now().strftime('%H:%M')}\n\n"
        text_response += "💡 *Aviso:* Dados simulados para demonstração"
        
        buttons = [
            {'id': 'stock_details', 'title': '📊 Detalhes'},
            {'id': 'market_news', 'title': '📰 Notícias'},
            {'id': 'investment_tips', 'title': '💡 Dicas'}
        ]
        
        return {
            'success': True,
            'text': text_response,
            'buttons': buttons
        }
    
    def _handle_general_market_info(self) -> Dict[str, Any]:
        """Informações gerais do mercado"""
        text = "📊 *MERCADO FINANCEIRO*\n\n"
        text += "Que informação você precisa?\n\n"
        text += "💱 *Câmbio:*\n"
        text += "• Dólar americano (USD)\n"
        text += "• Euro (EUR)\n"
        text += "• Real brasileiro (BRL)\n\n"
        text += "₿ *Criptomoedas:*\n"
        text += "• Bitcoin (BTC)\n"
        text += "• Ethereum (ETH)\n"
        text += "• Outras altcoins\n\n"
        text += "📈 *Ações:*\n"
        text += "• Bolsa angolana (BODIVA)\n"
        text += "• Principais empresas\n\n"
        text += "*Exemplos de comandos:*\n"
        text += "• 'Preço do Bitcoin'\n"
        text += "• 'Dólar hoje'\n"
        text += "• 'Ações da BAI'"
        
        buttons = [
            {'id': 'currencies', 'title': '💱 Moedas'},
            {'id': 'cryptocurrencies', 'title': '₿ Criptomoedas'},
            {'id': 'stocks', 'title': '📈 Ações'},
            {'id': 'market_news', 'title': '📰 Notícias'}
        ]
        
        return {
            'success': True,
            'text': text,
            'buttons': buttons
        }
    
    def _get_mock_crypto_data(self, crypto: str) -> Dict[str, Any]:
        """Dados simulados de criptomoedas"""
        mock_data = {
            'bitcoin': {
                'name': 'Bitcoin',
                'symbol': 'btc',
                'price': 43250.75,
                'change_24h': 2.34,
                'change_7d': -1.56,
                'market_cap': 847000000000,
                'volume_24h': 18500000000
            },
            'ethereum': {
                'name': 'Ethereum',
                'symbol': 'eth',
                'price': 2580.90,
                'change_24h': 1.87,
                'change_7d': 3.21,
                'market_cap': 310000000000,
                'volume_24h': 12300000000
            },
            'cardano': {
                'name': 'Cardano',
                'symbol': 'ada',
                'price': 0.485,
                'change_24h': -0.95,
                'change_7d': 2.14,
                'market_cap': 17200000000,
                'volume_24h': 285000000
            }
        }
        
        return mock_data.get(crypto)
    
    def _get_mock_currency_data(self, currency: str) -> Dict[str, Any]:
        """Dados simulados de moedas"""
        mock_data = {
            'usd': {
                'name': 'Dólar Americano',
                'code': 'usd',
                'rate': 825.50,
                'change': 0.75,
                'high': 828.20,
                'low': 823.10
            },
            'eur': {
                'name': 'Euro',
                'code': 'eur',
                'rate': 895.30,
                'change': -0.45,
                'high': 898.50,
                'low': 892.80
            },
            'brl': {
                'name': 'Real Brasileiro',
                'code': 'brl',
                'rate': 165.75,
                'change': 1.20,
                'high': 167.20,
                'low': 164.30
            }
        }
        
        return mock_data.get(currency)
    
    def get_investment_tips(self) -> Dict[str, Any]:
        """Dicas de investimento"""
        text = "💡 *DICAS DE INVESTIMENTO*\n\n"
        text += "⚠️ *IMPORTANTE:* Estas são dicas educacionais, não conselhos financeiros!\n\n"
        text += "📚 *PRINCÍPIOS BÁSICOS:*\n"
        text += "• Nunca invista mais do que pode perder\n"
        text += "• Diversifique seus investimentos\n"
        text += "• Estude antes de investir\n"
        text += "• Tenha objetivos claros\n"
        text += "• Mantenha reserva de emergência\n\n"
        text += "🎯 *ESTRATÉGIAS:*\n"
        text += "• Investimento a longo prazo\n"
        text += "• Aportes regulares (DCA)\n"
        text += "• Reavaliação periódica\n"
        text += "• Controle emocional\n\n"
        text += "⚠️ *RISCOS:*\n"
        text += "• Volatilidade do mercado\n"
        text += "• Risco de liquidez\n"
        text += "• Risco cambial\n"
        text += "• Risco regulatório\n\n"
        text += "📞 *BUSQUE ORIENTAÇÃO:* Consulte sempre um consultor financeiro qualificado!"
        
        return {
            'success': True,
            'text': text
        }
    
    def get_status(self) -> bool:
        """Retorna status do módulo"""
        return True

