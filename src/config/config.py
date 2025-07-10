import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configuração base da aplicação"""
    
    # Configurações básicas do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações do WhatsApp Business API
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN')
    WHATSAPP_WEBHOOK_URL = os.environ.get('WHATSAPP_WEBHOOK_URL')
    
    # Configurações do OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Configurações do Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Configurações de segurança
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # Configurações de APIs externas
    FINANCIAL_API_KEY = os.environ.get('FINANCIAL_API_KEY')
    SCHOLARSHIP_API_KEY = os.environ.get('SCHOLARSHIP_API_KEY')
    
    # Configurações de upload
    MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 10485760))  # 10MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/')
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,pdf,doc,docx').split(','))
    
    # Configurações de rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60))
    RATE_LIMIT_PER_HOUR = int(os.environ.get('RATE_LIMIT_PER_HOUR', 1000))
    
    # URLs da API do WhatsApp
    WHATSAPP_API_BASE_URL = "https://graph.facebook.com/v18.0"
    
    @staticmethod
    def init_app(app):
        """Inicialização adicional da aplicação"""
        pass

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///database/app_dev.db'

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database/app.db'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log para syslog em produção
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

