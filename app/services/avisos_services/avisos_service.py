from __future__ import annotations

from typing import Dict, List

from app import db
from app.models.avisos_models.aviso import Aviso
from app.models.avisos_models.aviso_destinatario import AvisoDestinatario
from app.models.avisos_models.aviso_evento import AvisoEvento
from .avisos_query_service import listar_avisos_capacidade


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _upsert_avisos_automaticos
# [RESPONSABILIDADE] Sincronizar avisos calculados com a tabela persistida
# ====================================================================
def _upsert_avisos_automaticos(avisos_calculados: List[Dict]) -> None:
    codigos_calculados = {a["codigo"] for a in avisos_calculados}

    avisos_existentes = Aviso.query.filter(Aviso.tipo == "capacidade").all()
    mapa_existentes = {a.codigo: a for a in avisos_existentes}

    for payload in avisos_calculados:
        aviso = mapa_existentes.get(payload["codigo"])

        if not aviso:
            aviso = Aviso(
                codigo=payload["codigo"],
                ocorrencia_codigo=_gerar_ocorrencia_codigo(payload.get("data_aviso")),
                tipo="capacidade",
                titulo=payload["titulo"],
                descricao=payload["descricao"],
                severidade=payload["severidade"],
                status="novo",
                modelo=payload["modelo"],
                origem=payload["origem"],
                data_aviso=payload["data_aviso"],
                capacidade_atual=payload["capacidade_atual"],
                estoque_maximo=payload["estoque_maximo"],
            )
            db.session.add(aviso)
            continue

        if not aviso.ocorrencia_codigo:
            aviso.ocorrencia_codigo = _gerar_ocorrencia_codigo(
                aviso.data_aviso or payload.get("data_aviso")
            )

        if aviso.status == "resolvido":
            aviso.status = "novo"
            aviso.resolvido_por_user_id = None
            aviso.resolvido_por_nome = None
            aviso.resolvido_em = None

        aviso.titulo = payload["titulo"]
        aviso.descricao = payload["descricao"]
        aviso.severidade = payload["severidade"]
        aviso.modelo = payload["modelo"]
        aviso.origem = payload["origem"]
        aviso.capacidade_atual = payload["capacidade_atual"]
        aviso.estoque_maximo = payload["estoque_maximo"]

    for aviso in avisos_existentes:
        if aviso.codigo not in codigos_calculados and aviso.status != "resolvido":
            aviso.status = "resolvido"

    db.session.commit()


# ====================================================================
# [FIM BLOCO] _upsert_avisos_automaticos
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _upsert_avisos_automaticos
# [RESPONSABILIDADE] Sincronizar avisos calculados com a tabela persistida
# ====================================================================
def _upsert_avisos_automaticos(avisos_calculados: List[Dict]) -> None:
    codigos_calculados = {a["codigo"] for a in avisos_calculados}

    avisos_existentes = Aviso.query.filter(Aviso.tipo == "capacidade").all()
    mapa_existentes = {a.codigo: a for a in avisos_existentes}

    for payload in avisos_calculados:
        aviso = mapa_existentes.get(payload["codigo"])

        if not aviso:
            aviso = Aviso(
                codigo=payload["codigo"],
                tipo="capacidade",
                titulo=payload["titulo"],
                descricao=payload["descricao"],
                severidade=payload["severidade"],
                status="novo",
                modelo=payload["modelo"],
                origem=payload["origem"],
                data_aviso=payload["data_aviso"],
                capacidade_atual=payload["capacidade_atual"],
                estoque_maximo=payload["estoque_maximo"],
            )
            db.session.add(aviso)
            continue

        if aviso.status == "resolvido":
            aviso.status = "novo"
            aviso.resolvido_por_user_id = None
            aviso.resolvido_por_nome = None
            aviso.resolvido_em = None

        aviso.titulo = payload["titulo"]
        aviso.descricao = payload["descricao"]
        aviso.severidade = payload["severidade"]
        aviso.modelo = payload["modelo"]
        aviso.origem = payload["origem"]
        aviso.capacidade_atual = payload["capacidade_atual"]
        aviso.estoque_maximo = payload["estoque_maximo"]

    for aviso in avisos_existentes:
        if aviso.codigo not in codigos_calculados and aviso.status != "resolvido":
            aviso.status = "resolvido"

    db.session.commit()


# ====================================================================
# [FIM BLOCO] _upsert_avisos_automaticos
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _montar_historico_aviso
# [RESPONSABILIDADE] Transformar eventos persistidos em linhas de histórico para o template
# ====================================================================
def _montar_historico_aviso(aviso: Aviso) -> List[str]:
    linhas: List[str] = []

    eventos = (
        aviso.eventos.order_by(AvisoEvento.created_at.desc()).all()
        if hasattr(aviso.eventos, "order_by")
        else []
    )

    for evento in eventos:
        data_txt = (
            evento.created_at.strftime("%d/%m/%Y %H:%M") if evento.created_at else "—"
        )

        if evento.tipo_evento == "lido":
            linhas.append(f"Lido por: {evento.usuario_nome or '—'} às {data_txt}.")
        elif evento.tipo_evento == "comunicado":
            linhas.append(
                f"Comunicado por: {evento.usuario_nome or '—'} às {data_txt} ao {evento.destino or 'setor não informado'}."
            )
        else:
            linhas.append(
                f"{evento.tipo_evento}: {evento.usuario_nome or '—'} às {data_txt}."
            )

    return linhas


# ====================================================================
# [FIM BLOCO] _montar_historico_aviso
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] _montar_payload_aviso
# [RESPONSABILIDADE] Converter Aviso persistido em payload pronto para a tela
# ====================================================================
def _montar_payload_aviso(aviso: Aviso, pecas_criticas: List[Dict]) -> Dict:
    return {
        "codigo": aviso.codigo,
        "ocorrencia_codigo": aviso.ocorrencia_codigo,
        "severidade": aviso.severidade,
        "titulo": aviso.titulo,
        "descricao": aviso.descricao,
        "modelo": aviso.modelo,
        "origem": aviso.origem,
        "data_aviso": aviso.data_aviso,
        "lido_por_nome": aviso.lido_por_nome,
        "lido_em": aviso.lido_em,
        "status": aviso.status,
        "capacidade_atual": aviso.capacidade_atual,
        "estoque_maximo": aviso.estoque_maximo,
        "pecas_criticas": pecas_criticas,
        "historico": _montar_historico_aviso(aviso),
    }


# ====================================================================
# [FIM BLOCO] _montar_payload_aviso
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] montar_painel_avisos
# [RESPONSABILIDADE] Consolidar dados da central de avisos para tela e APIs
# ====================================================================
def montar_painel_avisos() -> Dict:
    avisos_calculados: List[Dict] = listar_avisos_capacidade()
    _upsert_avisos_automaticos(avisos_calculados)

    mapa_pecas = {a["codigo"]: a.get("pecas_criticas", []) for a in avisos_calculados}

    avisos_db = (
        Aviso.query.filter(Aviso.tipo == "capacidade")
        .order_by(Aviso.status.asc(), Aviso.data_aviso.desc())
        .all()
    )

    avisos: List[Dict] = [
        _montar_payload_aviso(
            aviso=aviso,
            pecas_criticas=mapa_pecas.get(aviso.codigo, []),
        )
        for aviso in avisos_db
    ]

    ativos = [a for a in avisos if a.get("status") != "resolvido"]

    return {
        "avisos": avisos,
        "avisos_qtd": len(ativos),
        "tem_avisos": len(ativos) > 0,
    }


# ====================================================================
# [FIM BLOCO] montar_painel_avisos
# ====================================================================


# ====================================================================
# [BLOCO] FUNÇÃO
# [NOME] montar_card_home_producao
# [RESPONSABILIDADE] Gerar payload resumido para o card AVISOS da home da produção
# ====================================================================
def montar_card_home_producao() -> Dict:
    painel = montar_painel_avisos()
    return {
        "avisos_qtd": painel["avisos_qtd"],
        "avisos_ativos": painel["tem_avisos"],
    }


# ====================================================================
# [FIM BLOCO] montar_card_home_producao
# ====================================================================
