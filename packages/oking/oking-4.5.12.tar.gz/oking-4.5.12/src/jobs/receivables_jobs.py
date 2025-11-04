"""
Job de Sincronização de Contas a Receber com OKING Hub
========================================================

Autor: Sistema OKING Hub
Data: 2025-10-31
Versão: 1.0.0

Descrição:
    Sincroniza contas a receber (duplicatas/títulos) do ERP com o OKING Hub,
    processando em lotes configuráveis via tamanho_pacote (default: 1000).
    
    Utiliza semáforo para sincronização incremental baseada em data_alteracao,
    garantindo que apenas registros novos ou modificados sejam enviados.

Features:
    - Processamento em lotes (batch size dinâmico via tamanho_pacote)
    - Sincronização incremental com LEFT JOIN semáforo
    - Identificadores: codcabrecpag + cgccpf
    - Suporte a Oracle, Firebird, SQL Server, MySQL
    - Validação de respostas individuais
    - Logging completo de progresso
    - Tratamento robusto de erros

Dependências:
    - src.api.entities.contas_a_receber (ContasAReceber)
    - src.api.okinghub (post_contas_a_receber)
    - src.database.queries (IntegrationType)
    - src.database.connection (get_database_connection)

Exemplo de Uso:
    config = {
        'send_logs': True,
        'sql': 'QUERY_CONTAS_RECEBER_COM_SEMAFORO.sql',
        'tamanho_pacote': 500  # Opcional, default: 1000
    }
    job_sincroniza_contas_receber(config)
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import time

# Importações internas
from src.api.entities.contas_a_receber import ContasAReceber
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
DEFAULT_BATCH_SIZE = 1000  # Tamanho padrão do lote
JOB_NAME = 'SINCRONIZA_CONTAS_RECEBER'


def job_sincroniza_contas_receber(job_config: dict) -> None:
    """
    Job principal de sincronização de contas a receber
    
    Fluxo de Execução:
        1. Conecta ao banco de dados
        2. Executa query com LEFT JOIN semáforo
        3. Divide registros em lotes configuráveis
        4. Para cada lote:
           a. Converte para objetos ContasAReceber
           b. Envia via post_contas_a_receber()
           c. Valida respostas individuais
           d. Atualiza semáforo (MERGE/UPSERT)
        5. Loga estatísticas finais
    
    Args:
        job_config (dict): Configuração do job
            - send_logs (bool): Enviar logs online
            - sql (str): Path para arquivo SQL com query
            - tamanho_pacote (int, optional): Tamanho do lote (default: 1000)
            - db_host, db_user, db_password, etc: Configurações do banco
    
    Returns:
        None
    
    Example:
        config = {
            'send_logs': True,
            'sql': 'QUERY_CONTAS_RECEBER_COM_SEMAFORO.sql',
            'tamanho_pacote': 500,
            'db_host': 'localhost',
            'connection_type': 'mysql'
        }
        job_sincroniza_contas_receber(config)
    """
    send_logs = job_config.get('send_logs', True)
    sql_file = job_config.get('sql')
    
    # Obter tamanho_pacote dinâmico (com fallback para 1000)
    tamanho_pacote = job_config.get('tamanho_pacote')
    if tamanho_pacote is None or tamanho_pacote == 0 or not isinstance(tamanho_pacote, int):
        tamanho_pacote = DEFAULT_BATCH_SIZE
        logger.info(f'[{JOB_NAME}] tamanho_pacote não configurado ou inválido, usando default: {DEFAULT_BATCH_SIZE}')
    else:
        logger.info(f'[{JOB_NAME}] tamanho_pacote configurado: {tamanho_pacote}')
    
    logger.info(f'[{JOB_NAME}] ========================================')
    logger.info(f'[{JOB_NAME}] Iniciando sincronização de contas a receber')
    logger.info(f'[{JOB_NAME}] Batch size: {tamanho_pacote}')
    logger.info(f'[{JOB_NAME}] ========================================')
    
    # Obter configuração do banco
    db_config = utils.get_database_config(job_config)
    
    # Estatísticas
    stats = {
        'total_registros': 0,
        'total_lotes': 0,
        'total_sucesso': 0,
        'total_erro': 0,
        'inicio': datetime.now()
    }
    
    # Conexão com banco de dados
    connection = None
    cursor = None
    
    try:
        # Conectar ao banco (padrão OKING HUB)
        logger.info(f'[{JOB_NAME}] Conectando ao banco de dados...')
        db = database.Connection(db_config)
        connection = db.get_conect()
        
        if connection is None:
            logger.error(f'[{JOB_NAME}] Falha ao conectar ao banco de dados')
            OnlineLogger.send_log(
                JOB_NAME,
                send_logs,
                True,
                'Falha ao conectar ao banco de dados',
                LogType.ERROR,
                'CONTAS_A_RECEBER'
            )
            return
        
        cursor = connection.cursor()
        logger.info(f'[{JOB_NAME}] Conexão estabelecida com sucesso')
        
        # Ler query SQL do arquivo
        if sql_file:
            logger.info(f'[{JOB_NAME}] Lendo query de: {sql_file}')
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_query = f.read()
            except FileNotFoundError:
                logger.error(f'[{JOB_NAME}] Arquivo SQL não encontrado: {sql_file}')
                OnlineLogger.send_log(
                    JOB_NAME,
                    send_logs,
                    True,
                    f'Arquivo SQL não encontrado: {sql_file}',
                    LogType.ERROR,
                    'CONTAS_A_RECEBER'
                )
                return
        else:
            logger.error(f'[{JOB_NAME}] Query SQL não configurada')
            OnlineLogger.send_log(
                JOB_NAME,
                send_logs,
                True,
                'Query SQL não configurada no job',
                LogType.ERROR,
                'CONTAS_A_RECEBER'
            )
            return
        
        # Executar query
        logger.info(f'[{JOB_NAME}] Executando query para buscar contas a receber...')
        cursor.execute(sql_query)
        
        # Obter nomes das colunas (importante para usar row.get('nome_coluna'))
        column_names = [desc[0].lower() for desc in cursor.description]
        logger.info(f'[{JOB_NAME}] Colunas retornadas: {len(column_names)}')
        
        # Buscar todos os registros
        rows = cursor.fetchall()
        stats['total_registros'] = len(rows)
        
        logger.info(f'[{JOB_NAME}] Total de registros encontrados: {stats["total_registros"]}')
        
        if stats['total_registros'] == 0:
            logger.info(f'[{JOB_NAME}] Nenhuma conta a receber para sincronizar')
            OnlineLogger.send_log(
                JOB_NAME,
                send_logs,
                False,
                'Nenhuma conta a receber encontrada para sincronização',
                LogType.INFO,
                'CONTAS_A_RECEBER'
            )
            return
        
        # Converter rows para dicionários
        logger.info(f'[{JOB_NAME}] Convertendo registros para dicionários...')
        rows_dict = []
        for row in rows:
            row_dict = {}
            for idx, col_name in enumerate(column_names):
                row_dict[col_name] = row[idx]
            rows_dict.append(row_dict)
        
        # Processar em lotes
        logger.info(f'[{JOB_NAME}] Iniciando processamento em lotes de {tamanho_pacote}')
        
        for i in range(0, len(rows_dict), tamanho_pacote):
            batch = rows_dict[i:i + tamanho_pacote]
            stats['total_lotes'] += 1
            
            logger.info(f'[{JOB_NAME}] ----------------------------------------')
            logger.info(f'[{JOB_NAME}] Processando lote {stats["total_lotes"]} ({len(batch)} registros)')
            logger.info(f'[{JOB_NAME}] ----------------------------------------')
            
            # Processar lote
            result = process_batch(
                batch=batch,
                send_logs=send_logs,
                connection=connection,
                connection_type=db_config['connection_type']
            )
            
            stats['total_sucesso'] += result['sucesso']
            stats['total_erro'] += result['erro']
            
            logger.info(f'[{JOB_NAME}] Lote {stats["total_lotes"]} concluído: {result["sucesso"]} sucesso, {result["erro"]} erro')
            
            # Sleep entre lotes para evitar sobrecarga
            if i + tamanho_pacote < len(rows_dict):
                time.sleep(0.5)
        
        # Log final
        stats['fim'] = datetime.now()
        stats['duracao'] = (stats['fim'] - stats['inicio']).total_seconds()
        
        logger.info(f'[{JOB_NAME}] ========================================')
        logger.info(f'[{JOB_NAME}] RESUMO DA SINCRONIZAÇÃO')
        logger.info(f'[{JOB_NAME}] ========================================')
        logger.info(f'[{JOB_NAME}] Total de registros: {stats["total_registros"]}')
        logger.info(f'[{JOB_NAME}] Total de lotes: {stats["total_lotes"]}')
        logger.info(f'[{JOB_NAME}] Total sucesso: {stats["total_sucesso"]}')
        logger.info(f'[{JOB_NAME}] Total erro: {stats["total_erro"]}')
        logger.info(f'[{JOB_NAME}] Duração: {stats["duracao"]:.2f} segundos')
        logger.info(f'[{JOB_NAME}] ========================================')
        
        # Log online
        OnlineLogger.send_log(
            JOB_NAME,
            send_logs,
            False,
            f'Sincronização concluída: {stats["total_sucesso"]} sucesso, {stats["total_erro"]} erro em {stats["duracao"]:.2f}s',
            LogType.INFO,
            'CONTAS_A_RECEBER'
        )
        
    except Exception as e:
        logger.error(f'[{JOB_NAME}] Erro crítico na sincronização: {str(e)}', exc_info=True)
        OnlineLogger.send_log(
            JOB_NAME,
            send_logs,
            True,
            f'Erro crítico: {str(e)}',
            LogType.ERROR,
            'CONTAS_A_RECEBER'
        )
    
    finally:
        # Fechar conexões
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logger.info(f'[{JOB_NAME}] Conexão com banco encerrada')


def process_batch(batch: List[Dict[str, Any]], send_logs: bool, connection, connection_type: str) -> Dict[str, int]:
    """
    Processa um lote de contas a receber
    
    Args:
        batch: Lista de dicionários com dados das contas
        send_logs: Flag para enviar logs
        connection: Conexão com banco de dados
        connection_type: Tipo do banco (mysql, oracle, etc)
    
    Returns:
        Dict com contadores de sucesso e erro
    """
    result = {'sucesso': 0, 'erro': 0}
    
    try:
        # Converter batch para objetos ContasAReceber
        contas = []
        for row in batch:
            try:
                conta = ContasAReceber(
                    codcabrecpag=row.get('codcabrecpag'),
                    referencia=row.get('referencia'),
                    codfilial=row.get('codfilial'),
                    datalimi=row.get('datalimi'),
                    datavcto=row.get('datavcto'),
                    emissao=row.get('emissao'),
                    documento=row.get('documento'),
                    valor=row.get('valor'),
                    valorpg=row.get('valorpg'),
                    valorjurosdesc=row.get('valorjurosdesc'),
                    valordev=row.get('valordev'),
                    valordcom=row.get('valordcom'),
                    cotacao=row.get('cotacao'),
                    cotacaobaixa=row.get('cotacaobaixa'),
                    juros=row.get('juros'),
                    juroslimi=row.get('juroslimi'),
                    multa=row.get('multa'),
                    antecipacao=row.get('antecipacao'),
                    pontualidade=row.get('pontualidade'),
                    tipojuro=row.get('tipojuro'),
                    tipojurovcto=row.get('tipojurovcto'),
                    obs=row.get('obs'),
                    fdatabase=row.get('fdatabase'),
                    fdatavcto=row.get('fdatavcto'),
                    fiof=row.get('fiof'),
                    fiofembutido=row.get('fiofembutido'),
                    tipoantec=row.get('tipoantec'),
                    codfilial_empresa=row.get('codfilial_empresa'),
                    tipodoc=row.get('tipodoc'),
                    vlradicional=row.get('vlradicional'),
                    efeito2=row.get('efeito2'),
                    nrobloqueto=row.get('nrobloqueto'),
                    nossonumero=row.get('nossonumero'),
                    d_dtassinat=row.get('d_dtassinat'),
                    desc_const=row.get('desc_const'),
                    vlrjurosdiario=row.get('vlrjurosdiario'),
                    naoconciliado=row.get('naoconciliado'),
                    codfatura=row.get('codfatura'),
                    vlrantecipacaodiario=row.get('vlrantecipacaodiario'),
                    datadesconto=row.get('datadesconto'),
                    codcrsituacao=row.get('codcrsituacao'),
                    codclifor=row.get('codclifor'),
                    classifica=row.get('classifica'),
                    codunidclifor=row.get('codunidclifor'),
                    cgccpf=row.get('cgccpf'),
                    datalimcredito=row.get('datalimcredito'),
                    limcredito=row.get('limcredito'),
                    codmoedalim=row.get('codmoedalim'),
                    efeito=row.get('efeito'),
                    codgrupoclifor=row.get('codgrupoclifor'),
                    codgrupoclifor2=row.get('codgrupoclifor2'),
                    ecliente=row.get('ecliente'),
                    eforneced=row.get('eforneced'),
                    etransportador=row.get('etransportador'),
                    clienteavista=row.get('clienteavista'),
                    respcobranca=row.get('respcobranca'),
                    respcobranca_nome=row.get('respcobranca_nome'),
                    nomeprodutor=row.get('nomeprodutor'),
                    vctolimcredito=row.get('vctolimcredito'),
                    categoria=row.get('categoria'),
                    descsetor=row.get('descsetor'),
                    codimovelrural=row.get('codimovelrural'),
                    codformapgto=row.get('codformapgto'),
                    codbandeira=row.get('codbandeira'),
                    codbanco=row.get('codbanco'),
                    codbancodia=row.get('codbancodia'),
                    cobranca=row.get('cobranca'),
                    codmoeda=row.get('codmoeda'),
                    codperfilfin=row.get('codperfilfin'),
                    ultbaixa=row.get('ultbaixa'),
                    codcobrador=row.get('codcobrador'),
                    codtipotr=row.get('codtipotr'),
                    desctipotr=row.get('desctipotr'),
                    descsitduplicata=row.get('descsitduplicata')
                )
                contas.append(conta)
            except Exception as e:
                logger.error(f'[{JOB_NAME}] Erro ao criar objeto ContasAReceber: {str(e)}')
                result['erro'] += 1
                continue
        
        if not contas:
            logger.warning(f'[{JOB_NAME}] Nenhuma conta válida no lote')
            return result
        
        logger.info(f'[{JOB_NAME}] Enviando {len(contas)} contas para API...')
        
        # Enviar para API
        api_response = okinghub.post_contas_a_receber(send_logs, contas)
        
        # Validar resposta
        validation_result = validate_response_contas_receber(
            api_response=api_response,
            batch=batch,
            send_logs=send_logs,
            connection=connection,
            connection_type=connection_type
        )
        
        result['sucesso'] = validation_result['sucesso']
        result['erro'] = validation_result['erro']
        
    except Exception as e:
        logger.error(f'[{JOB_NAME}] Erro ao processar lote: {str(e)}', exc_info=True)
        result['erro'] = len(batch)
    
    return result


def validate_response_contas_receber(
    api_response: dict,
    batch: List[Dict[str, Any]],
    send_logs: bool,
    connection,
    connection_type: str
) -> Dict[str, int]:
    """
    Valida resposta da API e atualiza semáforo
    
    Args:
        api_response: Resposta da API post_contas_a_receber
        batch: Lista de dicionários com dados originais
        send_logs: Flag para enviar logs
        connection: Conexão com banco de dados
        connection_type: Tipo do banco
    
    Returns:
        Dict com contadores de sucesso e erro
    """
    result = {'sucesso': 0, 'erro': 0}
    
    try:
        # Verificar se API retornou sucesso
        if not api_response.get('sucesso'):
            logger.error(f'[{JOB_NAME}] API retornou erro: {api_response.get("mensagem")}')
            result['erro'] = len(batch)
            return result
        
        # Obter lista de respostas individuais
        response_list = api_response.get('response', [])
        
        if not isinstance(response_list, list):
            logger.warning(f'[{JOB_NAME}] API não retornou lista de respostas, usando totais agregados')
            result['sucesso'] = api_response.get('total_sucesso', 0)
            result['erro'] = api_response.get('total_erro', 0)
            
            # Atualizar semáforo para todos (assumindo sucesso)
            if result['sucesso'] > 0:
                insert_update_semaphore_receivables(
                    batch=batch,
                    connection=connection,
                    connection_type=connection_type,
                    status='SUCESSO'
                )
            
            return result
        
        # Validar respostas individuais
        logger.info(f'[{JOB_NAME}] Validando {len(response_list)} respostas individuais...')
        
        successful_items = []
        
        for idx, response_item in enumerate(response_list):
            if idx >= len(batch):
                break
            
            original_item = batch[idx]
            
            try:
                # Verificar sucesso do item
                sucesso_val = response_item.get('sucesso') if isinstance(response_item, dict) else False
                
                # Aceitar múltiplos formatos de sucesso
                if sucesso_val in (True, 1, '1', 'true', 'True', 'SUCESSO'):
                    result['sucesso'] += 1
                    successful_items.append(original_item)
                else:
                    result['erro'] += 1
                    mensagem_erro = response_item.get('mensagem', 'Erro desconhecido') if isinstance(response_item, dict) else 'Erro desconhecido'
                    logger.warning(f'[{JOB_NAME}] Conta {original_item.get("codcabrecpag")} com erro: {mensagem_erro}')
            
            except Exception as e:
                logger.error(f'[{JOB_NAME}] Erro ao validar resposta do item {idx}: {str(e)}')
                result['erro'] += 1
        
        # Atualizar semáforo apenas para itens com sucesso
        if successful_items:
            logger.info(f'[{JOB_NAME}] Atualizando semáforo para {len(successful_items)} itens bem-sucedidos...')
            insert_update_semaphore_receivables(
                batch=successful_items,
                connection=connection,
                connection_type=connection_type,
                status='SUCESSO'
            )
        
        logger.info(f'[{JOB_NAME}] Validação concluída: {result["sucesso"]} sucesso, {result["erro"]} erro')
        
    except Exception as e:
        logger.error(f'[{JOB_NAME}] Erro ao validar resposta: {str(e)}', exc_info=True)
        result['erro'] = len(batch)
    
    return result


def insert_update_semaphore_receivables(
    batch: List[Dict[str, Any]],
    connection,
    connection_type: str,
    status: str
) -> None:
    """
    Atualiza semáforo para contas a receber processadas
    
    Identificadores:
        - identificador: codcabrecpag (VARCHAR 100)
        - identificador2: cgccpf (VARCHAR 100)
        - tipo_id: 28 (IntegrationType.CONTAS_A_RECEBER)
    
    Args:
        batch: Lista de dicionários com dados das contas
        connection: Conexão com banco de dados
        connection_type: Tipo do banco
        status: Status a ser registrado ('SUCESSO' ou 'ERRO')
    """
    try:
        cursor = connection.cursor()
        
        # Obter comando MERGE/UPSERT apropriado
        merge_command = queries.get_semaphore_command_data_sincronizacao(connection_type)
        
        # Preparar parâmetros
        params = []
        for item in batch:
            codcabrecpag = str(item.get('codcabrecpag', ''))
            cgccpf = str(item.get('cgccpf', ''))
            
            if not codcabrecpag:
                logger.warning(f'[{JOB_NAME}] Item sem codcabrecpag, pulando semáforo')
                continue
            
            # (identificador, identificador2, tipo_id, mensagem)
            params.append((
                codcabrecpag,
                cgccpf,
                queries.IntegrationType.CONTAS_A_RECEBER.value,
                status
            ))
        
        if not params:
            logger.warning(f'[{JOB_NAME}] Nenhum parâmetro válido para semáforo')
            return
        
        # Executar em lote
        logger.info(f'[{JOB_NAME}] Atualizando semáforo para {len(params)} registros...')
        
        if connection_type.lower() == 'mysql':
            cursor.executemany(merge_command, params)
        else:
            for param in params:
                cursor.execute(merge_command, param)
        
        connection.commit()
        logger.info(f'[{JOB_NAME}] Semáforo atualizado com sucesso')
        
    except Exception as e:
        logger.error(f'[{JOB_NAME}] Erro ao atualizar semáforo: {str(e)}', exc_info=True)
        connection.rollback()
    finally:
        if cursor:
            cursor.close()
