import requests
import json
import logging
from flask import current_app
from typing import Optional, List, Dict, Any

class WhatsAppIntegration:
    """Classe para integração com WhatsApp Business API"""
    
    def __init__(self):
        self.base_url = current_app.config.get('WHATSAPP_API_BASE_URL', 'https://graph.facebook.com/v18.0')
        self.phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = current_app.config.get('WHATSAPP_TOKEN')
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
    def send_message(self, to: str, message: str, image_url: Optional[str] = None, 
                    buttons: Optional[List[Dict]] = None, list_items: Optional[List[Dict]] = None) -> bool:
        """Envia mensagem via WhatsApp"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Monta payload básico
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message}
            }
            
            # Se há imagem, muda o tipo da mensagem
            if image_url:
                payload["type"] = "image"
                payload["image"] = {
                    "link": image_url,
                    "caption": message
                }
                del payload["text"]
            
            # Se há botões, cria mensagem interativa
            elif buttons:
                payload = self._create_button_message(to, message, buttons)
            
            # Se há lista, cria mensagem de lista
            elif list_items:
                payload = self._create_list_message(to, message, list_items)
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                current_app.logger.info(f'Mensagem enviada com sucesso para {to}')
                return True
            else:
                current_app.logger.error(f'Erro ao enviar mensagem: {response.status_code} - {response.text}')
                return False
                
        except Exception as e:
            current_app.logger.error(f'Erro na integração WhatsApp: {str(e)}')
            return False
    
    def _create_button_message(self, to: str, message: str, buttons: List[Dict]) -> Dict:
        """Cria mensagem com botões interativos"""
        button_components = []
        
        for i, button in enumerate(buttons[:3]):  # WhatsApp permite máximo 3 botões
            button_components.append({
                "type": "reply",
                "reply": {
                    "id": button.get('id', f'btn_{i}'),
                    "title": button.get('title', f'Opção {i+1}')[:20]  # Máximo 20 caracteres
                }
            })
        
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message},
                "action": {
                    "buttons": button_components
                }
            }
        }
    
    def _create_list_message(self, to: str, message: str, list_items: List[Dict]) -> Dict:
        """Cria mensagem com lista interativa"""
        sections = [{
            "title": "Opções",
            "rows": []
        }]
        
        for i, item in enumerate(list_items[:10]):  # WhatsApp permite máximo 10 itens
            sections[0]["rows"].append({
                "id": item.get('id', f'item_{i}'),
                "title": item.get('title', f'Item {i+1}')[:24],  # Máximo 24 caracteres
                "description": item.get('description', '')[:72]  # Máximo 72 caracteres
            })
        
        return {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": message},
                "action": {
                    "button": "Ver opções",
                    "sections": sections
                }
            }
        }
    
    def send_template_message(self, to: str, template_name: str, language_code: str = "pt_BR", 
                            components: Optional[List[Dict]] = None) -> bool:
        """Envia mensagem usando template aprovado"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code}
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                current_app.logger.info(f'Template enviado com sucesso para {to}')
                return True
            else:
                current_app.logger.error(f'Erro ao enviar template: {response.status_code} - {response.text}')
                return False
                
        except Exception as e:
            current_app.logger.error(f'Erro ao enviar template: {str(e)}')
            return False
    
    def download_media(self, media_id: str) -> Optional[bytes]:
        """Baixa mídia do WhatsApp"""
        try:
            # Primeiro, obtém URL da mídia
            url = f"{self.base_url}/{media_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                current_app.logger.error(f'Erro ao obter URL da mídia: {response.status_code}')
                return None
            
            media_data = response.json()
            media_url = media_data.get('url')
            
            if not media_url:
                current_app.logger.error('URL da mídia não encontrada')
                return None
            
            # Baixa o arquivo
            media_response = requests.get(media_url, headers=self.headers)
            
            if media_response.status_code == 200:
                return media_response.content
            else:
                current_app.logger.error(f'Erro ao baixar mídia: {media_response.status_code}')
                return None
                
        except Exception as e:
            current_app.logger.error(f'Erro ao baixar mídia: {str(e)}')
            return None
    
    def mark_as_read(self, message_id: str) -> bool:
        """Marca mensagem como lida"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            return response.status_code == 200
            
        except Exception as e:
            current_app.logger.error(f'Erro ao marcar como lida: {str(e)}')
            return False
    
    def send_location(self, to: str, latitude: float, longitude: float, 
                     name: Optional[str] = None, address: Optional[str] = None) -> bool:
        """Envia localização"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            location_data = {
                "latitude": latitude,
                "longitude": longitude
            }
            
            if name:
                location_data["name"] = name
            if address:
                location_data["address"] = address
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "location",
                "location": location_data
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                current_app.logger.info(f'Localização enviada com sucesso para {to}')
                return True
            else:
                current_app.logger.error(f'Erro ao enviar localização: {response.status_code} - {response.text}')
                return False
                
        except Exception as e:
            current_app.logger.error(f'Erro ao enviar localização: {str(e)}')
            return False
    
    def send_contact(self, to: str, contact_data: Dict) -> bool:
        """Envia contato"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "contacts",
                "contacts": [contact_data]
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                current_app.logger.info(f'Contato enviado com sucesso para {to}')
                return True
            else:
                current_app.logger.error(f'Erro ao enviar contato: {response.status_code} - {response.text}')
                return False
                
        except Exception as e:
            current_app.logger.error(f'Erro ao enviar contato: {str(e)}')
            return False
    
    def get_business_profile(self) -> Optional[Dict]:
        """Obtém perfil do negócio"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/whatsapp_business_profile"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f'Erro ao obter perfil: {response.status_code}')
                return None
                
        except Exception as e:
            current_app.logger.error(f'Erro ao obter perfil: {str(e)}')
            return None
    
    def update_business_profile(self, profile_data: Dict) -> bool:
        """Atualiza perfil do negócio"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/whatsapp_business_profile"
            
            response = requests.post(url, headers=self.headers, json=profile_data)
            
            if response.status_code == 200:
                current_app.logger.info('Perfil atualizado com sucesso')
                return True
            else:
                current_app.logger.error(f'Erro ao atualizar perfil: {response.status_code} - {response.text}')
                return False
                
        except Exception as e:
            current_app.logger.error(f'Erro ao atualizar perfil: {str(e)}')
            return False

