"""Este módulo guarda todas as funções do MCP visíveis para o Agente usar"""

from os import getenv
from typing import Literal, Sequence
import aiohttp
import ujson
from siga_mcp._types import (
    CategoriasInfraestruturaType,
    EquipeInfraestruturaType,
    EquipeSistemasType,
    FiltrosOSType,
    OrigemAtendimentoAvulsoSistemasType,
    ProjetoType,
    SistemasType,
    TipoAtendimentoAvulsoInfraestruturaType,
    TipoOsSistemasType,
    LinguagemOsSistemasType,
    OrigemOsSistemasType,
    OsInternaSistemasType,
    StatusOsType,
    CriticidadeOsType,
    PrioridadeUsuarioOsType,
)
from siga_mcp.dynamic_constants import (
    CATEGORIA_TO_NUMBER,
    EQUIPE_INFRAESTRUTURA_TO_NUMBER,
    EQUIPE_TO_NUMBER,
    PROJETO_TO_NUMBER,
    SISTEMA_TO_NUMBER,
    TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA,
    TIPO_TO_NUMBER_OS_SISTEMAS,
    LINGUAGEM_TO_NUMBER_OS_SISTEMAS,
    ORIGEM_OS_TO_NUMBER,
    OS_INTERNA_OS_TO_NUMBER,
    STATUS_OS_TO_NUMBER,
    CRITICIDADE_OS_TO_NUMBER,
    PRIORIDADE_USUARIO_OS_TO_NUMBER,
)
from siga_mcp.dynamic_constants import (
    USUARIOS_SISTEMAS_IDS,
    USUARIOS_INFRAESTRUTURA_IDS,
    USUARIOS_SISTEMAS_PARA_ERRO,
    USUARIOS_INFRAESTRUTURA_PARA_ERRO,
)
from siga_mcp.decorators import controlar_acesso_matricula
from siga_mcp.utils import converter_data_siga
from siga_mcp.xml_builder import XMLBuilder


async def buscar_todas_os_usuario(
    *,
    matricula: str | Sequence[str] | Literal["CURRENT_USER"] | None = "CURRENT_USER",
    os: str | Sequence[str] | None = None,
    filtrar_por: Sequence[FiltrosOSType]
    | Literal["Todas OS em Aberto"]
    | str
    | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> str:
    if not matricula and not os:
        return "Erro: É necessário informar pelo menos a matrícula ou o código da OS para realizar a consulta."

    if filtrar_por == "Todas OS em Aberto":
        filtrar_por = [
            "Pendente-Atendimento",
            "Em Teste",
            "Pendente-Teste",
            "Em Atendimento",
            "Em Implantação",
            "Pendente-Liberação",
            "Não Planejada",
            "Pendente-Sist. Administrativos",
            "Pendente-AVA",
            "Pendente-Consultoria",
            "Solicitação em Aprovação",
            "Pendente-Aprovação",
            "Pendente-Sist. Acadêmicos",
            "Pendente-Marketing",
            "Pendente-Equipe Manutenção",
            "Pendente-Equipe Infraestrutura",
            "Pendente-Atualização de Versão",
            "Pendente-Help-Desk",
            "Pendente-Fornecedor",
            "Pendente-Usuário",
        ]

    async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
        async with session.post(
            "https://ava3.uniube.br/ava/api/os/buscarTodasOsPorMatriculaSigaIA/",
            json={
                "descricaoStatusOs": filtrar_por or "",  # Array ou string puro
                "matricula": matricula or "",  # Array ou string puro
                "codOs": os or "",  # Array ou string puro
                "dataIni": converter_data_siga(data_inicio) if data_inicio else "",
                "dataFim": converter_data_siga(data_fim) if data_fim else "",
                "apiKey": getenv("AVA_API_KEY"),
            },
        ) as response:
            try:
                # Verifica se a requisição HTTP foi bem-sucedida (status 2xx)
                # response.raise_for_status()

                data = await response.json(content_type=None)
                retorno = XMLBuilder().build_xml(
                    data=data["result"],
                    root_element_name="ordens_servico",
                    item_element_name="ordem_servico",
                    root_attributes={"matricula": str(matricula)},
                    custom_attributes={"sistema": "SIGA"},
                )

                return retorno

            except Exception as e:
                # Captura qualquer outro erro não previsto
                return f"Erro ao consultar dados da(s) OS. {e} Matrícula: {matricula}"


@controlar_acesso_matricula
async def inserir_os_sistemas(
    data_solicitacao: str,
    assunto: str,
    descricao: str,
    responsavel: str | Literal["CURRENT_USER"],
    responsavel_atual: str | Literal["CURRENT_USER"],
    matSolicitante: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    criada_por: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    prioridade: str | None = None,
    tempo_previsto: int | None = None,
    data_inicio_previsto: str | None = None,
    data_limite: str | None = None,
    sprint: str | None = None,
    os_predecessora: str | None = None,
    chamado_fornecedor: str | None = None,
    os_principal: str | None = None,
    rotinas: str | None = None,
    classificacao: str | None = None,
    nova: str | None = None,
    data_previsao_entrega: str | None = None,
    modulo: str | None = None,
    tempo_restante: str | None = None,
    ramal: str | None = None,
    data_envio_email_conclusao: str | None = None,
    tipo_transacao: str | None = None,
    acao: str | None = None,
    planejamento: str | None = None,
    grupo: str | None = None,
    sistema: SistemasType = "Sistemas AVA",
    tipo: TipoOsSistemasType = "Implementação",
    equipe: EquipeSistemasType = "Equipe AVA",
    linguagem: LinguagemOsSistemasType = "PHP",
    projeto: ProjetoType = "Operação AVA",
    status: StatusOsType = "Em Atendimento",
    os_interna: OsInternaSistemasType = "Sim",
    origem: OrigemOsSistemasType = "Teams",
    prioridade_usuario: PrioridadeUsuarioOsType = "Nenhuma",
    criticidade: CriticidadeOsType = "Nenhuma",
) -> str:
    if data_solicitacao:
        data_solicitacao = converter_data_siga(data_solicitacao, manter_horas=True)

    if data_inicio_previsto:
        data_inicio_previsto = converter_data_siga(
            data_inicio_previsto, manter_horas=True
        )

    if data_limite:
        data_limite = converter_data_siga(data_limite, manter_horas=True)

    if data_previsao_entrega:
        data_previsao_entrega = converter_data_siga(
            data_previsao_entrega, manter_horas=True
        )

    if data_envio_email_conclusao:
        data_envio_email_conclusao = converter_data_siga(
            data_envio_email_conclusao, manter_horas=True
        )

    # VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
    # Validar matSolicitante
    if (
        not matSolicitante
        or matSolicitante == "0"
        or (matSolicitante != "CURRENT_USER" and not matSolicitante.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "mat_solicitante_obrigatorio",
                    "campo_invalido": "matSolicitante",
                    "valor_informado": str(matSolicitante),
                    "mensagem": f"Campo 'matSolicitante' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {matSolicitante}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar criada_por
    if (
        not criada_por
        or criada_por == "0"
        or (criada_por != "CURRENT_USER" and not criada_por.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criada_por_obrigatorio",
                    "campo_invalido": "criada_por",
                    "valor_informado": str(criada_por),
                    "mensagem": f"Campo 'criada_por' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {criada_por}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # VALIDAÇÃO DE USUÁRIOS RESPONSÁVEIS
    # Validar responsavel (se não for CURRENT_USER)
    if responsavel != "CURRENT_USER" and responsavel not in USUARIOS_SISTEMAS_IDS:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_invalido",
                    "responsavel_informado": responsavel,
                    "mensagem": f"Responsável '{responsavel}' não encontrado na lista de usuários válidos para Sistemas",
                    "usuarios_validos": USUARIOS_SISTEMAS_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar responsavel_atual (se não for CURRENT_USER)
    if (
        responsavel_atual != "CURRENT_USER"
        and responsavel_atual not in USUARIOS_SISTEMAS_IDS
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_atual_invalido",
                    "responsavel_atual_informado": responsavel_atual,
                    "mensagem": f"Responsável atual '{responsavel_atual}' não encontrado na lista de usuários válidos para Sistemas",
                    "usuarios_validos": USUARIOS_SISTEMAS_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Busca o tipo correto na constante TIPO_TO_NUMBER_OS_SISTEMAS ignorando maiúsculas/minúsculas
    tipo_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário TIPO_TO_NUMBER_OS_SISTEMAS
        (
            key
            for key in TIPO_TO_NUMBER_OS_SISTEMAS.keys()
            # Compara a chave atual em minúsculas com o tipo recebido em minúsculas
            if str(key).lower() == str(tipo).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um tipo válido após a busca case-insensitive
    if tipo_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "tipo_invalido",
                    "tipo_informado": tipo,
                    "mensagem": f"Tipo '{tipo}' não encontrado na constante TIPO_TO_NUMBER_OS_SISTEMAS",
                    "tipos_validos": list(TIPO_TO_NUMBER_OS_SISTEMAS.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    tipo_final = TIPO_TO_NUMBER_OS_SISTEMAS[tipo_normalizado]

    # Busca o sistema correto na constante SISTEMA_TO_NUMBER ignorando maiúsculas/minúsculas
    sistema_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário SISTEMA_TO_NUMBER
        (
            key
            for key in SISTEMA_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o sistema recebido em minúsculas
            if str(key).lower() == str(sistema).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um sistema válido após a busca case-insensitive
    if sistema_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "sistema_invalido",
                    "sistema_informado": sistema,
                    "mensagem": f"Sistema '{sistema}' não encontrado na constante SISTEMA_TO_NUMBER",
                    "sistemas_validos": list(SISTEMA_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "inserir_os_sistemas",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    sistema_final = SISTEMA_TO_NUMBER[sistema_normalizado]

    # Busca a equipe correta na constante EQUIPE_TO_NUMBER ignorando maiúsculas/minúsculas
    equipe_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário EQUIPE_TO_NUMBER
        (
            key
            for key in EQUIPE_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a equipe recebida em minúsculas
            if str(key).lower() == str(equipe).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma equipe válida após a busca case-insensitive
    if equipe_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "equipe_invalida",
                    "equipe_informada": equipe,
                    "mensagem": f"Equipe '{equipe}' não encontrada na constante EQUIPE_TO_NUMBER",
                    "equipes_validas": list(EQUIPE_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "inserir_os_sistemas",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    equipe_final = EQUIPE_TO_NUMBER[equipe_normalizada]

    # Busca o projeto correto na constante PROJETO_TO_NUMBER ignorando maiúsculas/minúsculas
    projeto_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PROJETO_TO_NUMBER
        (
            key
            for key in PROJETO_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o projeto recebido em minúsculas
            if str(key).lower() == str(projeto).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um projeto válido após a busca case-insensitive
    if projeto_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "projeto_invalido",
                    "projeto_informado": projeto,
                    "mensagem": f"Projeto '{projeto}' não encontrado na constante PROJETO_TO_NUMBER",
                    "projetos_validos": list(PROJETO_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "inserir_os_sistemas",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    projeto_final = PROJETO_TO_NUMBER[projeto_normalizado]

    # Busca a linguagem correta na constante LINGUAGEM_TO_NUMBER_OS_SISTEMAS ignorando maiúsculas/minúsculas
    linguagem_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário LINGUAGEM_TO_NUMBER_OS_SISTEMAS
        (
            key
            for key in LINGUAGEM_TO_NUMBER_OS_SISTEMAS.keys()
            # Compara a chave atual em minúsculas com a linguagem recebida em minúsculas
            if str(key).lower() == str(linguagem).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma linguagem válida após a busca case-insensitive
    if linguagem_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "linguagem_invalida",
                    "linguagem_informada": linguagem,
                    "mensagem": f"Linguagem '{linguagem}' não encontrada na constante LINGUAGEM_TO_NUMBER_OS_SISTEMAS",
                    "linguagens_validas": list(LINGUAGEM_TO_NUMBER_OS_SISTEMAS.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    linguagem_final = LINGUAGEM_TO_NUMBER_OS_SISTEMAS[linguagem_normalizada]

    # Busca o status correto na constante STATUS_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    status_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário STATUS_OS_TO_NUMBER
        (
            key
            for key in STATUS_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o status recebido em minúsculas
            if str(key).lower() == str(status).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um status válido após a busca case-insensitive
    if status_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "status_invalido",
                    "status_informado": status,
                    "mensagem": f"Status '{status}' não encontrado na constante STATUS_OS_TO_NUMBER",
                    "status_validos": list(STATUS_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    status_final = STATUS_OS_TO_NUMBER[status_normalizado]

    # Busca a origem correta na constante ORIGEM_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    origem_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário ORIGEM_OS_TO_NUMBER
        (
            key
            for key in ORIGEM_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a origem recebida em minúsculas
            if str(key).lower() == str(origem).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma origem válida após a busca case-insensitive
    if origem_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "origem_invalida",
                    "origem_informada": origem,
                    "mensagem": f"Origem '{origem}' não encontrada na constante ORIGEM_OS_TO_NUMBER",
                    "origens_validas": list(ORIGEM_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    origem_final = ORIGEM_OS_TO_NUMBER[origem_normalizada]

    # Busca o valor correto de OS interna na constante OS_INTERNA_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    os_interna_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário OS_INTERNA_OS_TO_NUMBER
        (
            key
            for key in OS_INTERNA_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o valor de os_interna recebido em minúsculas
            if str(key).lower() == str(os_interna).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um valor válido para OS interna após a busca case-insensitive
    if os_interna_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "os_interna_invalida",
                    "os_interna_informada": os_interna,
                    "mensagem": f"OS Interna '{os_interna}' não encontrada na constante OS_INTERNA_OS_TO_NUMBER",
                    "valores_validos": list(OS_INTERNA_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    os_interna_final = OS_INTERNA_OS_TO_NUMBER[os_interna_normalizada]

    # Busca a criticidade correta na constante CRITICIDADE_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    criticidade_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário CRITICIDADE_OS_TO_NUMBER
        (
            key
            for key in CRITICIDADE_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a criticidade recebida em minúsculas
            if str(key).lower() == str(criticidade).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma criticidade válida após a busca case-insensitive
    if criticidade_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criticidade_invalida",
                    "criticidade_informada": criticidade,
                    "mensagem": f"Criticidade '{criticidade}' não encontrada na constante CRITICIDADE_OS_TO_NUMBER",
                    "criticidades_validas": list(CRITICIDADE_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    criticidade_final = CRITICIDADE_OS_TO_NUMBER[criticidade_normalizada]

    # Busca a prioridade do usuário correta na constante PRIORIDADE_USUARIO_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    prioridade_usuario_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PRIORIDADE_USUARIO_OS_TO_NUMBER
        (
            key
            for key in PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a prioridade_usuario recebida em minúsculas
            if str(key).lower() == str(prioridade_usuario).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma prioridade do usuário válida após a busca case-insensitive
    if prioridade_usuario_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "prioridade_usuario_invalida",
                    "prioridade_usuario_informada": prioridade_usuario,
                    "mensagem": f"Prioridade do usuário '{prioridade_usuario}' não encontrada na constante PRIORIDADE_USUARIO_OS_TO_NUMBER",
                    "prioridades_validas": list(PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    prioridade_usuario_final = PRIORIDADE_USUARIO_OS_TO_NUMBER[
        prioridade_usuario_normalizada
    ]

    try:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                "https://ava3.uniube.br/ava/api/os/inserirOsSigaIA/",
                json={
                    "apiKey": getenv("AVA_API_KEY"),
                    "dtSolicitacao": data_solicitacao,
                    "assunto": assunto,
                    "descricao": descricao,
                    "matSolicitante": matSolicitante,
                    "nmSolicitante": "",
                    "centroCusto": "",
                    "setor": "",
                    "origem": origem_final,
                    "tipo": tipo_final,
                    "status": status_final,
                    "equipe": equipe_final,
                    "responsavel": responsavel,
                    "responsavelAtual": responsavel_atual,
                    "matGestor": "",
                    "criadaPor": criada_por,
                    "classe": 1,
                    "osInterna": os_interna_final,
                    "campus": "",
                    "sistema": sistema_final or "",
                    "linguagem": linguagem_final or "",
                    "categoria": "",
                    "projeto": projeto_final or "",
                    "prioridade": prioridade or "",
                    "tempo_previsto": tempo_previsto or "",
                    "dtInicioPrevisto": data_inicio_previsto or "",
                    "dtLimite": data_limite or "",
                    "sprint": sprint or "",
                    "dtConclusao": "",
                    "osPredecessora": os_predecessora or "",
                    "chamadoFornecedor": chamado_fornecedor or "",
                    "osPrincipal": os_principal or "",
                    "rotinas": rotinas or "",
                    "plaqueta": "",
                    "classificacao": classificacao or "",
                    "criticidade": criticidade_final or "",
                    "nova": nova or "",
                    "dtPrevisaoEntrega": data_previsao_entrega or "",
                    "prioridadeUsuario": prioridade_usuario_final or "",
                    "modulo": modulo or "",
                    "tempoRestante": tempo_restante or "",
                    "ramal": ramal or "",
                    "dtEnvioEmailConclusao": data_envio_email_conclusao or "",
                    "tipoTransacao": tipo_transacao or "",
                    "acao": acao or "",
                    "planejamento": planejamento or "",
                    "grupo": grupo or "",
                },
            ) as response:
                json_response = await response.json(content_type=None)
                result_data = json_response.get("result")

                # Trata a resposta
                if result_data is None:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Não foi possível salvar a OS. Verifique as informações digitadas.",
                        }
                    ]
                elif result_data == 1:
                    data_final = [
                        {
                            "status": "sucesso",
                            "mensagem": "OS cadastrado com sucesso!",
                        }
                    ]
                else:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Erro ao gravar a OS. Tente novamente.",
                        }
                    ]

                # Adiciona os root_attributes
                return XMLBuilder().build_xml(
                    data=data_final,
                    root_element_name="ordens_servico",
                    item_element_name="ordem_servico",
                    root_attributes={
                        "dtSolicitacao": str(data_solicitacao),
                        "assunto": str(assunto),
                        "descricao": str(descricao),
                        "matSolicitante": str(matSolicitante),
                        "origem": str(origem_final),
                        "tipo": str(tipo_final),
                        "status": str(status_final),
                        "equipe": str(equipe_final),
                        "responsavel": str(responsavel),
                        "responsavelAtual": str(responsavel_atual),
                        "criadaPor": str(criada_por),
                        "osInterna": str(os_interna_final),
                        "sistema": str(sistema_final),
                        "linguagem": str(linguagem_final),
                        "projeto": str(projeto_final),
                        "prioridade": str(prioridade),
                        "tempo_previsto": str(tempo_previsto),
                        "dtInicioPrevisto": str(data_inicio_previsto),
                        "dtLimite": str(data_limite),
                        "sprint": str(sprint),
                        "osPredecessora": str(os_predecessora),
                        "chamadoFornecedor": str(chamado_fornecedor),
                        "osPrincipal": str(os_principal),
                        "rotinas": str(rotinas),
                        "classificacao": str(classificacao),
                        "criticidade": str(criticidade_final),
                        "nova": str(nova),
                        "dtPrevisaoEntrega": str(data_previsao_entrega),
                        "prioridadeUsuario": str(prioridade_usuario_final),
                        "modulo": str(modulo),
                        "tempoRestante": str(tempo_restante),
                        "ramal": str(ramal),
                        "dtEnvioEmailConclusao": str(data_envio_email_conclusao),
                        "tipoTransacao": str(tipo_transacao),
                        "acao": str(acao),
                        "planejamento": str(planejamento),
                        "grupo": str(grupo),
                    },
                    custom_attributes={"sistema": "SIGA"},
                )

    except Exception as e:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "mensagem": f"Erro interno: {str(e)}. Tente novamente mais tarde.",
                }
            ],
            root_element_name="resultado",
            item_element_name="item",
            custom_attributes={"sistema": "SIGA"},
        )


@controlar_acesso_matricula
async def inserir_os_infraestrutura(
    data_solicitacao: str,
    assunto: str,
    descricao: str,
    responsavel: str | Literal["CURRENT_USER"],
    responsavel_atual: str | Literal["CURRENT_USER"],
    matSolicitante: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    criada_por: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    prioridade: str | None = None,
    tempo_previsto: int | None = None,
    data_inicio_previsto: str | None = None,
    data_limite: str | None = None,
    sprint: str | None = None,
    os_predecessora: str | None = None,
    chamado_fornecedor: str | None = None,
    os_principal: str | None = None,
    plaqueta: str | None = None,
    rotinas: str | None = None,
    classificacao: str | None = None,
    nova: str | None = None,
    data_previsao_entrega: str | None = None,
    modulo: str | None = None,
    tempo_restante: str | None = None,
    ramal: str | None = None,
    data_envio_email_conclusao: str | None = None,
    tipo_transacao: str | None = None,
    acao: str | None = None,
    planejamento: str | None = None,
    grupo: str | None = None,
    equipe: EquipeInfraestruturaType = "Help-Desk - Aeroporto",
    tipo: TipoAtendimentoAvulsoInfraestruturaType = "Suporte",
    categoria: CategoriasInfraestruturaType = "AD - Suporte/Dúvidas/Outros",
    projeto: ProjetoType = "Operação Help Desk",
    os_interna: OsInternaSistemasType = "Sim",
    origem: OrigemAtendimentoAvulsoSistemasType = "E-mail",
    status: StatusOsType = "Em Atendimento",
    prioridade_usuario: PrioridadeUsuarioOsType = "Nenhuma",
    criticidade: CriticidadeOsType = "Nenhuma",
) -> str:
    if data_solicitacao:
        data_solicitacao = converter_data_siga(data_solicitacao, manter_horas=True)

    if data_inicio_previsto:
        data_inicio_previsto = converter_data_siga(
            data_inicio_previsto, manter_horas=True
        )

    if data_limite:
        data_limite = converter_data_siga(data_limite, manter_horas=True)

    if data_previsao_entrega:
        data_previsao_entrega = converter_data_siga(
            data_previsao_entrega, manter_horas=True
        )

    if data_envio_email_conclusao:
        data_envio_email_conclusao = converter_data_siga(
            data_envio_email_conclusao, manter_horas=True
        )

    # VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
    # Validar matSolicitante
    if (
        not matSolicitante
        or matSolicitante == "0"
        or (matSolicitante != "CURRENT_USER" and not matSolicitante.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "mat_solicitante_obrigatorio",
                    "campo_invalido": "matSolicitante",
                    "valor_informado": str(matSolicitante),
                    "mensagem": f"Campo 'matSolicitante' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {matSolicitante}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar criada_por
    if (
        not criada_por
        or criada_por == "0"
        or (criada_por != "CURRENT_USER" and not criada_por.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criada_por_obrigatorio",
                    "campo_invalido": "criada_por",
                    "valor_informado": str(criada_por),
                    "mensagem": f"Campo 'criada_por' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {criada_por}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # VALIDAÇÃO DE USUÁRIOS RESPONSÁVEIS
    # Validar responsavel (se não for CURRENT_USER)
    if responsavel != "CURRENT_USER" and responsavel not in USUARIOS_INFRAESTRUTURA_IDS:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_invalido",
                    "responsavel_informado": responsavel,
                    "mensagem": f"Responsável '{responsavel}' não encontrado na lista de usuários válidos para Infraestrutura",
                    "usuarios_validos": USUARIOS_INFRAESTRUTURA_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar responsavel_atual (se não for CURRENT_USER)
    if (
        responsavel_atual != "CURRENT_USER"
        and responsavel_atual not in USUARIOS_INFRAESTRUTURA_IDS
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_atual_invalido",
                    "responsavel_atual_informado": responsavel_atual,
                    "mensagem": f"Responsável atual '{responsavel_atual}' não encontrado na lista de usuários válidos para Infraestrutura",
                    "usuarios_validos": USUARIOS_INFRAESTRUTURA_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Busca o tipo correto na constante TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA ignorando maiúsculas/minúsculas
    tipo_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA
        (
            key
            for key in TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA.keys()
            # Compara a chave atual em minúsculas com o tipo recebido em minúsculas
            if str(key).lower() == str(tipo).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um tipo válido após a busca case-insensitive
    if tipo_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "tipo_invalido",
                    "tipo_informado": tipo,
                    "mensagem": f"Tipo '{tipo}' não encontrado na constante TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA",
                    "tipos_validos": list(
                        TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA.keys()
                    ),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    tipo_final = TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA[tipo_normalizado]

    # Busca a categoria correta na constante CATEGORIA_TO_NUMBER ignorando maiúsculas/minúsculas
    categoria_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário CATEGORIA_TO_NUMBER
        (
            key
            for key in CATEGORIA_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a categoria recebida em minúsculas
            if str(key).lower() == str(categoria).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma categoria válida após a busca case-insensitive
    if categoria_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "categoria_invalida",
                    "categoria_informada": categoria,
                    "mensagem": f"Categoria '{categoria}' não encontrada na constante CATEGORIA_TO_NUMBER",
                    "categorias_validas": list(CATEGORIA_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "inserir_os_infraestrutura",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    categoria_final = CATEGORIA_TO_NUMBER[categoria_normalizada]

    # Busca a equipe correta na constante EQUIPE_INFRAESTRUTURA_TO_NUMBER ignorando maiúsculas/minúsculas
    equipe_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário EQUIPE_INFRAESTRUTURA_TO_NUMBER
        (
            key
            for key in EQUIPE_INFRAESTRUTURA_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a equipe recebida em minúsculas
            if str(key).lower() == str(equipe).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma equipe válida após a busca case-insensitive
    if equipe_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "equipe_invalida",
                    "equipe_informada": equipe,
                    "mensagem": f"Equipe '{equipe}' não encontrada na constante EQUIPE_INFRAESTRUTURA_TO_NUMBER",
                    "equipes_validas": list(EQUIPE_INFRAESTRUTURA_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "inserir_os_infraestrutura",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    equipe_final = EQUIPE_INFRAESTRUTURA_TO_NUMBER[equipe_normalizada]

    # Busca o projeto correto na constante PROJETO_TO_NUMBER ignorando maiúsculas/minúsculas
    projeto_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PROJETO_TO_NUMBER
        (
            key
            for key in PROJETO_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o projeto recebido em minúsculas
            if str(key).lower() == str(projeto).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um projeto válido após a busca case-insensitive
    if projeto_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "projeto_invalido",
                    "projeto_informado": projeto,
                    "mensagem": f"Projeto '{projeto}' não encontrado na constante PROJETO_TO_NUMBER",
                    "projetos_validos": list(PROJETO_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "inserir_os_infraestrutura",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    projeto_final = PROJETO_TO_NUMBER[projeto_normalizado]

    # Busca o status correto na constante STATUS_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    status_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário STATUS_OS_TO_NUMBER
        (
            key
            for key in STATUS_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o status recebido em minúsculas
            if str(key).lower() == str(status).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um status válido após a busca case-insensitive
    if status_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "status_invalido",
                    "status_informado": status,
                    "mensagem": f"Status '{status}' não encontrado na constante STATUS_OS_TO_NUMBER",
                    "status_validos": list(STATUS_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    status_final = STATUS_OS_TO_NUMBER[status_normalizado]

    # Busca a origem correta na constante ORIGEM_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    origem_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário ORIGEM_OS_TO_NUMBER
        (
            key
            for key in ORIGEM_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a origem recebida em minúsculas
            if str(key).lower() == str(origem).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma origem válida após a busca case-insensitive
    if origem_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "origem_invalida",
                    "origem_informada": origem,
                    "mensagem": f"Origem '{origem}' não encontrada na constante ORIGEM_OS_TO_NUMBER",
                    "origens_validas": list(ORIGEM_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    origem_final = ORIGEM_OS_TO_NUMBER[origem_normalizada]

    # Busca o valor correto de OS interna na constante OS_INTERNA_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    os_interna_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário OS_INTERNA_OS_TO_NUMBER
        (
            key
            for key in OS_INTERNA_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o valor de os_interna recebido em minúsculas
            if str(key).lower() == str(os_interna).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um valor válido para OS interna após a busca case-insensitive
    if os_interna_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "os_interna_invalida",
                    "os_interna_informada": os_interna,
                    "mensagem": f"OS Interna '{os_interna}' não encontrada na constante OS_INTERNA_OS_TO_NUMBER",
                    "valores_validos": list(OS_INTERNA_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    os_interna_final = OS_INTERNA_OS_TO_NUMBER[os_interna_normalizada]

    # Busca a criticidade correta na constante CRITICIDADE_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    criticidade_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário CRITICIDADE_OS_TO_NUMBER
        (
            key
            for key in CRITICIDADE_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a criticidade recebida em minúsculas
            if str(key).lower() == str(criticidade).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma criticidade válida após a busca case-insensitive
    if criticidade_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criticidade_invalida",
                    "criticidade_informada": criticidade,
                    "mensagem": f"Criticidade '{criticidade}' não encontrada na constante CRITICIDADE_OS_TO_NUMBER",
                    "criticidades_validas": list(CRITICIDADE_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    criticidade_final = CRITICIDADE_OS_TO_NUMBER[criticidade_normalizada]

    # Busca a prioridade do usuário correta na constante PRIORIDADE_USUARIO_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    prioridade_usuario_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PRIORIDADE_USUARIO_OS_TO_NUMBER
        (
            key
            for key in PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a prioridade_usuario recebida em minúsculas
            if str(key).lower() == str(prioridade_usuario).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma prioridade do usuário válida após a busca case-insensitive
    if prioridade_usuario_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "prioridade_usuario_invalida",
                    "prioridade_usuario_informada": prioridade_usuario,
                    "mensagem": f"Prioridade do usuário '{prioridade_usuario}' não encontrada na constante PRIORIDADE_USUARIO_OS_TO_NUMBER",
                    "prioridades_validas": list(PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "inserir_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    prioridade_usuario_final = PRIORIDADE_USUARIO_OS_TO_NUMBER[
        prioridade_usuario_normalizada
    ]

    try:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                "https://ava3.uniube.br/ava/api/os/inserirOsSigaIA/",
                json={
                    "apiKey": getenv("AVA_API_KEY"),
                    "dtSolicitacao": data_solicitacao,
                    "assunto": assunto,
                    "descricao": descricao,
                    "matSolicitante": matSolicitante,
                    "nmSolicitante": "",
                    "centroCusto": "",
                    "setor": "",
                    "origem": origem_final,
                    "tipo": tipo_final,
                    "status": status_final,
                    "equipe": equipe_final,
                    "responsavel": responsavel,
                    "responsavelAtual": responsavel_atual,
                    "matGestor": "",
                    "criadaPor": criada_por,
                    "classe": 2,
                    "osInterna": os_interna_final,
                    "campus": "",
                    "sistema": "",
                    "linguagem": "",
                    "categoria": categoria_final or "",
                    "projeto": projeto_final or "",
                    "prioridade": prioridade or "",
                    "tempo_previsto": tempo_previsto or "",
                    "dtInicioPrevisto": data_inicio_previsto or "",
                    "dtLimite": data_limite or "",
                    "sprint": sprint or "",
                    "dtConclusao": "",
                    "osPredecessora": os_predecessora or "",
                    "chamadoFornecedor": chamado_fornecedor or "",
                    "osPrincipal": os_principal or "",
                    "rotinas": rotinas or "",
                    "plaqueta": plaqueta or "",
                    "classificacao": classificacao or "",
                    "criticidade": criticidade_final or "",
                    "nova": nova or "",
                    "dtPrevisaoEntrega": data_previsao_entrega or "",
                    "prioridadeUsuario": prioridade_usuario_final or "",
                    "modulo": modulo or "",
                    "tempoRestante": tempo_restante or "",
                    "ramal": ramal or "",
                    "dtEnvioEmailConclusao": data_envio_email_conclusao or "",
                    "tipoTransacao": tipo_transacao or "",
                    "acao": acao or "",
                    "planejamento": planejamento or "",
                    "grupo": grupo or "",
                },
            ) as response:
                json_response = await response.json(content_type=None)
                result_data = json_response.get("result")

                # Trata a resposta
                if result_data is None:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Não foi possível salvar a OS. Verifique as informações digitadas.",
                        }
                    ]
                elif result_data == 1:
                    data_final = [
                        {
                            "status": "sucesso",
                            "mensagem": "OS cadastrado com sucesso!",
                        }
                    ]
                else:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Erro ao gravar a OS. Tente novamente.",
                        }
                    ]

                # Adiciona os root_attributes
                return XMLBuilder().build_xml(
                    data=data_final,
                    root_element_name="ordens_servico",
                    item_element_name="ordem_servico",
                    root_attributes={
                        "dtSolicitacao": str(data_solicitacao),
                        "assunto": str(assunto),
                        "descricao": str(descricao),
                        "matSolicitante": str(matSolicitante),
                        "origem": str(origem_final),
                        "tipo": str(tipo_final),
                        "status": str(status_final),
                        "equipe": str(equipe_final),
                        "responsavel": str(responsavel),
                        "responsavelAtual": str(responsavel_atual),
                        "criadaPor": str(criada_por),
                        "osInterna": str(os_interna_final),
                        "categoria": str(categoria_final),
                        "projeto": str(projeto_final),
                        "prioridade": str(prioridade),
                        "tempo_previsto": str(tempo_previsto),
                        "dtInicioPrevisto": str(data_inicio_previsto),
                        "dtLimite": str(data_limite),
                        "sprint": str(sprint),
                        "osPredecessora": str(os_predecessora),
                        "chamadoFornecedor": str(chamado_fornecedor),
                        "osPrincipal": str(os_principal),
                        "rotinas": str(rotinas),
                        "classificacao": str(classificacao),
                        "criticidade": str(criticidade_final),
                        "nova": str(nova),
                        "dtPrevisaoEntrega": str(data_previsao_entrega),
                        "prioridadeUsuario": str(prioridade_usuario_final),
                        "modulo": str(modulo),
                        "tempoRestante": str(tempo_restante),
                        "ramal": str(ramal),
                        "dtEnvioEmailConclusao": str(data_envio_email_conclusao),
                        "tipoTransacao": str(tipo_transacao),
                        "acao": str(acao),
                        "planejamento": str(planejamento),
                        "grupo": str(grupo),
                    },
                    custom_attributes={"sistema": "SIGA"},
                )

    except Exception as e:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "mensagem": f"Erro interno: {str(e)}. Tente novamente mais tarde.",
                }
            ],
            root_element_name="resultado",
            item_element_name="item",
            custom_attributes={"sistema": "SIGA"},
        )


async def buscar_informacoes_os(
    codigo_os: str | int,
) -> str:
    try:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                "https://ava3.uniube.br/ava/api/os/buscarInfoOsSigaIA/",
                json={
                    "apiKey": getenv("AVA_API_KEY"),
                    "codOs": codigo_os,
                },
            ) as response:
                json_response = await response.json(content_type=None)
                result_data = json_response.get("result")

                # Trata a resposta
                if result_data is None:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Não foi possível buscar as informações da OS. Verifique o código informado.",
                        }
                    ]
                elif result_data and len(result_data) > 0:
                    # Sucesso - retorna os dados da OS diretamente
                    return XMLBuilder().build_xml(
                        data=result_data,
                        root_element_name="info_os",
                        item_element_name="os",
                        root_attributes={
                            "codOs": str(codigo_os),
                        },
                        custom_attributes={"sistema": "SIGA"},
                    )
                else:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": f"OS com código '{codigo_os}' não foi encontrada no sistema.",
                        }
                    ]

                # Retorna erro estruturado
                return XMLBuilder().build_xml(
                    data=data_final,
                    root_element_name="info_os",
                    item_element_name="resultado",
                    root_attributes={
                        "codOs": str(codigo_os),
                    },
                    custom_attributes={"sistema": "SIGA"},
                )

    except Exception as e:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "mensagem": f"Erro interno: {str(e)}. Tente novamente mais tarde.",
                }
            ],
            root_element_name="resultado",
            item_element_name="item",
            custom_attributes={"sistema": "SIGA"},
        )


@controlar_acesso_matricula
async def editar_os_sistemas(
    codigo_os: str | int,
    data_solicitacao: str,
    assunto: str,
    descricao: str,
    responsavel: str | Literal["CURRENT_USER"],
    responsavel_atual: str | Literal["CURRENT_USER"],
    matSolicitante: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    criada_por: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    prioridade: str | None = None,
    tempo_previsto: int | None = None,
    data_inicio_previsto: str | None = None,
    data_limite: str | None = None,
    sprint: str | None = None,
    os_predecessora: str | None = None,
    chamado_fornecedor: str | None = None,
    os_principal: str | None = None,
    rotinas: str | None = None,
    classificacao: str | None = None,
    nova: str | None = None,
    data_previsao_entrega: str | None = None,
    modulo: str | None = None,
    tempo_restante: str | None = None,
    ramal: str | None = None,
    data_envio_email_conclusao: str | None = None,
    tipo_transacao: str | None = None,
    acao: str | None = None,
    planejamento: str | None = None,
    grupo: str | None = None,
    sistema: SistemasType = "Sistemas AVA",
    tipo: TipoOsSistemasType = "Implementação",
    equipe: EquipeSistemasType = "Equipe AVA",
    linguagem: LinguagemOsSistemasType = "PHP",
    projeto: ProjetoType = "Operação AVA",
    status: StatusOsType = "Em Atendimento",
    os_interna: OsInternaSistemasType = "Sim",
    origem: OrigemOsSistemasType = "Teams",
    prioridade_usuario: PrioridadeUsuarioOsType = "Nenhuma",
    criticidade: CriticidadeOsType = "Nenhuma",
) -> str:
    if data_solicitacao:
        data_solicitacao = converter_data_siga(data_solicitacao, manter_horas=True)

    if data_inicio_previsto:
        data_inicio_previsto = converter_data_siga(
            data_inicio_previsto, manter_horas=True
        )

    if data_limite:
        data_limite = converter_data_siga(data_limite, manter_horas=True)

    if data_previsao_entrega:
        data_previsao_entrega = converter_data_siga(
            data_previsao_entrega, manter_horas=True
        )

    if data_envio_email_conclusao:
        data_envio_email_conclusao = converter_data_siga(
            data_envio_email_conclusao, manter_horas=True
        )

    # VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
    # Validar matSolicitante
    if (
        not matSolicitante
        or matSolicitante == "0"
        or (matSolicitante != "CURRENT_USER" and not matSolicitante.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "mat_solicitante_obrigatorio",
                    "campo_invalido": "matSolicitante",
                    "valor_informado": str(matSolicitante),
                    "mensagem": f"Campo 'matSolicitante' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {matSolicitante}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar criada_por
    if (
        not criada_por
        or criada_por == "0"
        or (criada_por != "CURRENT_USER" and not criada_por.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criada_por_obrigatorio",
                    "campo_invalido": "criada_por",
                    "valor_informado": str(criada_por),
                    "mensagem": f"Campo 'criada_por' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {criada_por}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # VALIDAÇÃO DE USUÁRIOS RESPONSÁVEIS
    # Validar responsavel (se não for CURRENT_USER)
    if responsavel != "CURRENT_USER" and responsavel not in USUARIOS_SISTEMAS_IDS:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_invalido",
                    "responsavel_informado": responsavel,
                    "mensagem": f"Responsável '{responsavel}' não encontrado na lista de usuários válidos para Sistemas",
                    "usuarios_validos": USUARIOS_SISTEMAS_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar responsavel_atual (se não for CURRENT_USER)
    if (
        responsavel_atual != "CURRENT_USER"
        and responsavel_atual not in USUARIOS_SISTEMAS_IDS
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_atual_invalido",
                    "responsavel_atual_informado": responsavel_atual,
                    "mensagem": f"Responsável atual '{responsavel_atual}' não encontrado na lista de usuários válidos para Sistemas",
                    "usuarios_validos": USUARIOS_SISTEMAS_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Busca o tipo correto na constante TIPO_TO_NUMBER_OS_SISTEMAS ignorando maiúsculas/minúsculas
    tipo_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário TIPO_TO_NUMBER_OS_SISTEMAS
        (
            key
            for key in TIPO_TO_NUMBER_OS_SISTEMAS.keys()
            # Compara a chave atual em minúsculas com o tipo recebido em minúsculas
            if str(key).lower() == str(tipo).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um tipo válido após a busca case-insensitive
    if tipo_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "tipo_invalido",
                    "tipo_informado": tipo,
                    "mensagem": f"Tipo '{tipo}' não encontrado na constante TIPO_TO_NUMBER_OS_SISTEMAS",
                    "tipos_validos": list(TIPO_TO_NUMBER_OS_SISTEMAS.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    tipo_final = TIPO_TO_NUMBER_OS_SISTEMAS[tipo_normalizado]

    # Busca o sistema correto na constante SISTEMA_TO_NUMBER ignorando maiúsculas/minúsculas
    sistema_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário SISTEMA_TO_NUMBER
        (
            key
            for key in SISTEMA_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o sistema recebido em minúsculas
            if str(key).lower() == str(sistema).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um sistema válido após a busca case-insensitive
    if sistema_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "sistema_invalido",
                    "sistema_informado": sistema,
                    "mensagem": f"Sistema '{sistema}' não encontrado na constante SISTEMA_TO_NUMBER",
                    "sistemas_validos": list(SISTEMA_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "editar_os_sistemas",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    sistema_final = SISTEMA_TO_NUMBER[sistema_normalizado]

    # Busca a equipe correta na constante EQUIPE_TO_NUMBER ignorando maiúsculas/minúsculas
    equipe_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário EQUIPE_TO_NUMBER
        (
            key
            for key in EQUIPE_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a equipe recebida em minúsculas
            if str(key).lower() == str(equipe).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma equipe válida após a busca case-insensitive
    if equipe_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "equipe_invalida",
                    "equipe_informada": equipe,
                    "mensagem": f"Equipe '{equipe}' não encontrada na constante EQUIPE_TO_NUMBER",
                    "equipes_validas": list(EQUIPE_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "editar_os_sistemas",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    equipe_final = EQUIPE_TO_NUMBER[equipe_normalizada]

    # Busca o projeto correto na constante PROJETO_TO_NUMBER ignorando maiúsculas/minúsculas
    projeto_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PROJETO_TO_NUMBER
        (
            key
            for key in PROJETO_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o projeto recebido em minúsculas
            if str(key).lower() == str(projeto).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um projeto válido após a busca case-insensitive
    if projeto_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "projeto_invalido",
                    "projeto_informado": projeto,
                    "mensagem": f"Projeto '{projeto}' não encontrado na constante PROJETO_TO_NUMBER",
                    "projetos_validos": list(PROJETO_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "editar_os_sistemas",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    projeto_final = PROJETO_TO_NUMBER[projeto_normalizado]

    # Busca a linguagem correta na constante LINGUAGEM_TO_NUMBER_OS_SISTEMAS ignorando maiúsculas/minúsculas
    linguagem_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário LINGUAGEM_TO_NUMBER_OS_SISTEMAS
        (
            key
            for key in LINGUAGEM_TO_NUMBER_OS_SISTEMAS.keys()
            # Compara a chave atual em minúsculas com a linguagem recebida em minúsculas
            if str(key).lower() == str(linguagem).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma linguagem válida após a busca case-insensitive
    if linguagem_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "linguagem_invalida",
                    "linguagem_informada": linguagem,
                    "mensagem": f"Linguagem '{linguagem}' não encontrada na constante LINGUAGEM_TO_NUMBER_OS_SISTEMAS",
                    "linguagens_validas": list(LINGUAGEM_TO_NUMBER_OS_SISTEMAS.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    linguagem_final = LINGUAGEM_TO_NUMBER_OS_SISTEMAS[linguagem_normalizada]

    # Busca o status correto na constante STATUS_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    status_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário STATUS_OS_TO_NUMBER
        (
            key
            for key in STATUS_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o status recebido em minúsculas
            if str(key).lower() == str(status).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um status válido após a busca case-insensitive
    if status_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "status_invalido",
                    "status_informado": status,
                    "mensagem": f"Status '{status}' não encontrado na constante STATUS_OS_TO_NUMBER",
                    "status_validos": list(STATUS_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    status_final = STATUS_OS_TO_NUMBER[status_normalizado]

    # Busca a origem correta na constante ORIGEM_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    origem_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário ORIGEM_OS_TO_NUMBER
        (
            key
            for key in ORIGEM_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a origem recebida em minúsculas
            if str(key).lower() == str(origem).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma origem válida após a busca case-insensitive
    if origem_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "origem_invalida",
                    "origem_informada": origem,
                    "mensagem": f"Origem '{origem}' não encontrada na constante ORIGEM_OS_TO_NUMBER",
                    "origens_validas": list(ORIGEM_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    origem_final = ORIGEM_OS_TO_NUMBER[origem_normalizada]

    # Busca o valor correto de OS interna na constante OS_INTERNA_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    os_interna_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário OS_INTERNA_OS_TO_NUMBER
        (
            key
            for key in OS_INTERNA_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o valor de os_interna recebido em minúsculas
            if str(key).lower() == str(os_interna).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um valor válido para OS interna após a busca case-insensitive
    if os_interna_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "os_interna_invalida",
                    "os_interna_informada": os_interna,
                    "mensagem": f"OS Interna '{os_interna}' não encontrada na constante OS_INTERNA_OS_TO_NUMBER",
                    "valores_validos": list(OS_INTERNA_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    os_interna_final = OS_INTERNA_OS_TO_NUMBER[os_interna_normalizada]

    # Busca a criticidade correta na constante CRITICIDADE_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    criticidade_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário CRITICIDADE_OS_TO_NUMBER
        (
            key
            for key in CRITICIDADE_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a criticidade recebida em minúsculas
            if str(key).lower() == str(criticidade).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma criticidade válida após a busca case-insensitive
    if criticidade_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criticidade_invalida",
                    "criticidade_informada": criticidade,
                    "mensagem": f"Criticidade '{criticidade}' não encontrada na constante CRITICIDADE_OS_TO_NUMBER",
                    "criticidades_validas": list(CRITICIDADE_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    criticidade_final = CRITICIDADE_OS_TO_NUMBER[criticidade_normalizada]

    # Busca a prioridade do usuário correta na constante PRIORIDADE_USUARIO_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    prioridade_usuario_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PRIORIDADE_USUARIO_OS_TO_NUMBER
        (
            key
            for key in PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a prioridade_usuario recebida em minúsculas
            if str(key).lower() == str(prioridade_usuario).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma prioridade do usuário válida após a busca case-insensitive
    if prioridade_usuario_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "prioridade_usuario_invalida",
                    "prioridade_usuario_informada": prioridade_usuario,
                    "mensagem": f"Prioridade do usuário '{prioridade_usuario}' não encontrada na constante PRIORIDADE_USUARIO_OS_TO_NUMBER",
                    "prioridades_validas": list(PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_sistemas"},
            custom_attributes={"sistema": "SIGA"},
        )

    prioridade_usuario_final = PRIORIDADE_USUARIO_OS_TO_NUMBER[
        prioridade_usuario_normalizada
    ]

    try:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                "https://ava3.uniube.br/ava/api/os/updateOsSigaIA/",
                json={
                    "apiKey": getenv("AVA_API_KEY"),
                    "numeroOS": codigo_os,
                    "dtSolicitacao": data_solicitacao,
                    "assunto": assunto,
                    "descricao": descricao,
                    "matSolicitante": matSolicitante,
                    "nmSolicitante": "",
                    "centroCusto": "",
                    "setor": "",
                    "origem": origem_final,
                    "tipo": tipo_final,
                    "status": status_final,
                    "equipe": equipe_final,
                    "responsavel": responsavel,
                    "responsavelAtual": responsavel_atual,
                    "matGestor": "",
                    "criadaPor": criada_por,
                    "area": 1,
                    "osInterna": os_interna_final,
                    "campus": "",
                    "sistema": sistema_final or "",
                    "linguagem": linguagem_final or "",
                    "categoria": "",
                    "projeto": projeto_final or "",
                    "prioridade": prioridade or "",
                    "tempo_previsto": tempo_previsto or "",
                    "dtInicioPrevisto": data_inicio_previsto or "",
                    "dtLimite": data_limite or "",
                    "sprint": sprint or "",
                    "dtConclusao": "",
                    "osPredecessora": os_predecessora or "",
                    "chamadoFornecedor": chamado_fornecedor or "",
                    "osPrincipal": os_principal or "",
                    "rotinas": rotinas or "",
                    "plaqueta": "",
                    "classificacao": classificacao or "",
                    "criticidade": criticidade_final or "",
                    "nova": nova or "",
                    "dtPrevisaoEntrega": data_previsao_entrega or "",
                    "prioridadeUsuario": prioridade_usuario_final or "",
                    "modulo": modulo or "",
                    "tempoRestante": tempo_restante or "",
                    "ramal": ramal or "",
                    "dtEnvioEmailConclusao": data_envio_email_conclusao or "",
                    "tipoTransacao": tipo_transacao or "",
                    "acao": acao or "",
                    "planejamento": planejamento or "",
                    "grupo": grupo or "",
                },
            ) as response:
                json_response = await response.json(content_type=None)
                result_data = json_response.get("result")

                # Trata a resposta
                if result_data is None:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Não foi possível editar a OS. Verifique as informações digitadas.",
                        }
                    ]
                elif result_data == 1:
                    data_final = [
                        {
                            "status": "sucesso",
                            "mensagem": "OS editada com sucesso!",
                        }
                    ]
                else:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Erro ao editar a OS. Tente novamente.",
                        }
                    ]

                # Adiciona os root_attributes
                return XMLBuilder().build_xml(
                    data=data_final,
                    root_element_name="ordens_servico",
                    item_element_name="ordem_servico",
                    root_attributes={
                        "numeroOS": str(codigo_os),
                        "dtSolicitacao": str(data_solicitacao),
                        "assunto": str(assunto),
                        "descricao": str(descricao),
                        "matSolicitante": str(matSolicitante),
                        "origem": str(origem_final),
                        "tipo": str(tipo_final),
                        "status": str(status_final),
                        "equipe": str(equipe_final),
                        "responsavel": str(responsavel),
                        "responsavelAtual": str(responsavel_atual),
                        "criadaPor": str(criada_por),
                        "osInterna": str(os_interna_final),
                        "sistema": str(sistema_final),
                        "linguagem": str(linguagem_final),
                        "projeto": str(projeto_final),
                        "prioridade": str(prioridade),
                        "tempo_previsto": str(tempo_previsto),
                        "dtInicioPrevisto": str(data_inicio_previsto),
                        "dtLimite": str(data_limite),
                        "sprint": str(sprint),
                        "osPredecessora": str(os_predecessora),
                        "chamadoFornecedor": str(chamado_fornecedor),
                        "osPrincipal": str(os_principal),
                        "rotinas": str(rotinas),
                        "classificacao": str(classificacao),
                        "criticidade": str(criticidade_final),
                        "nova": str(nova),
                        "dtPrevisaoEntrega": str(data_previsao_entrega),
                        "prioridadeUsuario": str(prioridade_usuario_final),
                        "modulo": str(modulo),
                        "tempoRestante": str(tempo_restante),
                        "ramal": str(ramal),
                        "dtEnvioEmailConclusao": str(data_envio_email_conclusao),
                        "tipoTransacao": str(tipo_transacao),
                        "acao": str(acao),
                        "planejamento": str(planejamento),
                        "grupo": str(grupo),
                    },
                    custom_attributes={"sistema": "SIGA"},
                )

    except Exception as e:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "mensagem": f"Erro interno: {str(e)}. Tente novamente mais tarde.",
                }
            ],
            root_element_name="resultado",
            item_element_name="item",
            custom_attributes={"sistema": "SIGA"},
        )


@controlar_acesso_matricula
async def editar_os_infraestrutura(
    codigo_os: str | int,
    data_solicitacao: str,
    assunto: str,
    descricao: str,
    responsavel: str | Literal["CURRENT_USER"],
    responsavel_atual: str | Literal["CURRENT_USER"],
    matSolicitante: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    criada_por: str | Literal["CURRENT_USER"] = "CURRENT_USER",
    prioridade: str | None = None,
    tempo_previsto: int | None = None,
    data_inicio_previsto: str | None = None,
    data_limite: str | None = None,
    sprint: str | None = None,
    os_predecessora: str | None = None,
    chamado_fornecedor: str | None = None,
    os_principal: str | None = None,
    rotinas: str | None = None,
    classificacao: str | None = None,
    nova: str | None = None,
    data_previsao_entrega: str | None = None,
    modulo: str | None = None,
    tempo_restante: str | None = None,
    ramal: str | None = None,
    data_envio_email_conclusao: str | None = None,
    tipo_transacao: str | None = None,
    acao: str | None = None,
    planejamento: str | None = None,
    grupo: str | None = None,
    plaqueta: str | None = None,
    categoria: CategoriasInfraestruturaType = "AD - Suporte/Dúvidas/Outros",
    tipo: TipoAtendimentoAvulsoInfraestruturaType = "Suporte",
    equipe: EquipeInfraestruturaType = "Help-Desk - Aeroporto",
    projeto: ProjetoType = "Operação Help Desk",
    status: StatusOsType = "Em Atendimento",
    os_interna: OsInternaSistemasType = "Sim",
    origem: OrigemOsSistemasType = "E-mail",
    prioridade_usuario: PrioridadeUsuarioOsType = "Nenhuma",
    criticidade: CriticidadeOsType = "Nenhuma",
) -> str:
    if data_solicitacao:
        data_solicitacao = converter_data_siga(data_solicitacao, manter_horas=True)

    if data_inicio_previsto:
        data_inicio_previsto = converter_data_siga(
            data_inicio_previsto, manter_horas=True
        )

    if data_limite:
        data_limite = converter_data_siga(data_limite, manter_horas=True)

    if data_previsao_entrega:
        data_previsao_entrega = converter_data_siga(
            data_previsao_entrega, manter_horas=True
        )

    if data_envio_email_conclusao:
        data_envio_email_conclusao = converter_data_siga(
            data_envio_email_conclusao, manter_horas=True
        )

    # VALIDAÇÃO DOS CAMPOS OBRIGATÓRIOS
    # Validar matSolicitante
    if (
        not matSolicitante
        or matSolicitante == "0"
        or (matSolicitante != "CURRENT_USER" and not matSolicitante.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "mat_solicitante_obrigatorio",
                    "campo_invalido": "matSolicitante",
                    "valor_informado": str(matSolicitante),
                    "mensagem": f"Campo 'matSolicitante' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {matSolicitante}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar criada_por
    if (
        not criada_por
        or criada_por == "0"
        or (criada_por != "CURRENT_USER" and not criada_por.isdigit())
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criada_por_obrigatorio",
                    "campo_invalido": "criada_por",
                    "valor_informado": str(criada_por),
                    "mensagem": f"Campo 'criada_por' é obrigatório e deve ser 'CURRENT_USER' ou um número válido maior que zero. Valor informado: {criada_por}",
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # VALIDAÇÃO DE USUÁRIOS RESPONSÁVEIS
    # Validar responsavel (se não for CURRENT_USER)
    if responsavel != "CURRENT_USER" and responsavel not in USUARIOS_INFRAESTRUTURA_IDS:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_invalido",
                    "responsavel_informado": responsavel,
                    "mensagem": f"Responsável '{responsavel}' não encontrado na lista de usuários válidos para infraestrutura",
                    "usuarios_validos": USUARIOS_INFRAESTRUTURA_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Validar responsavel_atual (se não for CURRENT_USER)
    if (
        responsavel_atual != "CURRENT_USER"
        and responsavel_atual not in USUARIOS_INFRAESTRUTURA_IDS
    ):
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "responsavel_atual_invalido",
                    "responsavel_atual_informado": responsavel_atual,
                    "mensagem": f"Responsável atual '{responsavel_atual}' não encontrado na lista de usuários válidos para infraestrutura",
                    "usuarios_validos": USUARIOS_INFRAESTRUTURA_PARA_ERRO,
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    # Busca o tipo correto na constante TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA ignorando maiúsculas/minúsculas
    tipo_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA
        (
            key
            for key in TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA.keys()
            # Compara a chave atual em minúsculas com o tipo recebido em minúsculas
            if str(key).lower() == str(tipo).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um tipo válido após a busca case-insensitive
    if tipo_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "tipo_invalido",
                    "tipo_informado": tipo,
                    "mensagem": f"Tipo '{tipo}' não encontrado na constante TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA",
                    "tipos_validos": list(
                        TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA.keys()
                    ),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    tipo_final = TIPO_TO_NUMBER_ATENDIMENTO_AVULSO_INFRAESTRUTURA[tipo_normalizado]

    # Busca a categoria correta na constante CATEGORIA_TO_NUMBER ignorando maiúsculas/minúsculas
    categoria_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário CATEGORIA_TO_NUMBER
        (
            key
            for key in CATEGORIA_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a categoria recebida em minúsculas
            if str(key).lower() == str(categoria).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado uma categoria válida após a busca case-insensitive
    if categoria_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "categoria_invalida",
                    "categoria_informada": categoria,
                    "mensagem": f"Categoria '{categoria}' não encontrada na constante CATEGORIA_TO_NUMBER",
                    "categorias_validas": list(CATEGORIA_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "editar_os_infraestrutura",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    categoria_final = CATEGORIA_TO_NUMBER[categoria_normalizada]

    # Busca a equipe correta na constante EQUIPE_INFRAESTRUTURA_TO_NUMBER ignorando maiúsculas/minúsculas
    equipe_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário EQUIPE_INFRAESTRUTURA_TO_NUMBER
        (
            key
            for key in EQUIPE_INFRAESTRUTURA_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a equipe recebida em minúsculas
            if str(key).lower() == str(equipe).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma equipe válida após a busca case-insensitive
    if equipe_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "equipe_invalida",
                    "equipe_informada": equipe,
                    "mensagem": f"Equipe '{equipe}' não encontrada na constante EQUIPE_INFRAESTRUTURA_TO_NUMBER",
                    "equipes_validas": list(EQUIPE_INFRAESTRUTURA_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "editar_os_infraestrutura",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    equipe_final = EQUIPE_INFRAESTRUTURA_TO_NUMBER[equipe_normalizada]

    # Busca o projeto correto na constante PROJETO_TO_NUMBER ignorando maiúsculas/minúsculas
    projeto_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PROJETO_TO_NUMBER
        (
            key
            for key in PROJETO_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o projeto recebido em minúsculas
            if str(key).lower() == str(projeto).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um projeto válido após a busca case-insensitive
    if projeto_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "projeto_invalido",
                    "projeto_informado": projeto,
                    "mensagem": f"Projeto '{projeto}' não encontrado na constante PROJETO_TO_NUMBER",
                    "projetos_validos": list(PROJETO_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={
                "sistema": "SIGA",
                "funcao": "editar_os_infraestrutura",
            },
            custom_attributes={"sistema": "SIGA"},
        )

    projeto_final = PROJETO_TO_NUMBER[projeto_normalizado]

    # Busca o status correto na constante STATUS_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    status_normalizado = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário STATUS_OS_TO_NUMBER
        (
            key
            for key in STATUS_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o status recebido em minúsculas
            if str(key).lower() == str(status).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um status válido após a busca case-insensitive
    if status_normalizado is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "status_invalido",
                    "status_informado": status,
                    "mensagem": f"Status '{status}' não encontrado na constante STATUS_OS_TO_NUMBER",
                    "status_validos": list(STATUS_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    status_final = STATUS_OS_TO_NUMBER[status_normalizado]

    # Busca a origem correta na constante ORIGEM_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    origem_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário ORIGEM_OS_TO_NUMBER
        (
            key
            for key in ORIGEM_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a origem recebida em minúsculas
            if str(key).lower() == str(origem).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma origem válida após a busca case-insensitive
    if origem_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "origem_invalida",
                    "origem_informada": origem,
                    "mensagem": f"Origem '{origem}' não encontrada na constante ORIGEM_OS_TO_NUMBER",
                    "origens_validas": list(ORIGEM_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    origem_final = ORIGEM_OS_TO_NUMBER[origem_normalizada]

    # Busca o valor correto de OS interna na constante OS_INTERNA_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    os_interna_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário OS_INTERNA_OS_TO_NUMBER
        (
            key
            for key in OS_INTERNA_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com o valor de os_interna recebido em minúsculas
            if str(key).lower() == str(os_interna).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrado um valor válido para OS interna após a busca case-insensitive
    if os_interna_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "os_interna_invalida",
                    "os_interna_informada": os_interna,
                    "mensagem": f"OS Interna '{os_interna}' não encontrada na constante OS_INTERNA_OS_TO_NUMBER",
                    "valores_validos": list(OS_INTERNA_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    os_interna_final = OS_INTERNA_OS_TO_NUMBER[os_interna_normalizada]

    # Busca a criticidade correta na constante CRITICIDADE_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    criticidade_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário CRITICIDADE_OS_TO_NUMBER
        (
            key
            for key in CRITICIDADE_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a criticidade recebida em minúsculas
            if str(key).lower() == str(criticidade).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma criticidade válida após a busca case-insensitive
    if criticidade_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "criticidade_invalida",
                    "criticidade_informada": criticidade,
                    "mensagem": f"Criticidade '{criticidade}' não encontrada na constante CRITICIDADE_OS_TO_NUMBER",
                    "criticidades_validas": list(CRITICIDADE_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    criticidade_final = CRITICIDADE_OS_TO_NUMBER[criticidade_normalizada]

    # Busca a prioridade do usuário correta na constante PRIORIDADE_USUARIO_OS_TO_NUMBER ignorando maiúsculas/minúsculas
    prioridade_usuario_normalizada = next(
        # Expressão geradora que itera sobre todas as chaves do dicionário PRIORIDADE_USUARIO_OS_TO_NUMBER
        (
            key
            for key in PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()
            # Compara a chave atual em minúsculas com a prioridade_usuario recebida em minúsculas
            if str(key).lower() == str(prioridade_usuario).lower()
        ),
        # Se nenhuma correspondência for encontrada, retorna None como valor padrão
        None,
    )

    # Verifica se foi encontrada uma prioridade do usuário válida após a busca case-insensitive
    if prioridade_usuario_normalizada is None:
        # Retorna XML de erro em vez de levantar exceção
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "tipo_erro": "prioridade_usuario_invalida",
                    "prioridade_usuario_informada": prioridade_usuario,
                    "mensagem": f"Prioridade do usuário '{prioridade_usuario}' não encontrada na constante PRIORIDADE_USUARIO_OS_TO_NUMBER",
                    "prioridades_validas": list(PRIORIDADE_USUARIO_OS_TO_NUMBER.keys()),
                }
            ],
            root_element_name="erro_validacao",
            item_element_name="erro",
            root_attributes={"sistema": "SIGA", "funcao": "editar_os_infraestrutura"},
            custom_attributes={"sistema": "SIGA"},
        )

    prioridade_usuario_final = PRIORIDADE_USUARIO_OS_TO_NUMBER[
        prioridade_usuario_normalizada
    ]

    try:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                "https://ava3.uniube.br/ava/api/os/updateOsSigaIA/",
                json={
                    "apiKey": getenv("AVA_API_KEY"),
                    "numeroOS": codigo_os,
                    "dtSolicitacao": data_solicitacao,
                    "assunto": assunto,
                    "descricao": descricao,
                    "matSolicitante": matSolicitante,
                    "nmSolicitante": "",
                    "centroCusto": "",
                    "setor": "",
                    "origem": origem_final,
                    "tipo": tipo_final,
                    "status": status_final,
                    "equipe": equipe_final,
                    "responsavel": responsavel,
                    "responsavelAtual": responsavel_atual,
                    "matGestor": "",
                    "criadaPor": criada_por,
                    "area": 2,
                    "osInterna": os_interna_final,
                    "campus": "",
                    "sistema": "",
                    "linguagem": "",
                    "categoria": categoria_final or "",
                    "projeto": projeto_final or "",
                    "prioridade": prioridade or "",
                    "tempo_previsto": tempo_previsto or "",
                    "dtInicioPrevisto": data_inicio_previsto or "",
                    "dtLimite": data_limite or "",
                    "sprint": sprint or "",
                    "dtConclusao": "",
                    "osPredecessora": os_predecessora or "",
                    "chamadoFornecedor": chamado_fornecedor or "",
                    "osPrincipal": os_principal or "",
                    "rotinas": rotinas or "",
                    "plaqueta": plaqueta or "",
                    "classificacao": classificacao or "",
                    "criticidade": criticidade_final or "",
                    "nova": nova or "",
                    "dtPrevisaoEntrega": data_previsao_entrega or "",
                    "prioridadeUsuario": prioridade_usuario_final or "",
                    "modulo": modulo or "",
                    "tempoRestante": tempo_restante or "",
                    "ramal": ramal or "",
                    "dtEnvioEmailConclusao": data_envio_email_conclusao or "",
                    "tipoTransacao": tipo_transacao or "",
                    "acao": acao or "",
                    "planejamento": planejamento or "",
                    "grupo": grupo or "",
                },
            ) as response:
                json_response = await response.json(content_type=None)
                result_data = json_response.get("result")

                # Trata a resposta
                if result_data is None:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Não foi possível editar a OS. Verifique as informações digitadas.",
                        }
                    ]
                elif result_data == 1:
                    data_final = [
                        {
                            "status": "sucesso",
                            "mensagem": "OS editada com sucesso!",
                        }
                    ]
                else:
                    data_final = [
                        {
                            "status": "erro",
                            "mensagem": "Erro ao editar a OS. Tente novamente.",
                        }
                    ]

                # Adiciona os root_attributes
                return XMLBuilder().build_xml(
                    data=data_final,
                    root_element_name="ordens_servico",
                    item_element_name="ordem_servico",
                    root_attributes={
                        "numeroOS": str(codigo_os),
                        "dtSolicitacao": str(data_solicitacao),
                        "assunto": str(assunto),
                        "descricao": str(descricao),
                        "matSolicitante": str(matSolicitante),
                        "origem": str(origem_final),
                        "tipo": str(tipo_final),
                        "status": str(status_final),
                        "equipe": str(equipe_final),
                        "responsavel": str(responsavel),
                        "responsavelAtual": str(responsavel_atual),
                        "criadaPor": str(criada_por),
                        "osInterna": str(os_interna_final),
                        "categoria": str(categoria_final),
                        "projeto": str(projeto_final),
                        "prioridade": str(prioridade),
                        "tempo_previsto": str(tempo_previsto),
                        "dtInicioPrevisto": str(data_inicio_previsto),
                        "dtLimite": str(data_limite),
                        "sprint": str(sprint),
                        "osPredecessora": str(os_predecessora),
                        "chamadoFornecedor": str(chamado_fornecedor),
                        "osPrincipal": str(os_principal),
                        "rotinas": str(rotinas),
                        "plaqueta": str(plaqueta),
                        "classificacao": str(classificacao),
                        "criticidade": str(criticidade_final),
                        "nova": str(nova),
                        "dtPrevisaoEntrega": str(data_previsao_entrega),
                        "prioridadeUsuario": str(prioridade_usuario_final),
                        "modulo": str(modulo),
                        "tempoRestante": str(tempo_restante),
                        "ramal": str(ramal),
                        "dtEnvioEmailConclusao": str(data_envio_email_conclusao),
                        "tipoTransacao": str(tipo_transacao),
                        "acao": str(acao),
                        "planejamento": str(planejamento),
                        "grupo": str(grupo),
                    },
                    custom_attributes={"sistema": "SIGA"},
                )

    except Exception as e:
        return XMLBuilder().build_xml(
            data=[
                {
                    "status": "erro",
                    "mensagem": f"Erro interno: {str(e)}. Tente novamente mais tarde.",
                }
            ],
            root_element_name="resultado",
            item_element_name="item",
            custom_attributes={"sistema": "SIGA"},
        )
