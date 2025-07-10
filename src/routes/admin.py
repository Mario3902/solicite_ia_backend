from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from src.models import db, User, PrestadorServico, Produto, ConexaoPessoal, AchadoPerdido, Reclamacao, Conversa
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@cross_origin()
def get_dashboard_stats():
    """Retorna estatísticas do dashboard"""
    try:
        # Estatísticas gerais
        total_users = User.query.count()
        total_providers = PrestadorServico.query.filter_by(ativo=True).count()
        total_products = Produto.query.filter_by(ativo=True, vendido=False).count()
        total_connections = ConexaoPessoal.query.filter_by(ativo=True).count()
        total_lost_found = AchadoPerdido.query.filter_by(ativo=True, resolvido=False).count()
        total_complaints = Reclamacao.query.filter_by(ativa=True).count()
        
        # Estatísticas dos últimos 30 dias
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        new_users_30d = User.query.filter(User.data_cadastro >= thirty_days_ago).count()
        new_providers_30d = PrestadorServico.query.filter(PrestadorServico.data_cadastro >= thirty_days_ago).count()
        new_products_30d = Produto.query.filter(Produto.data_publicacao >= thirty_days_ago).count()
        new_complaints_30d = Reclamacao.query.filter(Reclamacao.data_reclamacao >= thirty_days_ago).count()
        
        # Conversas por dia (últimos 7 dias)
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_conversations = db.session.query(
            func.date(Conversa.data_inicio).label('date'),
            func.count(Conversa.id).label('count')
        ).filter(
            Conversa.data_inicio >= seven_days_ago
        ).group_by(
            func.date(Conversa.data_inicio)
        ).order_by('date').all()
        
        # Top categorias de produtos
        top_product_categories = db.session.query(
            Produto.categoria,
            func.count(Produto.id).label('count')
        ).filter(
            Produto.ativo == True
        ).group_by(
            Produto.categoria
        ).order_by(desc('count')).limit(5).all()
        
        # Top especialidades de prestadores
        top_provider_specialties = db.session.query(
            PrestadorServico.especialidade,
            func.count(PrestadorServico.id).label('count')
        ).filter(
            PrestadorServico.ativo == True
        ).group_by(
            PrestadorServico.especialidade
        ).order_by(desc('count')).limit(5).all()
        
        # Status das reclamações
        complaint_status = db.session.query(
            Reclamacao.status,
            func.count(Reclamacao.id).label('count')
        ).filter(
            Reclamacao.ativa == True
        ).group_by(
            Reclamacao.status
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_users': total_users,
                    'total_providers': total_providers,
                    'total_products': total_products,
                    'total_connections': total_connections,
                    'total_lost_found': total_lost_found,
                    'total_complaints': total_complaints
                },
                'growth': {
                    'new_users_30d': new_users_30d,
                    'new_providers_30d': new_providers_30d,
                    'new_products_30d': new_products_30d,
                    'new_complaints_30d': new_complaints_30d
                },
                'charts': {
                    'daily_conversations': [
                        {'date': str(item.date), 'count': item.count}
                        for item in daily_conversations
                    ],
                    'top_product_categories': [
                        {'category': item.categoria, 'count': item.count}
                        for item in top_product_categories
                    ],
                    'top_provider_specialties': [
                        {'specialty': item.especialidade, 'count': item.count}
                        for item in top_provider_specialties
                    ],
                    'complaint_status': [
                        {'status': item.status, 'count': item.count}
                        for item in complaint_status
                    ]
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar estatísticas: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@cross_origin()
def get_users():
    """Lista usuários com paginação"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.nome.ilike(f'%{search}%'),
                    User.whatsapp_id.ilike(f'%{search}%'),
                    User.telefone.ilike(f'%{search}%')
                )
            )
        
        users = query.order_by(desc(User.data_cadastro)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users.items],
                'pagination': {
                    'page': page,
                    'pages': users.pages,
                    'per_page': per_page,
                    'total': users.total,
                    'has_next': users.has_next,
                    'has_prev': users.has_prev
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar usuários: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/providers', methods=['GET'])
@cross_origin()
def get_providers():
    """Lista prestadores de serviços"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        specialty = request.args.get('specialty', '')
        
        query = PrestadorServico.query.filter_by(ativo=True)
        
        if specialty:
            query = query.filter(PrestadorServico.especialidade.ilike(f'%{specialty}%'))
        
        providers = query.order_by(desc(PrestadorServico.data_cadastro)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'providers': [provider.to_dict() for provider in providers.items],
                'pagination': {
                    'page': page,
                    'pages': providers.pages,
                    'per_page': per_page,
                    'total': providers.total
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar prestadores: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/products', methods=['GET'])
@cross_origin()
def get_products():
    """Lista produtos do marketplace"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category', '')
        
        query = Produto.query.filter_by(ativo=True)
        
        if category:
            query = query.filter_by(categoria=category)
        
        products = query.order_by(desc(Produto.data_publicacao)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'products': [product.to_dict() for product in products.items],
                'pagination': {
                    'page': page,
                    'pages': products.pages,
                    'per_page': per_page,
                    'total': products.total
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar produtos: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/complaints', methods=['GET'])
@cross_origin()
def get_complaints():
    """Lista reclamações"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        
        query = Reclamacao.query.filter_by(ativa=True)
        
        if status:
            query = query.filter_by(status=status)
        
        complaints = query.order_by(
            Reclamacao.urgente.desc(),
            desc(Reclamacao.data_reclamacao)
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'complaints': [complaint.to_dict() for complaint in complaints.items],
                'pagination': {
                    'page': page,
                    'pages': complaints.pages,
                    'per_page': per_page,
                    'total': complaints.total
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar reclamações: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/complaints/<int:complaint_id>/status', methods=['PUT'])
@cross_origin()
def update_complaint_status(complaint_id):
    """Atualiza status de uma reclamação"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pendente', 'em_andamento', 'resolvida', 'rejeitada']:
            return jsonify({'success': False, 'error': 'Status inválido'}), 400
        
        complaint = Reclamacao.query.get_or_404(complaint_id)
        complaint.status = new_status
        complaint.data_atualizacao = datetime.now()
        
        if new_status == 'resolvida':
            complaint.data_resolucao = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status atualizado com sucesso',
            'data': complaint.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao atualizar status: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/block', methods=['PUT'])
@cross_origin()
def toggle_user_block(user_id):
    """Bloqueia/desbloqueia usuário"""
    try:
        user = User.query.get_or_404(user_id)
        user.bloqueado = not user.bloqueado
        db.session.commit()
        
        action = 'bloqueado' if user.bloqueado else 'desbloqueado'
        
        return jsonify({
            'success': True,
            'message': f'Usuário {action} com sucesso',
            'data': user.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao bloquear/desbloquear usuário: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/system/status', methods=['GET'])
@cross_origin()
def get_system_status():
    """Retorna status do sistema"""
    try:
        # Verifica conexão com banco
        db_status = True
        try:
            db.session.execute('SELECT 1')
        except:
            db_status = False
        
        # Estatísticas de performance
        active_conversations = Conversa.query.filter(
            Conversa.ativa == True
        ).count()
        
        # Últimas atividades
        recent_activities = []
        
        # Usuários recentes
        recent_users = User.query.order_by(desc(User.data_cadastro)).limit(5).all()
        for user in recent_users:
            recent_activities.append({
                'type': 'user_registration',
                'description': f'Novo usuário: {user.nome or user.whatsapp_id}',
                'timestamp': user.data_cadastro.isoformat()
            })
        
        # Reclamações recentes
        recent_complaints = Reclamacao.query.order_by(desc(Reclamacao.data_reclamacao)).limit(3).all()
        for complaint in recent_complaints:
            recent_activities.append({
                'type': 'complaint',
                'description': f'Nova reclamação: {complaint.empresa}',
                'timestamp': complaint.data_reclamacao.isoformat()
            })
        
        # Ordena por timestamp
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'database': db_status,
                'active_conversations': active_conversations,
                'recent_activities': recent_activities[:10],
                'uptime': '99.9%',  # Simulado
                'version': '1.0.0'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao buscar status: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/export/users', methods=['GET'])
@cross_origin()
def export_users():
    """Exporta dados de usuários"""
    try:
        users = User.query.all()
        
        export_data = []
        for user in users:
            export_data.append({
                'id': user.id,
                'nome': user.nome,
                'whatsapp_id': user.whatsapp_id,
                'telefone': user.telefone,
                'data_cadastro': user.data_cadastro.isoformat() if user.data_cadastro else None,
                'ultimo_acesso': user.ultimo_acesso.isoformat() if user.ultimo_acesso else None,
                'bloqueado': user.bloqueado,
                'verificado': user.verificado
            })
        
        return jsonify({
            'success': True,
            'data': export_data,
            'total': len(export_data)
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao exportar usuários: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

