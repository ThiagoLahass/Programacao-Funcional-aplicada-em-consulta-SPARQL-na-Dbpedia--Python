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
def getResults(results):
    VALUES = results['results']['bindings']
    return list( map ( lambda item: dict( map ( lambda key: (key, item[key]['value']), item.keys() )), VALUES) )

# Função para buscar carros pelo nome exato
def busca_carro_por_nome_exato(car_data, name):
    return list( filter( lambda car: car['model'] == name , car_data ) )

# Função para buscar carros por parte do nome
def busca_carro_por_nome_contem(car_data, name):
    return list( filter( lambda car: car['model'].__contains__(name) , car_data ) )

def carros(car_data, modelo=None, classe=None, ano=None):
    # Filtragem por modelo, classe e data
    carros_filtrados = []
    for car in car_data:
        if (not modelo or car['model'] == modelo) and \
           (not classe or car['class'] == classe) and \
           (not ano or int(car['yearCar'][:4]) == ano):
            #TO-DO: lembrar de mudar 'yearCar': car['yearCar'] para 'yearCar': int(car['yearCar'][:4]) caso seja conveniente
            carros_filtrados.append({'model': car['model'], 'class': car['class'], 'yearCar': car['yearCar'], 'manufacturer': car['manufacturer']})
    return carros_filtrados

# Função para verificar se um carro é antigo (default=1960)
def carro_antigo(car_data, car_name=None, threshold_year=1960):
    if car_name is None:
        # Consulta aberta: retorna todos os carros antigos (lançados antes de 1960)
        return list( filter(lambda car: int(car['yearCar'][:4]) < threshold_year, carros(car_data)) )
    else:
        # Consulta fechada: retorna True se o carro específico é antigo, False caso contrário
        return reduce(lambda result, car: result or (int(car['yearCar'][:4]) < threshold_year and car['model'] == car_name), car_data, False) 

def carros_busca(car_data, termo_busca, classe=None, ano=None):
    filtered_cars = []
    for car in carros(car_data):
        if termo_busca in car['model'] and \
                (classe is None or car['class'] == classe) and \
                (ano is None or int(car['yearCar'][:4]) == ano):
            filtered_cars.append(car)
    return filtered_cars

# ESTÁ CORRETO FAZER DESSA FORMA?
def carros_fabricante(car_data, modelo=None, fabricante=None):
    carros_fabricantes = {car['model']: car['manufacturer'] for car in carros(car_data)}

    if modelo is not None:
        return carros_fabricantes.get(modelo)
    elif fabricante is not None:
        return [modelo for modelo, fab in carros_fabricantes.items() if fab == fabricante]
    else:
        return carros_fabricantes

# É PERMITIDA ESSA IMPLEMENTAÇÃO ???????
def fabricante_de_carros(car_data, fabricante=None, ano_fundacao=None, pais=None, area_servida=None):
    fabricantes = {car['manufacturer']: {'foundingYear': car['foundingYear'], 'manufacturerCountry': car['manufacturerCountry'], 'areaServed': car['areaServed']} for car in car_data}
    
    # Filtragem por fabricante
    if fabricante is not None:
        fabricantes = {fabricante: fabricantes.get(fabricante)} if fabricante in fabricantes else {}
    
    # Filtragem por ano de fundação
    if ano_fundacao is not None:
        fabricantes = {fabricante: info for fabricante, info in fabricantes.items() if int(info['foundingYear'][:4]) == ano_fundacao}
    
    # Filtragem por país
    if pais is not None:
        fabricantes = {fabricante: info for fabricante, info in fabricantes.items() if info['manufacturerCountry'] == pais}
    
    # Filtragem por área servida
    if area_servida is not None:
        fabricantes = {fabricante: info for fabricante, info in fabricantes.items() if area_servida in info['areaServed']}
    
    return fabricantes

# Função para contar a quantidade de modelos fabricados por um fabricante
def qtd_modelos_fabricante(car_data, fabricante=None):
    carros_fabricantes = carros_fabricante(car_data)

    if fabricante is None:
        # Consulta aberta: retorna a lista com as quantidades de cada fabricante
        return reduce(lambda count_dict, modelo: {**count_dict, modelo: count_dict.get(modelo, 0) + 1}, carros_fabricantes.values(), {})
    else:
        # Consulta fechada: retorna a quantidade de modelos do fabricante especificado
        return sum(1 for modelo, fab in carros_fabricantes.items() if fab == fabricante)

# TO-DO: Verificar por que está dando alguns valores maiores aqui em comparação a quando aplica só "qtd_modelos_fabricante"
# Função para contar a quantidade de modelos de fabricantes cujo ano de fundação seja na década de 1930
def qtd_modelos_fabricante_30s(car_data, fabricante=None):
    carros_decada = [car for car in car_data if 1930 <= int(car['foundingYear'][:4]) < 1940]
    return qtd_modelos_fabricante(carros_decada, fabricante)
        
# Função para verificar se um fabricante fornece carros mundialmente
def fabricantes_que_vendem_mundialmente(car_data, fabricante=None):
    if fabricante == None:
        # Consulta aberta: retorna todos os fabricantes que servem mundialmente
        fabricantes_mundiais = set() # remove duplicatas
        for car1 in car_data:
            if "Worldwide" in car1['areaServed']:
                fabricantes_mundiais.add(car1['manufacturer'])
            elif len(set(car['areaServed'] for car in car_data if car1['manufacturer'] == car['manufacturer'])) > 4:
                fabricantes_mundiais.add(car1['manufacturer'])
        return list(fabricantes_mundiais)
    else:
        # Consulta fechada: verifica se um fabricante específico serve mundialmente
        filtered = list(filter(lambda car: car['manufacturer'] == fabricante, car_data))
        if not any("Worldwide" in car['areaServed'] for car in filtered):
            return len(set(car['areaServed'] for car in filtered)) > 4
        return True if any("Worldwide" in car['areaServed'] for car in filtered) else False

# Função para encontrar carros concorrentes (classe só é usada caso não seja passado nenhum modelo)
def carros_concorrentes(car_data, modelo1=None, modelo2=None, classe=None):
    car_data = carros(car_data)
    if modelo1 is None and modelo2 is None:
        if classe is None:
            # Consulta aberta: retorna todos os modelos concorrentes
            concorrentes = set()   # Remove duplicatas
            for car1 in car_data:
                for car2 in car_data:
                    if car1 != car2 and car1['manufacturer'] != car2['manufacturer'] and \
                            car1['class'] == car2['class'] and car1['yearCar'] == car2['yearCar']:
                        concorrentes.add((car1['model'], car2['model']))
            return list(concorrentes)
        else:
             # Consulta aberta mas classe definida: retorna todos os modelos concorrentes da classe escolhida
            concorrentes = set()   # Remove duplicatas
            for car1 in car_data:
                for car2 in car_data:
                    if car1 != car2 and car1['class'] == classe and car2['class'] == classe and \
                        car1['manufacturer'] != car2['manufacturer'] and car1['yearCar'] == car2['yearCar']:
                        concorrentes.add((car1['model'], car2['model']))
            return list(concorrentes)

    elif modelo1 is not None and modelo2 is None:
        # Consulta semi-aberta: retorna modelos concorrentes ao modelo1
        concorrentes_modelo1 = set() # remove duplicatas
        modelo1 = busca_carro_por_nome_exato(car_data, modelo1)
        for car in car_data:
            if car['class'] == modelo1[0]['class'] and car['manufacturer'] != modelo1[0]['manufacturer'] and \
                    modelo1[0]['yearCar'] == car['yearCar']:
                concorrentes_modelo1.add(car['model'])
        return concorrentes_modelo1

    else:
        # Consulta fechada: verifica se os modelos são concorrentes
        car1 = busca_carro_por_nome_exato(car_data, modelo1)
        car2 = busca_carro_por_nome_exato(car_data,modelo2)
        if not car1 or not car2:
            return False
        return car1[0]['manufacturer'] != car2[0]['manufacturer'] and \
               car1[0]['class'] == car2[0]['class'] and car1[0]['yearCar'] == car2[0]['yearCar']

# Função para verificar carros confiáveis
def carro_confiavel(car_data, modelo=None):
    if modelo is None:
        # Consulta aberta: retorna todos os modelos confiáveis
        confiaveis = set() # remove duplicatas
        for car in car_data:
            if int(car['foundingYear'][:4]) <= 2004 and fabricantes_que_vendem_mundialmente(car_data, car['manufacturer']) and not carro_antigo(car_data, car_name=car['model']):
                confiaveis.add(car['model'])
        return confiaveis

    else:
        # Consulta fechada: verifica se um modelo específico é confiável
        car = list(filter(lambda car: car['model'] == modelo, car_data))
        if not car:
            return False
        car = car[0]
        if int(car['foundingYear'][:4]) <= 2004 and fabricantes_que_vendem_mundialmente(car_data, car['manufacturer']) and not carro_antigo(car_data, car_name=car['model']):
            return True
        return False

# Função para obter a década de lançamento de um carro
def decada_de_lancamento_do_carro(car_data, modelo=None, decada=0):
    if modelo is None:
        if decada == 0:
            # Consulta aberta: retorna todos os modelos com suas respectivas décadas de lançamento
            modelos_decada = set()
            for car in carros(car_data):
                year = int(car['yearCar'][:4])
                modelos_decada.add((car['model'], year - (year % 10)))
            return modelos_decada
        else:
            # Consulta semi-aberta: retorna todos os carros lançados na década especificada
            carros_decada = set()
            for car in carros(car_data):
                year = int(car['yearCar'][:4])
                if year - (year % 10) == decada:
                    carros_decada.add(car['model'])
            return carros_decada

    else:
        # Consulta fechada: retorna a década de lançamento do modelo específico
        car_modelo = next((car for car in carros(car_data) if car['model'] == modelo), None)
        if car_modelo:
            year = int(car_modelo['yearCar'][:4])
            return year - (year % 10)
        else:
            return None
    
def novo_modelo(car_data, modelo=None, current_year=2024):
    if modelo is None:
        # Consulta aberta: retorna todos os modelos novos
        modelos_novos = set()
        for car in carros(car_data):
            if int(car['yearCar'][:4]) == current_year:
                modelos_novos.add(car['model'])
        return modelos_novos
    else:
        # Consulta fechada: verifica se o modelo específico foi lançado no último ano
        cars_modelo = list(filter(lambda car: car['model'] == modelo, carros(car_data)))
        if not cars_modelo:
            return False
        car = cars_modelo[0]
        return int(car['yearCar'][:4]) == current_year

def qtd_fabricantes_por_pais(car_data, pais=None):
    fabricantes_paises = {car['manufacturer']: car['manufacturerCountry'] for car in car_data}
    if pais is None:
        return {pais: list(fabricantes_paises.values()).count(pais) for pais in set(fabricantes_paises.values())}
    else:
        return list(fabricantes_paises.values()).count(pais)
    
# =======================================================================================
# ======================================== REGRAS =======================================
# =======================================================================================


# =======================================================================================
# ====================================== CONSULTAS ======================================
# =======================================================================================

# Pegando os resultados e "limpando eles"
CARS_DATA = getResults(RESULTS)

# # 0. Consultando todos os dados obtidos:
# print(CARS_DATA)

# # 1. Consultas relacionadas aos carros:
# # 1.1 Consulta aberta: todos os carros:
# print(carros(CARS_DATA))
# # 1.2 Consulta semi-aberta: carros lançados em um ano (ex: 2023)
# print(carros(CARS_DATA, ano=2023))
# # 1.3 Consulta semi-aberta: carros de uma determinada classe e ano (ex: Compact crossover SUV em 2020)
# print(carros(CARS_DATA, classe='Compact crossover SUV', ano=2020))
# # 1.4 Consulta fechada: um carro de modelo específico(ex: Toyota Corolla (E210))
# print(carros(CARS_DATA, modelo='Toyota Corolla (E210)'))

# # 2. Consultas relacionadas a carros antigos:
# # 2.1 Consulta aberta: todos os carros antigos
# print(carro_antigo(CARS_DATA))
#       MELHOR OPÇÃO ? (i.e aplicar a função "carros" antes de trabalhar os dados nessa função?)
#       SE SIM, É MELHOR CHAMAR A FUNÇÃO "carros(CARS_DATA)" aqui ou na própria função "carros_antigos"?
#       ACREDITO QUE DENTRO DA PRÓPIA FUNÇÃO, COMO ESTÁ IMPLEMENTADO ATÉ O MOMENTO
# print(carro_antigo(carros(CARS_DATA)))
# # 2.2 Consulta fechada: um carro antigo específico (exemplo: Fiat 1100 (True) e Lamborghini Aventador (False))
# print(carro_antigo(CARS_DATA, 'Fiat 1100'))
# print(carro_antigo(CARS_DATA, 'Lamborghini Aventador'))

# # 3. Consultas relacionadas a busca de carros (consulta aberta não faz sentido aqui):
# # 3.1 Consulta fechada: busca carros que contenham o termo da busca no nome do modelo (ex: 'Corolla')
# print(carros_busca(carros(CARS_DATA), 'Corolla'))                           #QUAL DAS DUAS OPÇÕES É A MAIS CORRETA?
# print(carros_busca(CARS_DATA, 'Corolla'))
# # 3.2 Consulta fechada: Consulta por modelo "Lamborghini" lançado em 2020
# print(carros_busca(carros(CARS_DATA), 'Lamborghini', ano=2020))             #QUAL DAS DUAS OPÇÕES É A MAIS CORRETA?
# print(carros_busca(CARS_DATA, 'Lamborghini', ano=2020))

# # 4. Consultas relacionadas a carros e seus respectivos fabricantes
# # 4.1 Consulta aberta: Retorna todos os modelos e seus fabricantes
# print(carros_fabricante(CARS_DATA))                                         #QUAL DAS DUAS OPÇÕES É A MAIS CORRETA?
# # print(carros_fabricante(carros(CARS_DATA)))
# # 4.2 Consulta semi-aberta: Retorna todos os modelos do fabricante especificado
# print(carros_fabricante(CARS_DATA, fabricante='Fiat'))
# # 4.3 Consulta fechada: Retorna o fabricante do modelo especificado
# print(carros_fabricante(CARS_DATA, modelo='Cadillac Celestiq'))

# # 5. Consultas relacionadas a fabricantes de carros
# # 5.1 Consulta aberta: todos os fabricantes de carros
# print(fabricante_de_carros(CARS_DATA))
# # 5.2 Consulta semi-aberta: fabricantes com localização específica
# print(fabricante_de_carros(CARS_DATA, pais='Japan'))
# # 5.3 Consulta semi-aberta: fabricantes fundados em 2000, com localização específica
# print(fabricante_de_carros(CARS_DATA, ano_fundacao=2000, pais='Japan'))
# # 5.4 Consulta semi-aberta: fabricantes fundados em 1937, com localização específica e área de serviço mundial
# print(fabricante_de_carros(CARS_DATA, ano_fundacao=1937, pais='Japan', area_servida="Worldwide") )

# # 6. Consultas relacionadas a quantidade de modelos lançados por fabricante
# # 6.1 Consulta aberta: quantidade de modelos fabricados por cada fabricante
# print(qtd_modelos_fabricante(carros(CARS_DATA)))
# # 6.2 Consulta fechada: quantidade de modelos fabricados por um fabricante (ex: Toyota)
# print(qtd_modelos_fabricante(carros(CARS_DATA), 'Toyota'))

# # 7. Consultas relacionadas a quantidade de modelos lançados por fabricantes fundadas na década de 1930
# # 7.1 Consulta aberta: quantidade de modelos fabricados por cada fabricante
# print(qtd_modelos_fabricante_30s(CARS_DATA))
# # 7.2 Consulta fechada: quantidade de modelos fabricados por um fabricante (ex: Toyota)
# print(qtd_modelos_fabricante_30s(CARS_DATA, 'Toyota'))
# print(qtd_modelos_fabricante_30s(CARS_DATA, 'BYD Auto')) # (retorna 0 pois não é fundada na decada de 1930)

# # 8. Consultas relacionadas a fabricantes servirem mundialmente
# # 8.1 Consulta aberta: todos os fabricantes que servem mundialmente
# print(fabricantes_que_vendem_mundialmente(CARS_DATA))
# # 8.2 Consulta fechada: verificar se um fabricante específico serve mundialmente(ex: Toyota)
# print(fabricantes_que_vendem_mundialmente(CARS_DATA, 'Toyota'))
# # 8.3 Consulta fechada: verificar se um fabricante específico serve mundialmente(ex: Chevrolet que nao é "Worldwide" mas serve em mais de 4 lugares)
# print(fabricantes_que_vendem_mundialmente(CARS_DATA, 'Chevrolet'))

# # 9. Consultas relacionadas a carros concorrentes
# # 9.1 Consulta aberta: Todos os modelos concorrentes:
# print(carros_concorrentes(CARS_DATA))
# # 9.2 Consulta aberta mas com classe definida: Todos os modelos concorrentes da classe escolhida (ex: Compact crossover SUV)
# print(carros_concorrentes(CARS_DATA, classe='Compact crossover SUV'))
# # 9.3 Consulta semi-aberta: modelos concorrentes ao modelo1 (ex: Toyota Corolla (E210))
# print(carros_concorrentes(CARS_DATA, 'Toyota Corolla (E210)'))
# # 9.4 Consulta fechada: verificar se dois modelos são concorrentes (ex: Toyota Corolla (E210) e Toyota Camry)
# print(carros_concorrentes(CARS_DATA, 'Toyota Corolla (E210)', 'Toyota Camry'))

# # 10. Consultas relacionadas a carros confiáveis
# # 10.1 Consulta aberta: todos os modelos confiáveis
# print(carro_confiavel(CARS_DATA))
# # 10.2 Consulta fechada: verificar se um modelo específico é confiável (ex: Toyota RAV4)
# print(carro_confiavel(CARS_DATA, 'Toyota RAV4'))

# # 11. Consultas relacionadas a décadas de lançamento dos carros
# # 11.1 Consulta aberta: todos os modelos com suas respectivas décadas de lançamento
# # ==== MAIS UMA VEZ: QUAL DAS DUAS OPÇÕES É A MAIS CORRETA? ====
# print(decada_de_lancamento_do_carro(CARS_DATA))
# print(decada_de_lancamento_do_carro(carros(CARS_DATA)))
# # 11.2 Consulta semi-aberta: todos os carros lançados na década especificada (ex: 2000)
# print(decada_de_lancamento_do_carro(CARS_DATA, decada=2000))
# # # 11.3 Consulta fechada: década de lançamento do modelo específico (ex: Toyota Corolla (E210))
# print(decada_de_lancamento_do_carro(CARS_DATA, modelo='Toyota Corolla (E210)'))

# # 12. Consultas relacionadas a novos modelos de carro lançados (i.e. ano de lançamento seja o ano atual (default 2024, mas pode ser alterado))
# # 12.1 Consulta aberta: todos os modelos novos
# print(novo_modelo(CARS_DATA))
# # 12.2 Consulta fechada: verifica se um modelo específico foi lançado no último ano (ex: 'Toyota RAV4' e 'Cadillac Celestiq')
# print(novo_modelo(CARS_DATA, 'Toyota RAV4'))
# print(novo_modelo(CARS_DATA, 'Cadillac Celestiq'))

# # 13. Consultas relacionadas a quantidade de fabricantes por país
# # 13.1 Consulta aberta: quantidade de fabricantes por país
# print(qtd_fabricantes_por_pais(CARS_DATA))
# # 13.2 Consulta fechada: quantidade de fabricantes no país específico (exemplo: 'Japan')
# print(qtd_fabricantes_por_pais(CARS_DATA, 'Japan'))

# =======================================================================================
# ====================================== CONSULTAS ======================================
# =======================================================================================





# =======================================================================================
# =================== PROGRAMA EM PROLOG PARA COMPARAÇÕES E ANALISES ====================
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
#     					    date_time_value(year, DT, Ano),
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

# =======================================================================================
# =================== PROGRAMA EM PROLOG PARA COMPARAÇÕES E ANALISES ====================
# =======================================================================================