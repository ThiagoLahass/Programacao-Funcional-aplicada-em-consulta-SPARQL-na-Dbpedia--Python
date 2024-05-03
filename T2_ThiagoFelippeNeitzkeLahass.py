from SPARQLWrapper import SPARQLWrapper, JSON
from functools import reduce


# =======================================================================================
# ======================================== BUSCA ========================================
# =======================================================================================

# Configurar o endpoint SPARQL
sparql = SPARQLWrapper("https://dbpedia.org/sparql")

# Configurar Query
sparql.setQuery("""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbp: <http://dbpedia.org/property/>

SELECT DISTINCT ?model ?yearCar ?class ?manufacturer ?foundingYear ?manufacturerCountry ?areaServed
WHERE {
    ?carro_uri a dbo:Automobile;
                rdfs:label ?model;
                dbo:productionStartYear ?productionStartYear;
                dbo:class/rdfs:label ?class;
                dbo:manufacturer ?manufacturer_uri.
    ?manufacturer_uri rdfs:label ?manufacturer;
                       dbo:foundingYear ?manufacturerFoundingYear;
                       dbp:locationCountry ?manufacturerCountry.
    OPTIONAL {?manufacturer_uri dbp:areaServed ?areaServed}
    BIND (xsd:gYear(?productionStartYear) as ?yearCar)
    BIND (xsd:gYear(?manufacturerFoundingYear) as ?foundingYear)
    FILTER (lang(?model) = 'en')
    FILTER (lang(?class) = 'en')
    FILTER (lang(?manufacturer) = 'en')
    FILTER (lang(?manufacturerCountry) = 'en')
    FILTER (lang(?areaServed) = 'en')
}
ORDER BY ASC(?yearCar)
""")

# Definir o formato da resposta como JSON
sparql.setReturnFormat(JSON)

# Executar a consulta e obter os resultados
RESULTS = sparql.query().convert()

# =======================================================================================
# ======================================== BUSCA ========================================
# =======================================================================================


# =======================================================================================
# ======================================== REGRAS =======================================
# =======================================================================================

# Processar os resultados
def getResults(resDcit):
    VALUES = resDcit['results']['bindings']
    return list( map ( lambda item: dict( map ( lambda key: (key, item[key]['value']), item.keys() )), VALUES) )

# Função para filtrar carros lançados em um determinado ano
def busca_carro_por_ano(cars_data, year):
    return list( filter( lambda car: int(car['yearCar'][:4]) == year, cars_data ) ) 

# Função para buscar carros por parte do nome
def busca_carro_por_nome(car_data, nome):
    return list( filter( lambda car: car['model'].__contains__(nome) , car_data ) )

# Função para buscar carros pela Classe
def busca_carro_por_classe(car_data, classe):
    return list( filter( lambda car: car['class'].__contains__(classe) , car_data ) )

# Função para verificar se um carro é antigo (default=1960)
def carro_antigo(car_data, threshold_year=1960, car_name=''):
    if car_name == '':
        return list(filter(lambda car: int(car['yearCar'][:4]) < threshold_year, car_data))
    else:
        return list(filter(lambda car: int(car['yearCar'][:4]) < threshold_year and car['model'] == car_name, car_data))

# Função para buscar fabricantes por parte do nome
def busca_fabricantes_por_nome(car_data, nome):
    return list( filter( lambda car: car['manufacturer'].__contains__(nome) , car_data ) )
    
# Função para contar a quantidade de modelos fabricados por um fabricante
def qtd_modelos_fabricante(car_data, fabricante):
    return reduce(lambda count, car: count + 1 if car['manufacturer'] == fabricante else count, car_data, 0)

# Função para contar a quantidade de modelos de fabricantes cujo ano de fundação seja na década de 1930
def qtd_modelos_fabricante_30s(car_data, fabricante):
    return reduce(lambda count, car: count + 1 if car['manufacturer'] == fabricante and 1930 <= int(car['foundingYear'][:4]) < 1940 else count, car_data, 0)

# Função para verificar se um fabricante fornece carros mundialmente
def fabricantes_que_vendem_mundialmente(car_data, fabricante):
    filtered = list(filter(lambda car: car['manufacturer'] == fabricante, car_data))
    if not any("Worldwide" in car['areaServed'] for car in filtered):
        return len(set(car['areaServed'] for car in filtered)) > 4
    return True if any("Worldwide" in car['areaServed'] for car in filtered) else False

# Função para encontrar carros concorrentes
def carros_concorrentes(car_data, modelo1, modelo2):
    cars_modelo1 = list(filter(lambda car: car['model'] == modelo1, car_data))
    cars_modelo2 = list(filter(lambda car: car['model'] == modelo2, car_data))
    if not cars_modelo1 or not cars_modelo2:
        return False
    car1 = cars_modelo1[0]
    car2 = cars_modelo2[0]
    return car1['class'] == car2['class'] and car1['yearCar'] == car2['yearCar']

# Função para verificar se um carro é confiável
def carro_confiavel(car_data, modelo):
    cars_modelo = list(filter(lambda car: car['model'] == modelo, car_data))
    if not cars_modelo:
        return False
    car = cars_modelo[0]
    fabricante = car['manufacturer']
    fabricante_info = list(filter(lambda car: car['manufacturer'] == fabricante, car_data))
    if not fabricante_info:
        return False
    fabricante_years = [int(info['yearCar'][:4]) for info in fabricante_info]
    if max(fabricante_years) - min(fabricante_years) > 20:
        return True
    return False

# Função para obter a década de lançamento de um carro
def decada_de_lancamento_do_carro(car_data, modelo):
    cars_modelo = list(filter(lambda car: car['model'] == modelo, car_data))
    if not cars_modelo:
        return None
    car = cars_modelo[0]
    year = int(car['yearCar'][:4])
    return year - (year % 10)

# Função para verificar se um modelo foi lançado no último ano
def novo_modelo(car_data, modelo, last_year):
    cars_modelo = list(filter(lambda car: car['model'] == modelo, car_data))
    if not cars_modelo:
        return False
    car = cars_modelo[0]
    return int(car['yearCar'][:4]) == last_year

# Função para contar a quantidade de fabricantes por país
def qtd_fabricantes_por_pais(car_data):
    fabricantes_pais = reduce(lambda count_dict, car: {**count_dict, car['manufacturerCountry']: count_dict.get(car['manufacturerCountry'], 0) + 1}, car_data, {})
    return fabricantes_pais

# =======================================================================================
# ======================================== REGRAS =======================================
# =======================================================================================


# =======================================================================================
# ====================================== CONSULTAS ======================================
# =======================================================================================

# Pegando os resultados e "limpando eles"
CARS_DATA = getResults(RESULTS)

## 1. Consultas relacionadas aos carros:
## 1.1 Consulta de todos os carros:
# print(CARS_DATA)
## 1.2 Consulta de carros lançados em uma data específica (exemplo: 1 de janeiro de 2023):
# print(busca_carro_por_ano(CARS_DATA, 2023))
## 1.3 Consulta de informações de um carro específico (exemplo: Lamborghini Aventador):
# print(busca_carro_por_nome(CARS_DATA, 'Lamborghini Aventador'))
## 1.4 Consulta de informações de carros de um Classe (exemplo: Executive car):
# print(busca_carro_por_classe(CARS_DATA, 'Executive car'))


## 2. Consultas relacionadas a carros antigos:
## 2.1 Consulta de carros antigos em geral:
# print(carro_antigo(CARS_DATA))
## 2.2 Consulta de um carro antigo específico (exemplo: Fiat 1100):
# print(carro_antigo(CARS_DATA, car_name='Fiat 1100'))                                                    # ESTÁ CORRETO DESSA FORMA?

## 3. Consultas de busca por nome de carro:
## 3.1 Consulta de carros que contêm a palavra "Corolla" no nome:
# print(busca_carro_por_nome(CARS_DATA, 'Corolla'))
## 3.2 Consulta de carros que contêm a palavra "Lamborghini" no nome e foram lançados em 2020:
# print(busca_carro_por_ano(busca_carro_por_nome(CARS_DATA, 'Lamborghini'), 2020))

# =========== ATÉ AQUI ===========

## 4. Consultas relacionadas a fabricantes de carros:
## 4.1 Consulta de fabricantes de um modelo específico (exemplo: Cadillac Celestiq):
# print(busca_fabricantes_por_nome(CARS_DATA, 'Cadillac Celestiq'))                                     (?????????????????? COMO FAZER ISSO?)
## 4.2 Consulta de quantidade de modelos fabricados por um fabricante (exemplo: Toyota):
print(qtd_modelos_fabricante(CARS_DATA, 'Toyota'))

## 5. Consultas relacionadas a década de lançamento do carro:
## 5.1 Consulta de década de lançamento de um modelo específico (exemplo: Toyota RAV4):
# print(decada_de_lancamento_do_carro(CARS_DATA, 'Toyota RAV4'))
## 5.2 Consulta de carros lançados na década de 2000:
# print(busca_carro_por_ano(CARS_DATA, 2000))                                                 (ERRADO! AJUSTAR!)


# Exemplo de uso: filtrar carros lançados antes de 1960
# print(carro_antigo(CARS_DATA, '1960-01-01'))

# Exemplo de uso: filtrar modelos que contenham o nome "Corolla"
# print(busca_carro_por_nome(CARS_DATA, 'Corolla'))

# Exemplo de uso: filtrar fabricantes que contenham o nome "Toyota"
# print(len(busca_fabricantes_por_nome(CARS_DATA, 'Toyota')))

# Exemplo de uso: filtrar fabricantes que contenham o nome "Toyota"
# print(len(busca_fabricantes_por_nome(CARS_DATA, 'Toyota')))

# =======================================================================================
# ====================================== CONSULTAS ======================================
# =======================================================================================









































# :- data_source(
# dbpedia_carros,
# sparql("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX dbo: <http://dbpedia.org/ontology/>
# PREFIX dbow: <http://dbpedia.org/ontology/Work/>
# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# PREFIX dbp: <http://dbpedia.org/property/>
       
# select distinct ?model ?yearCar ?class ?manufacturer ?foundingYear ?manufacturerCountry ?areaServed
# 	where { 
#         ?carro_uri a dbo:Automobile;
#         	rdfs:label ?model;
#         	dbo:productionStartYear ?productionStartYear;
#         	dbo:class/rdfs:label ?class;
#         	dbo:manufacturer ?manufacturer_uri.
#         ?manufacturer_uri rdfs:label ?manufacturer;
#         	dbo:foundingYear ?manufacturerFoundingYear;
#         	dbp:locationCountry ?manufacturerCountry.
#        		OPTIONAL {?manufacturer_uri dbp:areaServed ?areaServed}	
#        BIND (xsd:gYear(?productionStartYear) as ?yearCar)
#        BIND (xsd:gYear(?manufacturerFoundingYear) as ?foundingYear)
#        FILTER (lang(?model) = 'en')
#        FILTER (lang(?class) = 'en')
#        FILTER (lang(?manufacturer) = 'en')
#        FILTER (lang(?manufacturerCountry) = 'en')
#        FILTER (lang(?areaServed) = 'en')
#        }
#        ORDER BY ASC(?year) ?model
#   ",
#   [ endpoint('https://dbpedia.org/sparql')])  ).

# % Predicado para verificar se Substring faz parte de String
# substring(String, Substring) :- sub_string(String, _, _, _, Substring).

# % este predicado associa os carros às suas propriedades
# carros(Modelo, Classe, AnoLancamento) :- distinct([Modelo, Classe],
#                                          dbpedia_carros{model:Modelo, class:Classe, yearCar:AnoLancamento}).

# % carros lancados antes de 1960
# carroAntigo(Modelo) :- 	carros(Modelo, _, AnoDate),
#     					date_time_value(date, DT, AnoDate),
#     					date_time_value(year, DT, Ano),
#     					Ano < 1960.

# % busca um carro por parte do nome dele através do uso de string
# carrosBusca(CarroBusca, Modelo, Classe, Ano) :- carros(Modelo, Classe, Ano),
#     											substring(Modelo, CarroBusca).

# % este predicado associa os modelos aos seus respectivos fabricantes
# carrosFabricante(Modelo, Fabricante) :- distinct([Modelo],
#                                        	dbpedia_carros{model:Modelo, manufacturer:Fabricante}).

# % este predicado associa os fabricantes às suas propriedades
# fabricanteDeCarros(Fabricante, AnoFundacao, Localizacao, AreaServida) :- 	distinct([Fabricante, Localizacao, AreaServida],
#                                                                       		(dbpedia_carros{manufacturer:Fabricante, foundingYear:AnoFundacao, manufacturerCountry:Localizacao, areaServed:AreaServida})).

# % retorna a quantidade de modelos fabricados pela fabricante
# qtdModelosFabricante(Fabricante, QtdCarros) :- 	distinct([Fabricante], (fabricanteDeCarros(Fabricante,_,_,_))),
#     											aggregate_all(count, (carrosFabricante(_, Fabricante)), QtdCarros).

# % qtd de modelos de fabricantes cujo ano de fundação seja na decada de 1930
# qtdModelosFabricante30s(Fabricante, QtdCarros) :-	fabricanteDeCarros(Fabricante, AnoFundacaoDate,_,_),
#     												date_time_value(date, DT, AnoFundacaoDate),
#     												date_time_value(year, DT, Ano),
#     												Ano >= 1930, Ano < 1940,
#     												aggregate_all(count, (carrosFabricante(_, Fabricante)), QtdCarros).
    		
# % fabricantes de carros que fornecem carros mundialmente
# % se um fabricante não está servindo "Worldwide" diretamente, mas servir mais de 4 lugares diferentes,
# % então ele também é classificado como vendedor mundial
# fabricantesQueVendemMundialmente(Fabricante) :- distinct([Fabricante], (fabricanteDeCarros(Fabricante,_,_,AreaServida))),
#     											substring(AreaServida, "Worldwide");
#     											distinct([Fabricante], (fabricanteDeCarros(Fabricante,_,_,_))),
#     											aggregate_all(count, (fabricanteDeCarros(Fabricante,_,_,_)), QtdAreas),
#                                                 QtdAreas > 4.

# % carros concorrentes
# % verificar por que esta havendo repetição
# carrosConcorrentes(Modelo1, Modelo2, Classe) :- carros(Modelo1, Classe, Ano1),
#     											carros(Modelo2, Classe2, Ano2),
#     											dif(Modelo1, Modelo2),
#     											carrosFabricante(Modelo1, Fabricante1),
#     											carrosFabricante(Modelo2, Fabricante2),
#     											dif(Fabricante1, Fabricante2),
#     											Classe2 == Classe,
#     											date_time_value(date, DT, Ano1),
#     											date_time_value(year, DT, AnoModelo1),
#     											date_time_value(date, DT, Ano2),
#     											date_time_value(year, DT, AnoModelo2),
#     											AnoModelo1 == AnoModelo2.

# % carro confiável seria aquele cujo fabricante têm uma ampla área de serviço e está no mercado há mais de 20 anos
# % e não é um carro antigo
# carroConfiavel(Modelo) :- distinct([Modelo], (carrosFabricante(Modelo, Fabricante))),
#                           fabricanteDeCarros(Fabricante, AnoFundacao, _, _),
#                           date_time_value(date, DT, AnoFundacao),
#     					  date_time_value(year, DT, Ano),
#                           Ano < 2004,
#                           fabricantesQueVendemMundialmente(Fabricante),
#     					  \+carroAntigo(Modelo).

# decadaDeLancamentoDoCarro(Modelo, 1940) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum < 1950.
# decadaDeLancamentoDoCarro(Modelo, 1950) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 1950,
#     										AnoNum < 1960.
# decadaDeLancamentoDoCarro(Modelo, 1960) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 1960,
#     										AnoNum < 1970.
# decadaDeLancamentoDoCarro(Modelo, 1970) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 1970,
#     										AnoNum < 1980.
# decadaDeLancamentoDoCarro(Modelo, 1980) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 1980,
#     										AnoNum < 1990.
# decadaDeLancamentoDoCarro(Modelo, 1990) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 1990,
#     										AnoNum < 2000.
# decadaDeLancamentoDoCarro(Modelo, 2000) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 2000,
#     										AnoNum < 2010.
# decadaDeLancamentoDoCarro(Modelo, 2010) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 2010,
#     										AnoNum < 2020.
# decadaDeLancamentoDoCarro(Modelo, 2020) :- 	distinct([Modelo], (carros(Modelo, _, Ano))),
#     										date_time_value(date, DT, Ano),
#     									 	date_time_value(year, DT, AnoNum),
#     										AnoNum >= 2020.

# % se então (->)
# % verificar se determinado modelo foi lançado no ultimo ano
# novoModelo(Modelo) :-  	distinct([Modelo], carros(Modelo, _, AnoLancamento)),
#     					date_time_value(date, DT, AnoLancamento),
#     					date_time_value(year, DT, AnoNum),
#     					(/*if*/ AnoNum == 2024
#                        	/*then*/ -> true;
#                         /*else*/ false).

# % quantidade de fabricantes por país
# qtdFabricantesPorPais(Pais, QtdFabricantes) :- 	distinct([Pais], (fabricanteDeCarros(_,_,Pais,_))),
#     											aggregate_all(count, (fabricanteDeCarros( _, _, Pais, _)), QtdFabricantes).


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%% CONSULTAS PRE-DEFINIDAS %%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# /** <examples>

# ?- carros(Modelo, Classe, Ano).
# ?- carros(Modelo, Classe, date(2023,1,1)).
# ?- carros("Lamborghini Aventador", Classe, Ano).

# ?- carroAntigo(Modelo).
# ?- carroAntigo("Fiat 1100").
# ?- carroAntigo("Toyota Corolla (E210)").

# ?- carrosBusca("Corolla", Modelo, Classe, Ano).
# ?- carrosBusca("Lamborghini", Modelo, Classe, date(2020,1,1)).

# ?- carrosFabricante(Modelo, Fabricante).
# ?- carrosFabricante(Modelo, "Fiat").
# ?- carrosFabricante("Cadillac Celestiq", Fabricante).

# ?- fabricanteDeCarros(Fabricante, AnoFundacao, Localizacao, AreaServida).
# ?- fabricanteDeCarros(Fabricante, date(2000,1,1), Localizacao, AreaServida).
# ?- fabricanteDeCarros(Fabricante, date(2000,1,1), "Japan", AreaServida).

# ?- qtdModelosFabricante(Fabricante, QtdCarros).
# ?- qtdModelosFabricante("Toyota", QtdCarros).

# ?- qtdModelosFabricante30s(Fabricante, QtdCarros).
# ?- qtdModelosFabricante30s("Volkswagen", QtdCarros).
# ?- qtdModelosFabricante30s("BYD Auto", QtdCarros). %retorna falso por que essa nao é uma fabricante fundada e
# na década de 30

# ?- fabricantesQueVendemMundialmente(Fabricante).
# ?- fabricantesQueVendemMundialmente("BMW").
# ?- fabricantesQueVendemMundialmente("Arcfox").
# ?- fabricantesQueVendemMundialmente("Chevrolet"). % não serve "Worldwide", mas serve mais de 4 lugares diferentes, e retorna 'true'

# ?- carrosConcorrentes(Modelo1, Modelo2, Classe).
# ?- carrosConcorrentes("Toyota Corolla (E210)", Modelo, Classe).
# ?- carrosConcorrentes("BYD e2", Modelo, Classe).
# ?- carrosConcorrentes(Modelo1, Modelo2, "Compact car").

# ?- carroConfiavel(Modelo).
# ?- carroConfiavel("Toyota RAV4").

# ?- decadaDeLancamentoDoCarro(Modelo, Decada).
# ?- decadaDeLancamentoDoCarro("Toyota RAV4", Decada).
# ?- decadaDeLancamentoDoCarro(Modelo, 2000).

# ?- novoModelo(Modelo).
# ?- novoModelo("Toyota RAV4").
# ?- novoModelo("Cadillac Celestiq").

# ?- qtdFabricantesPorPais(Pais, QtdFabricantes).
# ?- qtdFabricantesPorPais("Japan", QtdFabricantes).

# */
