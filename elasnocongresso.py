#!/usr/bin/env python
# coding: utf-8

# In[11]:


# -*- coding: utf-8
# AZMina (https://azmina.com.br/)
# Reinaldo Chaves (reichaves@gmail.gom)
# Bárbara Libório
# Script para ler as APIs da Câmara e Senado
# Procurar proposições do dia anterior e corrente
# Filtrar aquelas de interesse para os direitos da mulheres
# Criar frases com os resumos da tramitação
# E tweetar no @elasnocongresso

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import json
import xmltodict
import sys
import hashlib

def hash_text(text, algorithm="sha256"):

    if isinstance(text, str):
        hash_object = hashlib.new(algorithm)
        hash_object.update(text.encode())
        return hash_object.hexdigest()
    else:
        return None

# FUNÇÃO DA CÂMARA DOS DEPUTADOS
def camara(dia_anterior, mes_anterior, ano_anterior, dia_hoje, mes_hoje, ano_hoje):
    # Forma url de pesquisa
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes?dataInicio=%s-%s-%s&dataFim=%s-%s-%s&ordem=ASC&ordenarPor=id" % (
            ano_anterior, mes_anterior, dia_anterior, ano_hoje, mes_hoje, dia_hoje)
    print(url)

    # Captura quantas páginas tem esse intervalo de data na API
    parametros = {'formato': 'json', 'itens': 100}
    resposta = requests.get(url, parametros)

    for vez in resposta.json()['links']:
        conta = {"rel": vez['rel'].strip(), "href": vez['href'].strip()}

    # Testa se a url tem alguma proposicao
    ultimo = conta['rel']
    if ultimo != 'last':
        column_names = ["a"]
        df = pd.DataFrame(columns=column_names)
        return df

    # Para este item da API da Câmara sempre o último item link (last) tem o número de páginas
    # Considerando 100 itens por página

    # Isola o endereço de last
    link_ultimo = str(conta['href'].strip())

    # Encontra local exato onde termina o número de páginas
    posicao = int(link_ultimo.find('&itens='))

    # Com um fatiamento de lista, a partir da posição 139 onde sempre está o número, captura o número
    # de caracteres que corresponde a "posicao"
    # Exemplo: se "posicao" tiver 141 então vai ser [139:141]
    # o que significa comprimento de 139 (inclusive) até 141 (exclusive)
    # E adiciono mais 1 porque o range abaixo sempre vai um menos
    ultima = int(link_ultimo[139:posicao]) + 1

    # Cria lista vazia
    proposicoes = []

    # Faz a iteração a partir do número de páginas encontrado
    for pagina in range(1, ultima):
            parametros = {'formato': 'json', 'itens': 100, 'pagina': pagina}
            print(url)
            resposta = requests.get(url, parametros)

    # Captura os dados
            for vez in resposta.json()['dados']:
                dicionario = {"id": str(vez['id']).strip(),
                                                    "uri": str(vez['uri']).strip(),
                                                    "siglaTipo": str(vez['siglaTipo']).strip(),
                                                    "codTipo": str(vez['codTipo']).strip(),
                                                    "numero": str(vez['numero']).strip(),
                                                    "ano": str(vez['ano']).strip(),
                                                    "ementa": str(vez['ementa']).strip()
                                                    }
                proposicoes.append(dicionario)

    df_proposicoes_api = pd.DataFrame(proposicoes)
    # df_proposicoes_api.info()

    # Isola apenas proposicoes de interesse
    df_proposicoes_api['ementa_copia'] = df_proposicoes_api['ementa']
    df_proposicoes_api['ementa_copia'] = df_proposicoes_api['ementa_copia'].str.upper()

    df_proposicoes_api_final = df_proposicoes_api[pd.notnull(
            df_proposicoes_api['ementa_copia'])].copy()

    # Coleta autores
    endpoint = "https://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarAutoresProposicao?codProposicao="

    conta = 0

    for num, row in df_proposicoes_api_final.iterrows():
        id = row['id']

        url = endpoint + id
        print(url)

        try:
            r = requests.get(url)
        except requests.exceptions.RequestException as e:
            print("Requests exception: {}".format(e))

        jsonString = json.dumps(xmltodict.parse(r.text), indent=4)

        d = json.loads(jsonString)

        lista = [d['autores']]

        df_lista = pd.DataFrame(lista)
        df_lista["id"] = id

        if conta == 0:
            df_autores = df_lista.copy()
        else:
            df_autores = df_autores.append(df_lista)

        conta = conta + 1
    # df_autores.info()

    seleciona = mulher(df_proposicoes_api_final, 'camara')

    # Testa se há frases no dia
    tamanho = len(seleciona)
    if tamanho == 0:
        return seleciona


    # Busca a última situação das proposicoes
    endpoint = "https://dadosabertos.camara.leg.br/api/v2/proposicoes/"

    projetos = []
    parametros = {'formato': 'json'}


    for num, row in seleciona.iterrows():
        id = row['id']

        url = endpoint + id
        print(url)

        # captura os dados de detalhes
        try:
            r = requests.get(url, parametros)
        except requests.exceptions.RequestException as e:
            print("Requests exception: {}".format(e))

        vez =  r.json()['dados']

        dicionario = {"id": str(vez['id']).strip(),
                                        "uri": str(vez['uri']).strip(),
                                                    "siglaTipo": str(vez['siglaTipo']).strip(),
                                                    "codTipo": str(vez['codTipo']).strip(),
                                                    "numero": str(vez['numero']).strip(),
                                                    "ano": str(vez['ano']).strip(),
                                                    "ementa": str(vez['ementa']).strip(),
                                                    "dataApresentacao": str(vez['dataApresentacao']).strip(),
                                                    "statusProposicao_dataHora": str(vez['statusProposicao']['dataHora']).strip(),
                                                    "statusProposicao_siglaOrgao": str(vez['statusProposicao']['siglaOrgao']).strip(),
                                                    "statusProposicao_siglaOrgao": str(vez['statusProposicao']['siglaOrgao']).strip(),
                                                    "statusProposicao_descricaoTramitacao": str(vez['statusProposicao']['descricaoTramitacao']).strip(),
                                                    "statusProposicao_descricaoSituacao": str(vez['statusProposicao']['descricaoSituacao']).strip(),
                                                    "statusProposicao_despacho": str(vez['statusProposicao']['despacho']).strip(),
                                                    "keywords": str(vez['keywords']).strip(),
                                                    "urlInteiroTeor": str(vez['urlInteiroTeor']).strip(),
                                                    "uriAutores": str(vez['uriAutores']).strip()
                                                    }

        projetos.append(dicionario)

    df_proposicoes_situacao = pd.DataFrame(projetos)
    # Inclui autores
    df_proposicoes_situacao_autor = pd.merge(df_proposicoes_situacao.drop_duplicates('id'), df_autores, left_on='id', right_on='id')
    # df_projetos_situacao.info()
    # df_projetos_situacao.to_csv('resultados/camara/proposicoes_camara_do_dia_mulheres_apenas_ultima_tramitacao.csv', index=False)

    df_proposicoes_situacao_autor['ementa_minuscula'] = df_proposicoes_situacao_autor['ementa']
    df_proposicoes_situacao_autor['ementa_minuscula'] = df_proposicoes_situacao_autor['ementa_minuscula'].str.lower()

    return df_proposicoes_situacao_autor





# FUNÇÃO DO SENADO
# função para ler todas chaves nas APIs do senado
def get_by_key(key, value):
        try:
                if '.' in key:
                        old_key, new_key = key.split('.', 1)
                        new_value = value[old_key]
                        return get_by_key(new_key, new_value)
                else:
                        return value[key]
        except (KeyError, TypeError) as _:
                return None


def senado(ano_anterior, mes_anterior, dia_anterior):
    # Define header padrão
    headers = {"Accept" : "application/json"}

    # Forma url de pesquisa principal
    url = "http://legis.senado.leg.br/dadosabertos/materia/tramitando?data=%s%s%s" % (ano_anterior, mes_anterior, dia_anterior)
    print(url)

    tramitando = []

    try:
        r = requests.get(url, headers=headers)
        tramit = r.json()
    except requests.exceptions.RequestException as e:
        print("Requests exception: {}".format(e))

    # Testa se a url tem alguma proposicao
    try:
        teste = str(tramit["ListaMateriasTramitando"]["Materias"]["Materia"])
    except KeyError:
        column_names = ["a"]
        df = pd.DataFrame(columns = column_names)
        return df
    except TypeError:
        column_names = ["a"]
        df = pd.DataFrame(columns = column_names)
        return df

    # Captura dados de proposicoes tramitando
    for item in tramit["ListaMateriasTramitando"]["Materias"]["Materia"]:
        dicionario = {
                        "CodigoMateria": get_by_key('IdentificacaoMateria.CodigoMateria', item),
                        "SiglaCasaIdentificacaoMateria": get_by_key('IdentificacaoMateria.SiglaCasaIdentificacaoMateria', item),
                        "NomeCasaIdentificacaoMateria": get_by_key('IdentificacaoMateria.NomeCasaIdentificacaoMateria', item),
                        "SiglaSubtipoMateria": get_by_key('IdentificacaoMateria.SiglaSubtipoMateria', item),
                        "DescricaoSubtipoMateria": get_by_key('IdentificacaoMateria.DescricaoSubtipoMateria', item),
                        "NumeroMateria": get_by_key('IdentificacaoMateria.NumeroMateria', item),
                        "AnoMateria": get_by_key('IdentificacaoMateria.AnoMateria', item),
                        "DescricaoIdentificacaoMateria": get_by_key('IdentificacaoMateria.DescricaoIdentificacaoMateria', item),
                        "IndicadorTramitando": get_by_key('IdentificacaoMateria.IndicadorTramitando', item),
                        "DataUltimaAtualizacao": get_by_key('DataUltimaAtualizacao', item)
                        }

        tramitando.append(dicionario)

    df_tramitando = pd.DataFrame(tramitando)
    # df_tramitando.info()

    # df_tramitando.to_csv('resultados/senado/proposicoes_senado_do_dia.csv',index=False)


    # Dados de cada materia
    prefixo = 'http://legis.senado.leg.br/dadosabertos/materia/'

    projetos_det = []

    for num, row in df_tramitando.iterrows():
        codigo = row['CodigoMateria']

        url = prefixo + codigo
        print(url)

        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:",errh)
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:",errc)
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:",errt)
        except requests.exceptions.RequestException as err:
            print ("OOps: Something Else",err)

        projects = r.json()

        dicionario = {
                        "CodigoMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.CodigoMateria', projects),
                        "SiglaCasaIdentificacaoMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.SiglaCasaIdentificacaoMateria', projects),
                        "NomeCasaIdentificacaoMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.NomeCasaIdentificacaoMateria', projects),
                        "SiglaSubtipoMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.SiglaSubtipoMateria', projects),
                        "DescricaoSubtipoMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.DescricaoSubtipoMateria', projects),
                        "NumeroMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.NumeroMateria', projects),
                        "AnoMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.AnoMateria', projects),
                        "DescricaoObjetivoProcesso": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.DescricaoObjetivoProcesso', projects),
                        "DescricaoIdentificacaoMateria": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.DescricaoIdentificacaoMateria', projects),
                        "IndicadorTramitando": get_by_key('DetalheMateria.Materia.IdentificacaoMateria.IndicadorTramitando', projects),
                        "EmentaMateria": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.EmentaMateria', projects),
                        "ExplicacaoEmentaMateria": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.ExplicacaoEmentaMateria', projects),
                        "ApelidoMateria": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.ApelidoMateria', projects),
                        "IndicadorComplementar": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.IndicadorComplementar', projects),
                        "DataApresentacao": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.DataApresentacao', projects),
                        "DataLeitura": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.DataLeitura', projects),
                        "SiglaCasaLeitura": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.SiglaCasaLeitura', projects),
                        "NomeCasaLeitura": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.NomeCasaLeitura', projects),
                        "CodigoNatureza": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.NaturezaMateria.CodigoNatureza', projects),
                        "NomeNatureza": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.NaturezaMateria.NomeNatureza', projects),
                        "DescricaoNatureza": get_by_key('DetalheMateria.Materia.DadosBasicosMateria.NaturezaMateria.DescricaoNatureza', projects),
                        "Codigo_assunto": get_by_key('DetalheMateria.Materia.Assunto.AssuntoEspecifico.Codigo', projects),
                        "Descricao_assunto": get_by_key('DetalheMateria.Materia.Assunto.AssuntoEspecifico.Descricao', projects),
                        "Codigo_assunto_geral": get_by_key('DetalheMateria.Materia.Assunto.AssuntoGeral.Codigo', projects),
                        "Descricao_assunto_geral": get_by_key('DetalheMateria.Materia.Assunto.AssuntoGeral.Descricao', projects),
                        "NomePoderOrigem": get_by_key('DetalheMateria.Materia.OrigemMateria.NomePoderOrigem', projects),
                        "SiglaCasaOrigem": get_by_key('DetalheMateria.Materia.OrigemMateria.SiglaCasaOrigem', projects),
                        "NomeCasaOrigem": get_by_key('DetalheMateria.Materia.OrigemMateria.NomeCasaOrigem', projects),
                        "SiglaCasaIniciadora": get_by_key('DetalheMateria.Materia.CasaIniciadoraNoLegislativo.SiglaCasaIniciadora', projects),
                        "NomeCasaIniciadora": get_by_key('DetalheMateria.Materia.CasaIniciadoraNoLegislativo.NomeCasaIniciadora', projects)
                                         }

        try:
            NomeAutor = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['NomeAutor'])
        except KeyError:
            NomeAutor = None
        except TypeError:
            NomeAutor = None

        try:
            SiglaTipoAutor = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['SiglaTipoAutor'])
        except KeyError:
            SiglaTipoAutor = None
        except TypeError:
         SiglaTipoAutor = None

        try:
                DescricaoTipoAutor = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['DescricaoTipoAutor'])
        except KeyError:
                DescricaoTipoAutor = None
        except TypeError:
                DescricaoTipoAutor = None

        try:
                UfAutor = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['UfAutor'])
        except KeyError:
                UfAutor = None
        except TypeError:
                UfAutor = None

        try:
            NumOrdemAutor = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['NumOrdemAutor'])
        except KeyError:
            NumOrdemAutor = None
        except TypeError:
            NumOrdemAutor = None

        try:
            IndicadorOutrosAutores = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IndicadorOutrosAutores'])
        except KeyError:
            IndicadorOutrosAutores = None
        except TypeError:
            IndicadorOutrosAutores = None

        try:
            CodigoParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['CodigoParlamentar'])
        except KeyError:
            CodigoParlamentar = None
        except TypeError:
            CodigoParlamentar = None

        try:
            CodigoPublicoNaLegAtual = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['CodigoPublicoNaLegAtual'])
        except KeyError:
            CodigoPublicoNaLegAtual = None
        except TypeError:
            CodigoPublicoNaLegAtual = None

        try:
            NomeParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['NomeParlamentar'])
        except KeyError:
            NomeParlamentar = None
        except TypeError:
            NomeParlamentar = None

        try:
            NomeCompletoParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['NomeCompletoParlamentar'])
        except KeyError:
            NomeCompletoParlamentar = None
        except TypeError:
             NomeCompletoParlamentar = None

        try:
            SexoParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['SexoParlamentar'])
        except KeyError:
            SexoParlamentar = None
        except TypeError:
            SexoParlamentar = None

        try:
            FormaTratamento = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['FormaTratamento'])
        except KeyError:
            FormaTratamento = None
        except TypeError:
            FormaTratamento = None

        try:
            UrlFotoParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['UrlFotoParlamentar'])
        except KeyError:
            UrlFotoParlamentar = None
        except TypeError:
             UrlFotoParlamentar = None

        try:
            UrlPaginaParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['UrlPaginaParlamentar'])
        except KeyError:
            UrlPaginaParlamentar = None
        except TypeError:
            UrlPaginaParlamentar = None

        try:
            EmailParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['EmailParlamentar'])
        except KeyError:
            EmailParlamentar = None
        except TypeError:
            EmailParlamentar = None

        try:
            SiglaPartidoParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['SiglaPartidoParlamentar'])
        except KeyError:
            SiglaPartidoParlamentar = None
        except TypeError:
            SiglaPartidoParlamentar = None

        try:
            UfParlamentar = str(projects['DetalheMateria']['Materia']['Autoria']['Autor'][0]['IdentificacaoParlamentar']['UfParlamentar'])
        except KeyError:
            UfParlamentar = None
        except TypeError:
            UfParlamentar = None

        try:
            NumeroAutuacao = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['NumeroAutuacao'])
        except KeyError:
            NumeroAutuacao = None
        except TypeError:
            NumeroAutuacao = None

        try:
            DataSituacao = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Situacao']['DataSituacao'])
        except KeyError:
            DataSituacao = None
        except TypeError:
            DataSituacao = None

        try:
            CodigoSituacao = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Situacao']['CodigoSituacao'])
        except KeyError:
            CodigoSituacao = None
        except TypeError:
            CodigoSituacao = None

        try:
            SiglaSituacao = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Situacao']['SiglaSituacao'])
        except KeyError:
            SiglaSituacao = None
        except TypeError:
            SiglaSituacao = None

        try:
            DescricaoSituacao = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Situacao']['DescricaoSituacao'])
        except KeyError:
            DescricaoSituacao = None
        except TypeError:
            DescricaoSituacao = None

        try:
            DataLocal = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Local']['DataLocal'])
        except KeyError:
            DataLocal = None
        except TypeError:
            DataLocal = None

        try:
            CodigoLocal = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Local']['CodigoLocal'])
        except KeyError:
            CodigoLocal = None
        except TypeError:
            CodigoLocal = None

        try:
            TipoLocal = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Local']['TipoLocal'])
        except KeyError:
            TipoLocal = None
        except TypeError:
            TipoLocal = None

        try:
            SiglaCasaLocal = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Local']['SiglaCasaLocal'])
        except KeyError:
            SiglaCasaLocal = None
        except TypeError:
            SiglaCasaLocal = None

        try:
            NomeCasaLocal = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Local']['NomeCasaLocal'])
        except KeyError:
            NomeCasaLocal = None
        except TypeError:
            NomeCasaLocal = None

        try:
            SiglaLocal = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Local']['SiglaLocal'])
        except KeyError:
            SiglaLocal = None
        except TypeError:
            SiglaLocal = None

        try:
            NomeLocal = str(projects['DetalheMateria']['Materia']['SituacaoAtual']['Autuacoes']['Autuacao'][0]['Local']['NomeLocal'])
        except KeyError:
            NomeLocal = None
        except TypeError:
            NomeLocal = None

        try:
            url_emendas = str(projects['DetalheMateria']['Materia']['OutrasInformacoes']['Servico'][0]['UrlServico'])
        except KeyError:
            url_emendas = None
        except TypeError:
            url_emendas = None

        try:
            url_movimentacoes = str(projects['DetalheMateria']['Materia']['OutrasInformacoes']['Servico'][1]['UrlServico'])
        except KeyError:
            url_movimentacoes = None
        except TypeError:
            url_movimentacoes = None

        try:
            url_relatorias = str(projects['DetalheMateria']['Materia']['OutrasInformacoes']['Servico'][2]['UrlServico'])
        except KeyError:
            url_relatorias = None
        except TypeError:
            url_relatorias = None

        try:
            url_texto = str(projects['DetalheMateria']['Materia']['OutrasInformacoes']['Servico'][3]['UrlServico'])
        except KeyError:
            url_texto = None
        except TypeError:
            url_texto = None

        try:
            url_votacoes_materia = str(projects['DetalheMateria']['Materia']['OutrasInformacoes']['Servico'][4]['UrlServico'])
        except KeyError:
            url_votacoes_materia = None
        except TypeError:
            url_votacoes_materia = None

        try:
            url_votacoes_comissoes = str(projects['DetalheMateria']['Materia']['OutrasInformacoes']['Servico'][5]['UrlServico'])
        except KeyError:
            url_votacoes_comissoes = None
        except TypeError:
            url_votacoes_comissoes = None

        dicionario['NomeAutor'] = NomeAutor
        dicionario['SiglaTipoAutor'] = SiglaTipoAutor
        dicionario['DescricaoTipoAutor'] = DescricaoTipoAutor
        dicionario['UfAutor'] = UfAutor
        dicionario['NumOrdemAutor'] = NumOrdemAutor
        dicionario['IndicadorOutrosAutores'] = IndicadorOutrosAutores
        dicionario['CodigoParlamentar'] = CodigoParlamentar
        dicionario['CodigoPublicoNaLegAtual'] = CodigoPublicoNaLegAtual
        dicionario['NomeParlamentar'] = NomeParlamentar
        dicionario['NomeCompletoParlamentar'] = NomeCompletoParlamentar
        dicionario['SexoParlamentar'] = SexoParlamentar
        dicionario['FormaTratamento'] = FormaTratamento
        dicionario['UrlFotoParlamentar'] = UrlFotoParlamentar
        dicionario['UrlPaginaParlamentar'] = UrlPaginaParlamentar
        dicionario['EmailParlamentar'] = EmailParlamentar
        dicionario['SiglaPartidoParlamentar'] = SiglaPartidoParlamentar
        dicionario['UfParlamentar'] = UfParlamentar
        dicionario['NumeroAutuacao'] = NumeroAutuacao
        dicionario['DataSituacao'] = DataSituacao
        dicionario['CodigoSituacao'] = CodigoSituacao
        dicionario['SiglaSituacao'] = SiglaSituacao
        dicionario['DescricaoSituacao'] = DescricaoSituacao
        dicionario['DataLocal'] = DataLocal
        dicionario['CodigoLocal'] = CodigoLocal
        dicionario['TipoLocal'] = TipoLocal
        dicionario['SiglaCasaLocal'] = SiglaCasaLocal
        dicionario['NomeCasaLocal'] = NomeCasaLocal
        dicionario['SiglaLocal'] = SiglaLocal
        dicionario['NomeLocal'] = NomeLocal
        dicionario['url_emendas'] = url_emendas
        dicionario['url_movimentacoes'] = url_movimentacoes
        dicionario['url_relatorias'] = url_relatorias
        dicionario['url_texto'] = url_texto
        dicionario['url_votacoes_materia'] = url_votacoes_materia
        dicionario['url_votacoes_comissoes'] = url_votacoes_comissoes


        projetos_det.append(dicionario)

    df_propdia_det = pd.DataFrame(projetos_det)
    df_propdia_det = df_propdia_det[pd.notnull(df_propdia_det['EmentaMateria'])].copy()
    # df_propdia_det.info()


    # Captura link do inteiro teor
    prefixo = 'http://legis.senado.leg.br/dadosabertos/materia/textos/'

    prop_teor = []

    for num, row in df_propdia_det.iterrows():
        codigo = row['CodigoMateria']

        url = prefixo + codigo
        print(url)

        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:",errh)
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:",errc)
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:",errt)
        except requests.exceptions.RequestException as err:
            print ("OOps: Something Else",err)

        projects = r.json()

        dicionario = {
                        "CodigoMateria": get_by_key('TextoMateria.Materia.IdentificacaoMateria.CodigoMateria', projects)}

        try:
            CodigoTexto = str(projects['TextoMateria']['Materia']['Textos']['Nome Proposição'][0]['CodigoTexto'])
        except KeyError:
            CodigoTexto = None
        except TypeError:
            CodigoTexto = None

        try:
            UrlTexto = str(projects['TextoMateria']['Materia']['Textos']['Nome Proposição'][0]['UrlTexto'])
        except KeyError:
            UrlTexto = None
        except TypeError:
            UrlTexto = None

        dicionario['CodigoTexto'] = CodigoTexto
        dicionario['UrlTexto'] = UrlTexto

        prop_teor.append(dicionario)

    df_prop_teor = pd.DataFrame(prop_teor)
    # df_prop_teor.info()

    # Une os dois dataframes
    df_proposicoes = pd.merge(df_propdia_det, df_prop_teor, left_on='CodigoMateria', right_on='CodigoMateria')
    # df_proposicoes.info()
    # df_proposicoes.to_csv('resultados/senado/proposicoes_senado_detalhes_do_dia.csv',index=False)


    # Isola apenas proposicoes de interesse
    df_proposicoes['ementa_copia'] = df_proposicoes['EmentaMateria']
    df_proposicoes['ementa_copia'] = df_proposicoes['ementa_copia'].str.upper()
    df_proposicoes['ementa_minuscula'] = df_proposicoes['EmentaMateria']
    df_proposicoes['ementa_minuscula'] = df_proposicoes['EmentaMateria'].str.lower()

    seleciona = mulher(df_proposicoes, 'senado')
    # seleciona.info()

    return seleciona





# FUNÇÃO PARA TERMOS DE INTERESSE
def mulher(dados, origem):
    # Define termos de interesse
    search_list = ["MULHER", "MULHERES", "TRABALHO DOMÉSTICO", "VIOLÊNCIA CONTRA A MULHER", "VIOLÊNCIA DOMÉSTICA", "VIOLÊNCIA DE GÊNERO", "MARIA DA PENHA", "ABORTO", "ABORTAMENTO", "INTERRUPÇÃO DE GRAVIDEZ", "INTERRUPÇÃO DE GESTAÇÃO", "DIREITO REPRODUTIVO", "DIREITOS REPRODUTIVOS", "DIREITO À VIDA", "CONCEPÇÃO", "CONTRACEPÇÃO", "CONTRACEPTIVO", "MISOPROSTOL", "MIFEPRISTONE", "CYTOTEC", "ÚTERO", "GESTAÇÃO", "GRAVIDEZ", "GESTANTE", "SEXO BIOLÓGICO", "PARTO", "VIOLÊNCIA OBSTÉTRICA", "FETO", "BEBÊ", "CRIANÇA", "VIOLÊNCIA SEXUAL", "FEMINICÍDIO", "MORTE DE MULHER", "MORTE DE MULHERES", "HOMICÍDIO DE MULHER", "HOMICÍDIO DE MULHERES", "ASSÉDIO SEXUAL", "ASSÉDIO", "ESTUPRO", "VIOLÊNCIA SEXUAL", "ABUSO SEXUAL", "ESTUPRO DE VULNERÁVEL", "LICENÇA MATERNIDADE", "FEMININO", "MULHER NEGRA", "MULHERES NEGRAS", "MULHERES QUILOMBOLAS", "MULHERES INDÍGENAS", "NEGRAS", "NEGRA", "RACISMO", "RAÇA", "RACIAL", "ABUSO SEXUAL", "MATERNIDADE", "MÃE", "AMAMENTAÇÃO", "SEXUALIDADE", "SEXO", "GÊNERO", "FEMINISMO", "MACHISMO", "GUARDA DE FILHOS", "GUARDA DOS FILHOS", "IGUALDADE DE GÊNERO", "IDENTIDADE DE GÊNERO", "IDEOLOGIA DE GÊNERO", "EDUCAÇÃO SEXUAL", "ESCOLA SEM PARTIDO", "TRANSEXUAL", "TRANSEXUALIDADE", "MULHER TRANS", "MULHERES TRANS", "MUDANÇA DE SEXO", "READEQUAÇÃO SEXUAL", "EXPLORAÇÃO SEXUAL", "PROSTITUIÇÃO", "ORIENTAÇÃO SEXUAL", "HOMOSSEXUAL", "HOMOSSEXUALIDADE", "HOMOSSEXUALISMO",  "LÉSBICA",  "LÉSBICAS",  "DIREITO DOS HOMENS", "EDUCAÇÃO RELIGIOSA",  "DEUS", "RELIGIÃO", "EDUCACÃO DOMICILIAR", "HOMESCHOOLING", "CRECHE",  "EDUCAÇÃO INFANTIL",  "CASAMENTO INFANTIL"]
    # dados.info()
    mask = dados['ementa_copia'].str.contains('|'.join(search_list))
    seleciona = dados[mask]
    return seleciona




# CRIA FRASES
def frases(dados, origem):
    lista_sentencas = []
    cols = list(dados)
    print('====================')
    print(cols)
    print('====================')

    ## Camara
    # ['id',
    #  'uri',
    #  'siglaTipo', 
    #  'codTipo',
    #  'numero',
    #  'ano',
    #  'ementa',
    #  'dataApresentacao',
    #  'statusProposicao_dataHora',
    #  'statusProposicao_siglaOrgao',
    #  'statusProposicao_descricaoTramitacao',
    #  'statusProposicao_descricaoSituacao',
    #  'statusProposicao_despacho',
    #  'keywords',
    #  'urlInteiroTeor',
    #  'uriAutores',
    #  'autor',
    #  'ementa_minuscula'
    # ]

    ## SENADO
    #  ['CodigoMateria',
    # 'SiglaCasaIdentificacaoMateria',
    # 'NomeCasaIdentificacaoMateria',
    # 'SiglaSubtipoMateria',
    # 'DescricaoSubtipoMateria',
    # 'NumeroMateria',
    # 'AnoMateria',
    # 'DescricaoObjetivoProcesso',
    # 'DescricaoIdentificacaoMateria',
    # 'IndicadorTramitando',
    # 'EmentaMateria',
    # 'ExplicacaoEmentaMateria',
    # 'ApelidoMateria',
    # 'IndicadorComplementar',
    # 'DataApresentacao',
    # 'DataLeitura',
    # 'SiglaCasaLeitura',
    # 'NomeCasaLeitura',
    # 'CodigoNatureza',
    # 'NomeNatureza',
    # 'DescricaoNatureza',
    # 'Codigo_assunto',
    # 'Descricao_assunto',
    # 'Codigo_assunto_geral',
    # 'Descricao_assunto_geral',
    # 'NomePoderOrigem',
    # 'SiglaCasaOrigem',
    # 'NomeCasaOrigem',
    # 'SiglaCasaIniciadora',
    # 'NomeCasaIniciadora',
    # 'NomeAutor',
    # 'SiglaTipoAutor',
    # 'DescricaoTipoAutor',
    # 'UfAutor',
    # 'NumOrdemAutor',
    # 'IndicadorOutrosAutores',
    # 'CodigoParlamentar',
    # 'CodigoPublicoNaLegAtual',
    # 'NomeParlamentar',
    # 'NomeCompletoParlamentar',
    # 'SexoParlamentar',
    # 'FormaTratamento',
    # 'UrlFotoParlamentar',
    # 'UrlPaginaParlamentar',
    # 'EmailParlamentar',
    # 'SiglaPartidoParlamentar',
    # 'UfParlamentar',
    # 'NumeroAutuacao',
    # 'DataSituacao',
    # 'CodigoSituacao',
    # 'SiglaSituacao',
    # 'DescricaoSituacao',
    # 'DataLocal',
    # 'CodigoLocal',
    # 'TipoLocal',
    # 'SiglaCasaLocal',
    # 'NomeCasaLocal',
    # 'SiglaLocal',
    # 'NomeLocal',
    # 'url_emendas',
    # 'url_movimentacoes',
    # 'url_relatorias',
    # 'url_texto',
    # 'url_votacoes_materia',
    # 'url_votacoes_comissoes',
    # 'CodigoTexto',
    # 'UrlTexto',
    # 'ementa_copia',
    # 'ementa_minuscula']

    conta = 1
    for num, row in dados.iterrows():

        if origem == 'senado':
                    proposicao_ementa = str(row['ementa_minuscula'] or '')
                    proposicao_tipo = str(row['SiglaSubtipoMateria'] or '')
                    proposicao_numero = str(row['NumeroMateria'] or '')
                    proposicao_ano = str(row['AnoMateria'] or '')
                    tramitacao = str(row['NomeLocal'] or '')
                    status = str(row['DescricaoSituacao'] or '')
                    endereco = str(row['UrlTexto'] or '')
                    nome = str((row['NomeAutor'] or row['NomeParlamentar'] or row['NomeCompletoParlamentar']) or '')
                    casa = 'SENADO'
                    id = str(row['CodigoMateria'] or '')
                    ementa = str(row['ementa_copia'] or '')
                    uf_autor = str(row['UfAutor'] or '')
                    partido_autor = str(row['SiglaPartidoParlamentar'] or '')
                    explicacao = str(row['ExplicacaoEmentaMateria'] or '')
                    data_apresentacao = str(row['DataApresentacao'] or '')
                    ultimo_despacho = str(row['DataSituacao'] or '')
        elif origem == 'camara':
                    proposicao_ementa = str(row['ementa_minuscula'] or '')
                    proposicao_tipo = str(row['siglaTipo'] or '')
                    proposicao_numero = str(row['numero'] or '')
                    proposicao_ano = str(row['ano'] or '')
                    tramitacao = str(row['statusProposicao_descricaoTramitacao'] or '')
                    status = str(row['statusProposicao_descricaoSituacao'] or '')
                    endereco = str(row['urlInteiroTeor'] or '')
                    nome = str(row['autor']).replace("[", "")
                    nome = nome.replace("]", "")
                    nome = nome.replace("'", "")
                    casa = 'CÂMARA'
                    id = proposicao_tipo + ' ' + proposicao_numero + '/' + proposicao_ano
                    ementa = str(row['ementa'] or '')
                    uf_autor = ''
                    partido_autor = ''
                    explicacao = ''
                    data_apresentacao = ''
                    ultimo_despacho = str(row['statusProposicao_despacho'] or '')

        try:
            id and nome
        except NameError:
            continue

        sentencas = {}

        if 'jornada de trabalho' in proposicao_ementa and 'mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'jornada de trabalho'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre jornada de trabalho para mulheres e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'jornada de trabalho' in proposicao_ementa and 'mulher' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'jornada de trabalho'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre jornada de trabalho para mulheres e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'violência contra a mulher' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'violência contra a mulher'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre violência contra a mulher e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'violência doméstica' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'violência doméstica'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre violência doméstica e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'aborto' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'aborto'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre aborto e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'violência sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'violência sexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre violência sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'feminicídio' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'feminicídio'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre feminicídio e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'assédio sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'assédio sexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre assédio sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'estupro' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'estupro'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre estupro e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'licença maternidade' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'licença maternidade'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre licença maternidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'mulheres' in proposicao_ementa or 'mulher' in proposicao_ementa or 'feminino' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'mulheres'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre mulheres e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'trabalho doméstico' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'trabalho doméstico'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre trabalho doméstico e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'maria da penha' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'maria da penha'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre Lei Maria da Penha e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'interrupção da gravidez' in proposicao_ementa or 'interrupção da gestação' in proposicao_ementa or 'interrupção de gestação' in proposicao_ementa or 'interrupção de gravidez' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'interrupção da gravidez'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre interrupção da gravidez e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'direitos reprodutivos' in proposicao_ementa or 'direito reprodutivo' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'direitos reprodutivos'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre direitos reprodutivos e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'direitos à vida' in proposicao_ementa or 'direito à vida' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'direitos à vida'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre direito à vida e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'contracepção' in proposicao_ementa or 'contraceptivos' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'contracepção'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre contracepção e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'violência obstétrica' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'violência obstétrica'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre violência obstétrica e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'misoprostol' in proposicao_ementa or 'mifepristone' in proposicao_ementa or 'cytotec' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'misoprostol'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre medicamentos abortivos e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'gestação' in proposicao_ementa or 'gravidez' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'gestação'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre gravidez e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'violência familiar' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'violência familiar'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre violência familiar e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'morte de mulher' in proposicao_ementa or 'morte de mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'morte de mulher'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre morte de mulheres e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'homicídio de mulher' in proposicao_ementa or 'homicídio de mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'homicídio de mulher'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre homicídio de mulheres e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'assédio' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'assédio'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre assédio e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'estupro de vulnerável' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'estupro de vulnerável'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre estupro de vulnerável e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'abuso sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'abuso sexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre abuso sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'mulher negra' in proposicao_ementa or 'mulheres negras' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'mulher negra'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre mulheres negras e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'maternidade' in proposicao_ementa or 'mãe' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'maternidade'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre maternidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'amamentação' in proposicao_ementa or 'leite materno' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'amamentação'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre amamentação e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'feminismo' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'feminismo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre feminismo e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'identidade de gênero' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'identidade de gênero'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre identidade de gênero e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'machismo' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'machismo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome},fala sobre machismo e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'guarda de filhos' in proposicao_ementa or 'guarda dos filhos' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'guarda de filhos'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre guarda dos filhos e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'igualdade de gênero' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'igualdade de gênero'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre igualdade de gênero e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'educação sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'educação sexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre educação sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'ideologia de gênero' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'ideologia de gênero'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre ideologia de gênero e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'transexualidade' in proposicao_ementa or 'transexual' in proposicao_ementa or 'mulher trans' in proposicao_ementa or 'mulheres trans' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'transexualidade'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre transexualidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'mudança de sexo' in proposicao_ementa or 'readequação sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'mudança de sexo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre readequação sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'exploração sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'exploração sexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre exploração sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'prostituição' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'prostituição'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre prostituição e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'racismo' in proposicao_ementa and 'mulher' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'racismo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre racismo e mulheres e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'racismo' in proposicao_ementa and 'mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'racismo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre racismo e mulheres e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'sexualidade' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'sexualidade'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre sexualidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'sexo' in proposicao_ementa and 'mulher' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'sexo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre sexualidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'sexo' in proposicao_ementa and 'mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'sexo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre sexualidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'deus' in proposicao_ementa and 'mulher' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'deus'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre religiosidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'deus' in proposicao_ementa and 'mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'deus'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre religiosidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'educação religiosa' in proposicao_ementa and 'mulher' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'educação religiosa'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre religiosidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'educação religiosa' in proposicao_ementa and 'mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'educação religiosa'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre religiosidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'religião' in proposicao_ementa and 'mulher' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'religião'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre religiosidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'religião' in proposicao_ementa and 'mulheres' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'religião'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre religiosidade e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'violência de gênero' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'violência de gênero'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre violência de gênero e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'parto' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'parto'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre parto e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'homeschooling' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'homeschooling'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre educação domiciliar e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'educação domiciliar' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'educação domiciliar'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre educação domiciliar e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'educação infantil' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'educação infantil'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre educação infantil e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'creches' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'creches'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre educação infantil e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'casamento infantil' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'casamento infantil'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre casamento infantil e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'homossexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'homossexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre orientação sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'homossexualidade' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'homossexualidade'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre orientação sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'homossexualismo' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'homossexualismo'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre orientação sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'orientação sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'orientação sexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre orientação sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'opção sexual' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'opção sexual'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre orientação sexual e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'criança' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'criança'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre crianças e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'sexo biológico' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'sexo biológico'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre sexo biológico e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'gênero' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'gênero'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre gênero e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'
        elif 'gestante' in proposicao_ementa:
            sentencas['id'] = f'{id}'
            sentencas['Casa'] = f'{casa}'
            sentencas['Tipo'] = f'{proposicao_tipo}'
            sentencas['Tema'] = f'gestante'
            sentencas['nome'] = f'{nome}'
            sentencas['Nome Proposição'] = f'{casa}: {proposicao_tipo} {proposicao_numero}/{proposicao_ano}, de autoria de {nome}, fala sobre gravidez e sofreu alterações em sua tramitação. Tramitação: {tramitacao}. Situação: {status}. {endereco}'
            sentencas['proposicao_ementa'] = f'{proposicao_ementa}'
            sentencas['proposicao_numero'] = f'{proposicao_numero}'
            sentencas['proposicao_ano'] = f'{proposicao_ano}'
            sentencas['tramitacao'] = f'{tramitacao}'
            sentencas['status'] = f'{status}'
            sentencas['endereco'] = f'{endereco}'
            sentencas['ementa'] = f'{ementa}'
            sentencas['uf_autor'] = f'{uf_autor}'
            sentencas['partido_autor'] = f'{partido_autor}'
            sentencas['explicacao'] = f'{explicacao}'
            sentencas['data_apresentacao'] = f'{data_apresentacao}'
            sentencas['ultimo_despacho'] = f'{ultimo_despacho}'

        # Testa se dicionario veio vazio
        res = not bool(sentencas)
        if res == False:
            lista_sentencas.append(sentencas)

            # print(lista_sentencas)
        conta = conta + 1


    df_lista_sentencas = pd.DataFrame(lista_sentencas)
    # df_lista_sentencas.info()
    # df_lista_sentencas.to_csv('teste_sen2.csv',index=False)
            # df_lista_sentencas.info()
            # print(df_lista_sentencas)

    #with open('dados/tweets.json', 'w') as outfile:
    #    json.dump(lista_sentencas, outfile)


    return df_lista_sentencas




GLOBAL_lista_para_tweetar = []

# TWEETA AS FRASES
def tweeta(dados):

    # Isola apenas primeiras linhas
    # df = dados.bfill().iloc[[0]]
    # columns = list(df)


    for index, row in dados.iterrows():
        GLOBAL_lista_para_tweetar.append(row.to_json())


    # Itera nas colunas de cada frase
    # for i in columns:
    #     texto = df[i][0]
    #     GLOBAL_lista_para_tweetar.append( { "tweet": f'{texto}' })





# DEFINIR BLOCO DE EXECUÇÃO PRINCIPAL
def main():

    # Captura o dia, mês e ano de ontem
    dia_anterior = (datetime.now() - timedelta(1)).strftime('%d')
    mes_anterior = (datetime.now() - timedelta(1)).strftime('%m')
    ano_anterior = (datetime.now() - timedelta(1)).strftime('%Y')

    # Captura o dia, mês e ano de amanha (assim nao preciso mudar o codigo para remover o parametro data_ate)
    now = datetime.now()
    dia_hoje = (datetime.now() + timedelta(1)).strftime('%d')
    mes_hoje = (datetime.now() + timedelta(1)).strftime('%m')
    ano_hoje = (datetime.now() + timedelta(1)).strftime('%Y')

    # Captura proposicoes Camara
    prop_cam = camara(dia_anterior,mes_anterior,ano_anterior,dia_hoje,mes_hoje,ano_hoje)
    tamanho = len(prop_cam.index)
    print("Quantidade de proposicoes de interesse na Camara: ", tamanho)
    prop_cam.info()

    # Cria frases da Camara
    if tamanho != 0:
        df_lista_sentencas = frases(prop_cam, 'camara')
         # print(df_lista_sentencas)

        df_lista_sentencas['hash'] = df_lista_sentencas.iloc[:, 0].apply(hash_text)

         # Faz Tweets
        tam_frases = len(df_lista_sentencas.index)
        if tam_frases > 0:
            tweeta(df_lista_sentencas)

    print("/////////////////////////////////////")

    # Captura proposicoes Senado
    prop_sen = senado(ano_anterior, mes_anterior, dia_anterior)

    tamanho = len(prop_sen.index)
    print("Quantidade de proposicoes de interesse no Senado: ", tamanho)
    prop_sen.info()

    # Cria frases do Senado
    if tamanho != 0:
        df_lista_sentencas = frases(prop_sen, 'senado')
         # print(df_lista_sentencas)

        df_lista_sentencas['hash'] = df_lista_sentencas.iloc[:, 0].apply(hash_text)

         # Faz Tweets
        tam_frases = len(df_lista_sentencas.index)
        if tam_frases > 0:
            tweeta(df_lista_sentencas)



# executar bloco principal
if __name__ == '__main__':
    main()

    with open('dados/tweets.json', 'w') as outfile:
        json.dump(GLOBAL_lista_para_tweetar, outfile)


# In[ ]:




