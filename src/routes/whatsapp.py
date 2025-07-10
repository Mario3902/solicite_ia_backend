from flask import Blueprint, request, jsonify, current_app
import json
import time
from datetime import datetime
from src.models import db, User, Conversa
from src.modules.whatsapp_integration import WhatsAppIntegration
from src.modules.nlp_processor import NLPProcessor
from src.modules.message_router import MessageRouter

whatsapp_bp = Blueprint('whatsapp', __name__)

@whatsapp_bp.route('/whatsapp', methods=['GET'])
def verify_webhook():
    """Verificação do webhook do WhatsApp"""
    try:
        # Parâmetros de verificação do WhatsApp
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        # Verifica se é uma requisição de verificação válida
        if mode == 'subscribe' and token == current_app.config.get('WHATSAPP_VERIFY_TOKEN'):
            current_app.logger.info('Webhook verificado com sucesso')
            return challenge, 200
        else:
            current_app.logger.warning('Falha na verificação do webhook')
            return 'Forbidden', 403
            
    except Exception as e:
        current_app.logger.error(f'Erro na verificação do webhook: {str(e)}')
        return 'Internal Server Error', 500

@whatsapp_bp.route('/whatsapp', methods=['POST'])
def receive_message():
    """Recebe mensagens do WhatsApp"""
    start_time = time.time()
    
    try:
        # Obtém dados da requisição
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        # Log da mensagem recebida (sem dados sensíveis)
        current_app.logger.info(f'Mensagem recebida: {json.dumps(data, indent=2)}')
        
        # Verifica se há mudanças de mensagem
        if 'entry' not in data:
            return jsonify({'status': 'ok'}), 200
        
        for entry in data['entry']:
            if 'changes' not in entry:
                continue
                
            for change in entry['changes']:
                if change.get('field') != 'messages':
                    continue
                
                value = change.get('value', {})
                messages = value.get('messages', [])
                
                for message in messages:
                    # Processa cada mensagem
                    process_single_message(message, value, start_time)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        current_app.logger.error(f'Erro ao processar mensagem: {str(e)}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_single_message(message, value, start_time):
    """Processa uma única mensagem"""
    try:
        # Extrai informações da mensagem
        from_number = message.get('from')
        message_id = message.get('id')
        timestamp = message.get('timestamp')
        message_type = message.get('type')
        
        if not from_number:
            current_app.logger.warning('Mensagem sem número de origem')
            return
        
        # Busca ou cria usuário
        user = User.buscar_ou_criar(whatsapp_id=from_number)
        
        # Extrai conteúdo da mensagem baseado no tipo
        message_content = extract_message_content(message, message_type)
        
        if not message_content:
            current_app.logger.warning(f'Não foi possível extrair conteúdo da mensagem tipo: {message_type}')
            return
        
        # Cria registro da conversa
        conversa = Conversa(
            usuario_id=user.id,
            mensagem_usuario=message_content.get('text', ''),
            tipo_comando='processando',
            imagem_recebida=message_content.get('image_url'),
            timestamp=datetime.fromtimestamp(int(timestamp)) if timestamp else datetime.utcnow(),
            sessao_id=f"{from_number}_{int(time.time())}"
        )
        
        db.session.add(conversa)
        db.session.commit()
        
        # Processa a mensagem com NLP
        nlp_processor = NLPProcessor()
        nlp_result = nlp_processor.process_message(
            text=message_content.get('text', ''),
            image_url=message_content.get('image_url'),
            user_id=user.id
        )
        
        # Atualiza conversa com resultado do NLP
        conversa.intencao_detectada = nlp_result.get('intent')
        conversa.tipo_comando = nlp_result.get('command_type')
        conversa.categoria = nlp_result.get('category')
        conversa.entidades_extraidas = json.dumps(nlp_result.get('entities', {}))
        
        # Roteia mensagem para o módulo apropriado
        message_router = MessageRouter()
        response = message_router.route_message(nlp_result, user, conversa)
        
        # Atualiza conversa com resposta
        conversa.resposta_ia = response.get('text', '')
        conversa.sucesso_comando = response.get('success', True)
        
        if not response.get('success'):
            conversa.erro_detalhes = response.get('error', '')
        
        # Calcula tempo de resposta
        end_time = time.time()
        conversa.tempo_resposta_ms = int((end_time - start_time) * 1000)
        
        db.session.commit()
        
        # Envia resposta via WhatsApp
        whatsapp = WhatsAppIntegration()
        whatsapp.send_message(
            to=from_number,
            message=response.get('text', ''),
            image_url=response.get('image_url'),
            buttons=response.get('buttons')
        )
        
        # Atualiza último acesso do usuário
        user.atualizar_ultimo_acesso()
        
        current_app.logger.info(f'Mensagem processada com sucesso para {from_number}')
        
    except Exception as e:
        current_app.logger.error(f'Erro ao processar mensagem individual: {str(e)}')
        
        # Tenta enviar mensagem de erro para o usuário
        try:
            whatsapp = WhatsAppIntegration()
            whatsapp.send_message(
                to=from_number,
                message="Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente em alguns instantes."
            )
        except:
            pass

def extract_message_content(message, message_type):
    """Extrai conteúdo da mensagem baseado no tipo"""
    content = {}
    
    try:
        if message_type == 'text':
            content['text'] = message.get('text', {}).get('body', '')
            
        elif message_type == 'image':
            image_data = message.get('image', {})
            content['text'] = image_data.get('caption', '')
            content['image_url'] = image_data.get('id')  # ID da imagem no WhatsApp
            content['mime_type'] = image_data.get('mime_type')
            
        elif message_type == 'document':
            doc_data = message.get('document', {})
            content['text'] = doc_data.get('caption', '')
            content['document_url'] = doc_data.get('id')
            content['filename'] = doc_data.get('filename')
            content['mime_type'] = doc_data.get('mime_type')
            
        elif message_type == 'audio':
            audio_data = message.get('audio', {})
            content['audio_url'] = audio_data.get('id')
            content['mime_type'] = audio_data.get('mime_type')
            
        elif message_type == 'video':
            video_data = message.get('video', {})
            content['text'] = video_data.get('caption', '')
            content['video_url'] = video_data.get('id')
            content['mime_type'] = video_data.get('mime_type')
            
        elif message_type == 'location':
            location_data = message.get('location', {})
            content['text'] = f"Localização: {location_data.get('latitude')}, {location_data.get('longitude')}"
            content['latitude'] = location_data.get('latitude')
            content['longitude'] = location_data.get('longitude')
            content['address'] = location_data.get('address')
            
        elif message_type == 'contacts':
            contacts_data = message.get('contacts', [])
            if contacts_data:
                contact = contacts_data[0]
                content['text'] = f"Contato: {contact.get('name', {}).get('formatted_name', '')}"
                content['contact_data'] = contact
                
        elif message_type == 'button':
            button_data = message.get('button', {})
            content['text'] = button_data.get('text', '')
            content['button_payload'] = button_data.get('payload')
            
        elif message_type == 'interactive':
            interactive_data = message.get('interactive', {})
            if interactive_data.get('type') == 'button_reply':
                button_reply = interactive_data.get('button_reply', {})
                content['text'] = button_reply.get('title', '')
                content['button_id'] = button_reply.get('id')
            elif interactive_data.get('type') == 'list_reply':
                list_reply = interactive_data.get('list_reply', {})
                content['text'] = list_reply.get('title', '')
                content['list_id'] = list_reply.get('id')
        
        return content
        
    except Exception as e:
        current_app.logger.error(f'Erro ao extrair conteúdo da mensagem: {str(e)}')
        return {'text': ''}

@whatsapp_bp.route('/status', methods=['GET'])
def webhook_status():
    """Endpoint para verificar status do webhook"""
    return jsonify({
        'status': 'active',
        'service': 'Solicite IA WhatsApp Webhook',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

