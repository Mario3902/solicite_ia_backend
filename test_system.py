#!/usr/bin/env python3
"""
Script de teste para validar o sistema Solicite IA
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("🔍 Testando imports dos módulos...")
    
    try:
        from src.config import config
        print("✅ Config importado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar config: {e}")
        return False
    
    try:
        from src.models import db, User, PrestadorServico, Produto
        print("✅ Modelos importados com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar modelos: {e}")
        return False
    
    try:
        from src.modules.whatsapp_integration import WhatsAppIntegration
        print("✅ Integração WhatsApp importada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar WhatsApp integration: {e}")
        return False
    
    try:
        from src.modules.nlp_processor import NLPProcessor
        print("✅ Processador NLP importado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar NLP processor: {e}")
        return False
    
    try:
        from src.modules.message_router import MessageRouter
        print("✅ Roteador de mensagens importado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar message router: {e}")
        return False
    
    return True

def test_nlp_processor():
    """Testa o processador de linguagem natural"""
    print("\n🧠 Testando processador NLP...")
    
    try:
        from src.modules.nlp_processor import NLPProcessor
        
        nlp = NLPProcessor()
        
        # Teste 1: Detecção de intenção de prestador de serviços
        result1 = nlp.process_message("Sou eletricista em Luanda, faço instalações elétricas")
        print(f"✅ Teste 1 - Prestador: {result1['intent']}")
        
        # Teste 2: Detecção de intenção de venda
        result2 = nlp.process_message("Vendo iPhone 12, 150.000 kz, estado novo")
        print(f"✅ Teste 2 - Venda: {result2['intent']}")
        
        # Teste 3: Detecção de busca
        result3 = nlp.process_message("Procuro mecânico em Benguela")
        print(f"✅ Teste 3 - Busca: {result3['intent']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste NLP: {e}")
        return False

def test_modules():
    """Testa os módulos funcionais"""
    print("\n⚙️ Testando módulos funcionais...")
    
    try:
        from src.modules.service_providers import ServiceProvidersModule
        from src.modules.marketplace import MarketplaceModule
        from src.modules.personal_connections import PersonalConnectionsModule
        
        # Testa instanciação dos módulos
        sp_module = ServiceProvidersModule()
        mp_module = MarketplaceModule()
        pc_module = PersonalConnectionsModule()
        
        print("✅ Todos os módulos funcionais instanciados com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar módulos: {e}")
        return False

def test_whatsapp_integration():
    """Testa a integração com WhatsApp"""
    print("\n📱 Testando integração WhatsApp...")
    
    try:
        from src.modules.whatsapp_integration import WhatsAppIntegration
        
        # Testa instanciação (sem fazer chamadas reais)
        wa = WhatsAppIntegration()
        
        # Testa formatação de mensagem
        message = wa.format_text_message("Olá! Como posso ajudar?")
        assert 'text' in message
        print("✅ Formatação de mensagem de texto OK")
        
        # Testa formatação de botões
        buttons = wa.format_button_message(
            "Escolha uma opção:",
            [{"id": "1", "title": "Opção 1"}]
        )
        assert 'interactive' in buttons
        print("✅ Formatação de mensagem com botões OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste WhatsApp: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do sistema Solicite IA\n")
    
    tests = [
        ("Imports", test_imports),
        ("NLP Processor", test_nlp_processor),
        ("Módulos Funcionais", test_modules),
        ("Integração WhatsApp", test_whatsapp_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Executando: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} - PASSOU")
        else:
            print(f"❌ {test_name} - FALHOU")
    
    print(f"\n{'='*50}")
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    print('='*50)
    
    if passed == total:
        print("🎉 Todos os testes passaram! Sistema validado com sucesso!")
        return True
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

