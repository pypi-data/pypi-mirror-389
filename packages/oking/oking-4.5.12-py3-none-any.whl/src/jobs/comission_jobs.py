"""
Job de Sincronização de Comissões com OKING Hub
==================================================

Autor: Sistema OKING Hub
Data: 2025
Versão: 1.0.0

Descrição:
    Sincroniza comissões do ERP com o OKING Hub, processando em lotes
    de 1000 registros para otimizar performance e garantir estabilidade.

Features:
    - Processamento em lotes (batch size: 1000)
    - Rastreamento de protocolo por lote
    - Suporte a Oracle, Firebird, SQL Server
    - Validação de semáforo para evitar duplicados
    - Logging completo de progresso
    - Tratamento robusto de erros

Dependências:
    - src.api.entities.comissao (Comissao)
    - src.api.okinghub (post_comissoes)
    - src.database.queries (get_comissao_query, IntegrationType)
    - src.database.connection (get_database_connection)

Exemplo de Uso:
    config = {
        'send_logs': True,
        'sql': None  # Usa query padrão
    }
    job_sincroniza_comissao(config)
"""

import logging
from typing import List, Optional
from datetime import datetime

# Importações internas
from src.api.entities.comissao import Comissao
from src.api import okinghub
from src.database import queries
import src.database.connection as database
import src.database.utils as utils
from src.log_types import LogType
from src.jobs.system_jobs import OnlineLogger
import src

# Logger
logger = logging.getLogger(__name__)

# Constantes
BATCH_SIZE = 1000  # Tamanho do lote (configurável)
JOB_NAME = 'SINCRONIZA_COMISSAO'


def job_sincroniza_comissao(config: dict) -> None:
    """
    Job principal de sincronização de comissões
    
    Fluxo de Execução:
        1. Conecta ao banco de dados
        2. Executa query de comissões (últimos 30 dias, enviado='N')
        3. Divide registros em lotes de 1000
        4. Para cada lote:
           a. Converte para objetos Comissao
           b. Envia via post_comissoes()
           c. Registra protocolo no semáforo
           d. Atualiza flag enviado='S'
        5. Loga estatísticas finais
    
    Args:
        config (dict): Configuração do job
            - send_logs (bool): Enviar logs online
            - sql (str, optional): SQL customizada (None = usa padrão)
    
    Returns:
        None
    
    Raises:
        Exception: Erros críticos são logados mas não interrompem processamento
    
    Example:
        config = {'send_logs': True, 'sql': None}
        job_sincroniza_comissao(config)
    """
    send_logs = config.get('send_logs', True)
    sql_customizado = config.get('sql')
    
    logger.info(f'[{JOB_NAME}] Iniciando sincronização de comissões')
    
    # Obter configuração do banco
    db_config = utils.get_database_config(config)
    
    # Estatísticas
    stats = {
        'total_registros': 0,
        'total_lotes': 0,
        'total_sucesso': 0,
        'total_erro': 0,
        'inicio': datetime.now()
    }
    
    conexao = None
    conn = None
    cursor = None
    
    try:
        # 1. Conectar ao banco
        if src.print_payloads:
            print('Passo 1 - Iniciando conexão com banco de dados')
        logger.info(f'[{JOB_NAME}] Conectando ao banco de dados')
        conexao = database.Connection(db_config)
        conn = conexao.get_conect()
        cursor = conn.cursor()
        if src.print_payloads:
            print('Passo 2 - Conexão estabelecida com sucesso')
        
        # 2. Executar query de comissões
        if src.print_payloads:
            print(f'Passo 3 - Executando query de comissões (Tipo DB: {db_config.db_type})')
        logger.info(f'[{JOB_NAME}] Executando query de comissões')
        
        # Obter query
        sql = queries.get_comissao_query(db_config.db_type, sql_customizado)
        
        if sql is None:
            logger.error(f'[{JOB_NAME}] Tipo de banco não suportado: {db_config.db_type}')
            OnlineLogger.send_log(
                JOB_NAME,
                send_logs,
                True,
                f'Tipo de banco não suportado: {db_config.db_type}',
                LogType.ERROR,
                'COMISSAO')
            return
        
        if src.print_payloads:
            print('Passo 4 - SQL Query:')
            print(sql)
            print('Passo 5 - Executando query...')
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # Mapear colunas por nome (padrão OKING Hub)
        columns = [col[0].lower() for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        
        stats['total_registros'] = len(results)
        if src.print_payloads:
            print(f'Passo 6 - Query executada: {stats["total_registros"]} registros encontrados')
        logger.info(f'[{JOB_NAME}] {stats["total_registros"]} comissões encontradas')
        
        if stats['total_registros'] == 0:
            if src.print_payloads:
                print('Passo 7 - Nenhuma comissão pendente, finalizando job')
            logger.info(f'[{JOB_NAME}] Nenhuma comissão para processar')
            OnlineLogger.send_log(
                JOB_NAME,
                send_logs,
                False,
                'Nenhuma comissão pendente encontrada',
                LogType.INFO,
                'COMISSAO')
            return
        
        # 3. Processar em lotes
        if src.print_payloads:
            print(f'Passo 7 - Iniciando processamento em lotes de {BATCH_SIZE}')
        logger.info(f'[{JOB_NAME}] Processando em lotes de {BATCH_SIZE}')
        
        for i in range(0, len(results), BATCH_SIZE):
            batch_number = (i // BATCH_SIZE) + 1
            batch_rows = results[i:i + BATCH_SIZE]
            
            if src.print_payloads:
                print(f'\nPasso 8.{batch_number} - Processando lote {batch_number}/{(len(results) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch_rows)} registros)')
            logger.info(f'[{JOB_NAME}] Processando lote {batch_number}/{(len(results) + BATCH_SIZE - 1) // BATCH_SIZE}')
            
            try:
                # Processar lote
                if src.print_payloads:
                    print(f'Passo 9.{batch_number} - Convertendo registros do lote {batch_number}')
                result = process_batch(batch_rows, batch_number, send_logs, db_config)
                
                stats['total_lotes'] += 1
                stats['total_sucesso'] += result.get('total_sucesso', 0)
                stats['total_erro'] += result.get('total_erro', 0)
                
                # Log do resultado do lote
                if result['sucesso']:
                    if src.print_payloads:
                        print(f'Passo 10.{batch_number} - Lote {batch_number} enviado com SUCESSO')
                        print(f'  └─ Protocolo: {result.get("protocolo", "N/A")}')
                        print(f'  └─ Sucesso: {result.get("total_sucesso", 0)} | Erro: {result.get("total_erro", 0)}')
                    logger.info(f'[{JOB_NAME}] Lote {batch_number} enviado com sucesso')
                else:
                    if src.print_payloads:
                        print(f'Passo 10.{batch_number} - Lote {batch_number} FALHOU')
                        print(f'  └─ Mensagem: {result.get("mensagem")}')
                    logger.error(f'[{JOB_NAME}] Lote {batch_number} falhou: {result.get("mensagem")}')
                
            except Exception as e:
                if src.print_payloads:
                    print(f'Passo 10.{batch_number} - ERRO ao processar lote {batch_number}: {str(e)}')
                logger.error(f'[{JOB_NAME}] Erro ao processar lote {batch_number}: {str(e)}')
                stats['total_erro'] += len(batch_rows)
                OnlineLogger.send_log(
                    JOB_NAME,
                    send_logs,
                    True,
                    f'Erro no lote {batch_number}: {str(e)}',
                    LogType.ERROR,
                    'COMISSAO')
        
        # 4. Estatísticas finais
        stats['fim'] = datetime.now()
        stats['duracao'] = (stats['fim'] - stats['inicio']).total_seconds()
        
        if src.print_payloads:
            print('\n' + '='*60)
            print('Passo 11 - ESTATÍSTICAS FINAIS')
            print('='*60)
        
        log_final_statistics(stats, send_logs)
        
    except Exception as e:
        logger.error(f'[{JOB_NAME}] Erro crítico: {str(e)}')
        OnlineLogger.send_log(
            JOB_NAME,
            send_logs,
            True,
            f'Erro crítico na sincronização: {str(e)}',
            LogType.ERROR,
            'COMISSAO')
    
    finally:
        # Fechar conexões
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        
        logger.info(f'[{JOB_NAME}] Sincronização finalizada')


def process_batch(rows: List[dict], batch_number: int, send_logs: bool, db_config) -> dict:
    """
    Processa um lote de comissões
    
    Args:
        rows: Lista de dicionários (row mapped by column names)
        batch_number: Número do lote (para logging)
        send_logs: Flag de envio de logs
        db_config: Configuração do banco de dados
    
    Returns:
        dict: Resultado do processamento
    
    Example:
        result = process_batch(rows[0:1000], 1, True, db_config)
    """
    try:
        # Converter rows para objetos Comissao
        comissoes = []
        
        if src.print_payloads:
            print(f'  └─ Convertendo {len(rows)} registros para objetos Comissao...')
        
        for idx, row in enumerate(rows):
            try:
                # Mapeamento por nome de coluna (padrão OKING Hub - tipado e seguro)
                comissao = Comissao(
                    numero_nota_fiscal=row.get('numero_nota_fiscal'),
                    codigo_vendedor=row.get('codigo_vendedor'),
                    data_emissao=row.get('data_emissao'),
                    codigo_da_filial=row.get('codigo_da_filial'),
                    nome_da_filial=row.get('nome_da_filial'),
                    codordtrans=row.get('codordtrans'),
                    codtransacao=row.get('codtransacao'),
                    cfop_nota_fiscal=row.get('cfop_nota_fiscal'),
                    preco_unitario=row.get('preco_unitario'),
                    data_vencimento=row.get('data_vencimento'),
                    quantidade=row.get('quantidade'),
                    serie=row.get('serie'),
                    referencia=row.get('referencia'),
                    numero_cupom=row.get('numero_cupom'),
                    total_nota_fiscal=row.get('total_nota_fiscal'),
                    codigo_produto=row.get('codigo_produto'),
                    codigo_fornecedor=row.get('codigo_fornecedor'),
                    codigo_cliente=row.get('codigo_cliente'),
                    cgccpf=row.get('cgccpf'),
                    codunidclifor=row.get('codunidclifor'),
                    quantidade_pontos=row.get('quantidade_pontos'),
                    preco_manual=row.get('preco_manual'),
                    quantidade_original=row.get('quantidade_original'),
                    codigo_multiplicador=row.get('codigo_multiplicador'),
                    descricao_multiplicador=row.get('descricao_multiplicador'),
                    pureza=row.get('pureza'),
                    total_convertido=row.get('total_convertido')
                )
                comissoes.append(comissao)
                
                if src.print_payloads and idx < 2:  # Mostrar apenas os 2 primeiros
                    print(f'  └─ Registro {idx+1}: NF={row.get("numero_nota_fiscal")}, Vendedor={row.get("codigo_vendedor")}, Valor={row.get("total_nota_fiscal")}')
            except Exception as e:
                if src.print_payloads:
                    print(f'  └─ ERRO ao converter registro {idx+1}: {str(e)}')
                logger.error(f'[{JOB_NAME}] Erro ao converter row: {str(e)}')
                continue
        
        if not comissoes:
            if src.print_payloads:
                print(f'  └─ AVISO: Lote {batch_number} sem comissões válidas')
            logger.warning(f'[{JOB_NAME}] Lote {batch_number} sem comissões válidas')
            return {
                'sucesso': False,
                'mensagem': 'Nenhuma comissão válida no lote',
                'total_sucesso': 0,
                'total_erro': len(rows)
            }
        
        if src.print_payloads:
            print(f'  └─ Conversão completa: {len(comissoes)}/{len(rows)} registros válidos')
            print(f'  └─ Enviando para API OKING Hub...')
        
        # Enviar via API
        logger.info(f'[{JOB_NAME}] Enviando {len(comissoes)} comissões (lote {batch_number})')
        result = okinghub.post_comissoes(send_logs, comissoes)
        
        if src.print_payloads:
            print(f'  └─ Resposta da API recebida:')
            print(f'     • Sucesso: {result.get("sucesso")}')
            print(f'     • Mensagem: {result.get("mensagem", "N/A")}')
            if result.get('protocolo'):
                print(f'     • Protocolo: {result.get("protocolo")}')
        
        # Atualizar semáforo individual para cada comissão
        if result.get('response'):
            validate_response_comissao(result.get('response'), rows, db_config, send_logs)
        
        # Registrar protocolo (se sucesso)
        if result.get('sucesso') and result.get('protocolo'):
            logger.info(f'[{JOB_NAME}] Protocolo lote {batch_number}: {result["protocolo"]}')
            # Atualizar semáforo com sucesso
            # validate_response_comissao será chamada externamente com os dados individuais
        
        return result
        
    except Exception as e:
        if src.print_payloads:
            print(f'  └─ EXCEÇÃO ao processar lote {batch_number}: {str(e)}')
        logger.error(f'[{JOB_NAME}] Erro ao processar lote {batch_number}: {str(e)}')
        return {
            'sucesso': False,
            'mensagem': str(e),
            'total_sucesso': 0,
            'total_erro': len(rows)
        }


def validate_response_comissao(response, rows: List[dict], db_config, send_logs: bool) -> None:
    """
    Valida resposta da API e atualiza semáforo para cada comissão
    
    Args:
        response: Resposta da API (lista de objetos com sucesso/erro)
        rows: Lista de dicionários originais (rows da query)
        db_config: Configuração do banco de dados
        send_logs: Flag para envio de logs
    
    Estrutura esperada da response:
        [
            {
                'identificador': '123456',       # CODTRANSACAO
                'identificador2': 'A2W-44003',   # REFERENCIA
                'sucesso': 1 ou 0,
                'Message': 'msg de erro (se sucesso=0)'
            },
            ...
        ]
    
    Semáforo:
        - IDENTIFICADOR: CODTRANSACAO (codtransacao)
        - IDENTIFICADOR2: REFERENCIA (referencia)
        - tipo_id: 27 (IntegrationType.COMISSAO)
    
    Example:
        validate_response_comissao(api_response, rows_batch, db_config, True)
    """
    if not response:
        logger.warning(f"[{JOB_NAME}] validate_response_comissao | Resposta vazia")
        return
    
    # Validar se resposta é string (erro da API)
    if isinstance(response, str):
        logger.error(f"[{JOB_NAME}] validate_response_comissao | API retornou erro (string): {response}")
        OnlineLogger.send_log(
            JOB_NAME,
            send_logs,
            True,
            f'API retornou erro: {response[:200]}',
            LogType.ERROR,
            'COMISSAO')
        return
    
    # Se não é lista, tentar converter
    if not isinstance(response, list):
        logger.error(f"[{JOB_NAME}] validate_response_comissao | Resposta não é lista: {type(response)}")
        return
    
    try:
        conexao = database.Connection(db_config)
        conn = conexao.get_conect()
        cursor = conn.cursor()

        # Percorrer todos os registros da resposta
        for item in response:
            try:
                # A API retorna dicts, não objetos
                if not isinstance(item, dict):
                    logger.warning(f"[{JOB_NAME}] validate_response_comissao | Item não é dict: {type(item)}")
                    continue
                
                # Validar campos obrigatórios
                if 'identificador' not in item:
                    logger.warning(f"[{JOB_NAME}] validate_response_comissao | Item sem 'identificador': {item}")
                    continue
                
                identificador = str(item.get('identificador'))  # CODORDTRANS
                identificador2 = str(item.get('identificador2', ''))  # CODTRANSACAO
                
                # Determinar mensagem - aceitar sucesso como boolean ou string
                sucesso_val = item.get('sucesso')
                if sucesso_val in (True, 1, '1', 'true', 'True', 'SUCESSO'):
                    msgret = item.get('mensagem', 'SUCESSO')[:150]
                else:
                    # Erro
                    msgret = str(item.get('mensagem', item.get('Message', 'Erro desconhecido')))[:150]
                    OnlineLogger.send_log(
                        JOB_NAME,
                        send_logs,
                        False,
                        f'Erro ao enviar Comissão {identificador}/{identificador2}: {msgret}',
                        LogType.WARNING,
                        f'{identificador}-{identificador2}')
                
                # Atualizar semáforo
                cursor.execute(
                    queries.get_insert_update_semaphore_command(db_config.db_type),
                    queries.get_command_parameter(db_config.db_type, [
                        identificador,
                        identificador2,
                        queries.IntegrationType.COMISSAO.value,
                        msgret
                    ])
                )
                
            except Exception as e:
                logger.error(f"[{JOB_NAME}] validate_response_comissao | Erro ao processar item: {str(e)}")
                OnlineLogger.send_log(
                    JOB_NAME,
                    send_logs,
                    True,
                    f'Erro ao processar item da resposta: {str(e)}',
                    LogType.ERROR,
                    'COMISSAO')
        
        cursor.close()
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.exception(f"[{JOB_NAME}] validate_response_comissao | Erro geral: {str(e)}")
        OnlineLogger.send_log(
            JOB_NAME,
            send_logs,
            True,
            f'Erro ao validar resposta da API: {str(e)}',
            LogType.ERROR,
            'COMISSAO')


def log_final_statistics(stats: dict, send_logs: bool) -> None:
    """
    Loga estatísticas finais da sincronização
    
    Args:
        stats: Dicionário com estatísticas
        send_logs: Flag de envio de logs
    
    Example:
        log_final_statistics({
            'total_registros': 20000,
            'total_lotes': 20,
            'total_sucesso': 19500,
            'total_erro': 500,
            'duracao': 120.5
        }, True)
    """
    if src.print_payloads:
        print('Total de registros: {}'.format(stats["total_registros"]))
        print('Total de lotes: {}'.format(stats["total_lotes"]))
        print('Sucesso: {}'.format(stats["total_sucesso"]))
        print('Erro: {}'.format(stats["total_erro"]))
        print('Duração: {:.2f}s'.format(stats.get("duracao", 0)))
        if stats['total_registros'] > 0:
            taxa_sucesso = (stats['total_sucesso'] / stats['total_registros']) * 100
            print('Taxa de sucesso: {:.2f}%'.format(taxa_sucesso))
        print('='*60)
    
    logger.info(f'[{JOB_NAME}] ===== ESTATÍSTICAS FINAIS =====')
    logger.info(f'[{JOB_NAME}] Total de registros: {stats["total_registros"]}')
    logger.info(f'[{JOB_NAME}] Total de lotes: {stats["total_lotes"]}')
    logger.info(f'[{JOB_NAME}] Sucesso: {stats["total_sucesso"]}')
    logger.info(f'[{JOB_NAME}] Erro: {stats["total_erro"]}')
    logger.info(f'[{JOB_NAME}] Duração: {stats.get("duracao", 0):.2f}s')
    
    # Taxa de sucesso
    if stats['total_registros'] > 0:
        taxa_sucesso = (stats['total_sucesso'] / stats['total_registros']) * 100
        logger.info(f'[{JOB_NAME}] Taxa de sucesso: {taxa_sucesso:.2f}%')
    
    # Log online
    OnlineLogger.send_log(
        JOB_NAME,
        send_logs,
        False,
        f'Sincronização concluída: {stats["total_registros"]} registros, '
        f'{stats["total_lotes"]} lotes, {stats["total_sucesso"]} sucesso, '
        f'{stats["total_erro"]} erro, {stats.get("duracao", 0):.2f}s',
        LogType.INFO,
        'COMISSAO')
