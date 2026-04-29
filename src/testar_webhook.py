#!/usr/bin/env python3
"""
Script para testar webhook do n8n
Envia dados fictícios em loop a cada 30 segundos
"""

import time
import json
import requests
from datetime import datetime


# URL do webhook
WEBHOOK_URL = "https://n8n.squaddev.bsb.br/webhook-test/c4affbf4-e187-4320-acc0-bd69476cd47b"

# Dados fictícios para teste
DADOS_TESTE = {
    "success": True,
    "cpf": "00012345678",
    "timestamp": None,  # Será atualizado a cada envio
    "data_processamento": None,  # Será atualizado a cada envio
    "hora_processamento": None,  # Será atualizado a cada envio
    "error": None,
    "data": {
        "cliente": {
            "nome": "JOAO DA SILVA TESTE",
            "tipo_proposta": "Recompra",
            "correntista_safra": "Não",
            "cpf": "000.123.456-78",
            "produto": "Financiamento de Veículos",
            "endereco": "RUA TESTE, 123",
            "cep": "70000-000",
            "cidade": "BRASILIA",
            "uf": "DF",
            "resultado": "SUCESSO"
        },
        "veiculo": {
            "marca": "VOLKSWAGEN",
            "modelo": "GOL 1.0",
            "modalidade": "Usado",
            "tipo": "Automóvel",
            "combustivel": "Flex",
            "placa": "ABC1234",
            "chassi": "9BWAA05U58P000001",
            "ano_fabricacao_modelo": "2020/2021",
            "renavam": "12345678901"
        },
        "operacao": {
            "contrato": "123456789",
            "data_contrato": "01/01/2020",
            "valor_compra": "R$ 50.000,00",
            "plano": "60 meses",
            "valor_parcelas_pagas": "R$ 30.000,00",
            "quantidade_parcelas_pagas": "36",
            "dias_atraso": "90",
            "data_parcela_vencida": "01/10/2024",
            "saldo_contabil": "R$ 20.000,00",
            "saldo_gerencial": "R$ 21.000,00",
            "saldo_principal": "R$ 19.000,00",
            "saldo_contabil_cdi": "R$ 20.500,00",
            "plano_balao": "Não"
        },
        "resumo_proposta": {
            "data_entrada": "14/11/2025",
            "validade": "30 dias",
            "primeiro_pagamento": "15/12/2025",
            "qtd_parcelas_acordo": "24",
            "repasse_banco": "R$ 18.000,00",
            "alvara": "R$ 500,00",
            "total_repasse_alvara": "R$ 18.500,00",
            "custas_banco": "R$ 300,00",
            "ho_escritorio": "R$ 1.000,00",
            "ho_politica": "R$ 800,00",
            "total_acordo": "R$ 20.600,00"
        },
        "estimativa_venda": {
            "cadin": "R$ 15.000,00",
            "valor_molicar": "R$ 25.000,00",
            "honorarios": "R$ 2.000,00"
        }
    }
}

# Dados para teste de contrato CANCELADO
DADOS_CANCELADO = {
    "success": True,
    "cpf": "11122233344",
    "timestamp": None,
    "data_processamento": None,
    "hora_processamento": None,
    "error": None,
    "data": {
        "cliente": {
            "nome": "",
            "tipo_proposta": "",
            "correntista_safra": "",
            "cpf": "111.222.333-44",
            "produto": "",
            "endereco": "",
            "cep": "",
            "cidade": "",
            "uf": "",
            "resultado": "CANCELADO"
        },
        "veiculo": {},
        "operacao": {},
        "resumo_proposta": {},
        "estimativa_venda": {}
    }
}

# Dados para teste de proposta NEGADA
DADOS_NEGADA = {
    "success": True,
    "cpf": "55566677788",
    "timestamp": None,
    "data_processamento": None,
    "hora_processamento": None,
    "error": None,
    "data": {
        "cliente": {
            "nome": "MARIA SANTOS NEGADA",
            "tipo_proposta": "Recompra",
            "correntista_safra": "Não",
            "cpf": "555.666.777-88",
            "produto": "Financiamento de Veículos",
            "endereco": "AV NEGADA, 456",
            "cep": "71000-000",
            "cidade": "BRASILIA",
            "uf": "DF",
            "resultado": "NEGADA"
        },
        "veiculo": {
            "marca": "FIAT",
            "modelo": "UNO 1.4",
            "modalidade": "Usado",
            "tipo": "Automóvel",
            "combustivel": "Flex",
            "placa": "DEF5678",
            "chassi": "9BWAA05U58P111111",
            "ano_fabricacao_modelo": "2018/2019",
            "renavam": "98765432101"
        },
        "operacao": {
            "contrato": "987654321",
            "data_contrato": "15/03/2019",
            "valor_compra": "R$ 35.000,00",
            "plano": "48 meses",
            "valor_parcelas_pagas": "R$ 20.000,00",
            "quantidade_parcelas_pagas": "28",
            "dias_atraso": "120",
            "data_parcela_vencida": "15/08/2024",
            "saldo_contabil": "R$ 15.000,00",
            "saldo_gerencial": "R$ 15.500,00",
            "saldo_principal": "R$ 14.500,00",
            "saldo_contabil_cdi": "R$ 15.300,00",
            "plano_balao": "Não"
        },
        "resumo_proposta": {
            "data_entrada": "25/11/2025",
            "validade": "30 dias",
            "primeiro_pagamento": "25/12/2025",
            "qtd_parcelas_acordo": "20",
            "repasse_banco": "R$ 13.000,00",
            "alvara": "R$ 400,00",
            "total_repasse_alvara": "R$ 13.400,00",
            "custas_banco": "R$ 250,00",
            "ho_escritorio": "R$ 800,00",
            "ho_politica": "R$ 600,00",
            "total_acordo": "R$ 15.050,00"
        },
        "estimativa_venda": {
            "cadin": "R$ 12.000,00",
            "valor_molicar": "R$ 20.000,00",
            "honorarios": "R$ 1.500,00"
        }
    }
}

# Dados para teste de CPF NÃO ENCONTRADO
DADOS_NAO_ENCONTRADO = {
    "success": False,
    "cpf": "99999999999",
    "timestamp": None,
    "data_processamento": None,
    "hora_processamento": None,
    "error": "CPF não encontrado - Nenhum contrato localizado",
    "data": {
        "cliente": {
            "nome": "",
            "tipo_proposta": "",
            "correntista_safra": "",
            "cpf": "999.999.999-99",
            "produto": "",
            "endereco": "",
            "cep": "",
            "cidade": "",
            "uf": "",
            "resultado": "CPF/CNPJ Não encontrado"
        },
        "veiculo": {},
        "operacao": {},
        "resumo_proposta": {},
        "estimativa_venda": {}
    }
}

# Dados para teste de ACORDO FORMALIZADO
DADOS_ACORDO_FORMALIZADO = {
    "success": True,
    "cpf": "33344455566",
    "timestamp": None,
    "data_processamento": None,
    "hora_processamento": None,
    "error": None,
    "data": {
        "cliente": {
            "nome": "",
            "tipo_proposta": "",
            "correntista_safra": "",
            "cpf": "333.444.555-66",
            "produto": "",
            "endereco": "",
            "cep": "",
            "cidade": "",
            "uf": "",
            "resultado": "ACORDO FORMALIZADO (EM CUMPRIMENTO)"
        },
        "veiculo": {},
        "operacao": {},
        "resumo_proposta": {},
        "estimativa_venda": {}
    }
}


def enviar_webhook(dados):
    """Envia dados para o webhook via POST."""
    # Atualizar timestamp no formato americano
    agora = datetime.now()
    dados["timestamp"] = agora.strftime("%Y-%m-%d %H:%M:%S")
    dados["data_processamento"] = agora.strftime("%Y-%m-%d")
    dados["hora_processamento"] = agora.strftime("%H:%M:%S")
    
    try:
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando dados para webhook via POST...")
        print(f"{'='*60}")
        
        response = requests.post(WEBHOOK_URL, json=dados, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Sucesso! Status: {response.status_code}")
        print(f"📊 Dados enviados:")
        print(json.dumps(dados, ensure_ascii=False, indent=2))
        
        if response.text:
            print(f"\n📥 Resposta do webhook:")
            try:
                resposta_json = response.json()
                print(json.dumps(resposta_json, ensure_ascii=False, indent=2))
            except:
                print(response.text)
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar webhook: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Resposta: {e.response.text}")
        return False


def main():
    """Função principal - loop de teste."""
    print("="*60)
    print("TESTE DE WEBHOOK - ENVIO EM LOOP")
    print("="*60)
    print(f"\n🎯 Webhook URL: {WEBHOOK_URL}")
    print(f"⏱️  Intervalo: 30 segundos")
    print(f"\n💡 Pressione Ctrl+C para parar\n")
    
    contador = 1
    
    try:
        while True:
            print(f"\n🔄 Tentativa #{contador}")
            
            # Alternar entre os 5 cenários para testar todos os casos
            tipo_envio = contador % 5
            
            if tipo_envio == 0:
                # Envio com erro (CPF não encontrado)
                print("📝 Tipo: CPF NÃO ENCONTRADO")
                enviar_webhook(DADOS_NAO_ENCONTRADO)
            elif tipo_envio == 1:
                # Envio com dados completos (sucesso)
                print("📝 Tipo: SUCESSO - Dados Completos")
                enviar_webhook(DADOS_TESTE)
            elif tipo_envio == 2:
                # Envio de contrato CANCELADO
                print("📝 Tipo: CONTRATO CANCELADO")
                enviar_webhook(DADOS_CANCELADO)
            elif tipo_envio == 3:
                # Envio de proposta NEGADA
                print("📝 Tipo: PROPOSTA NEGADA")
                enviar_webhook(DADOS_NEGADA)
            else:
                # Envio de acordo formalizado
                print("📝 Tipo: ACORDO FORMALIZADO")
                enviar_webhook(DADOS_ACORDO_FORMALIZADO)
            
            contador += 1
            
            # Aguardar 30 segundos
            print(f"\n⏳ Aguardando 30 segundos para próximo envio...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print(f"⚠️  Teste interrompido pelo usuário")
        print(f"📊 Total de envios: {contador - 1}")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
