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

def carros_fabricante(car_data, modelo=None, fabricante=None):
    carros_fabricantes = {car['model']: car['manufacturer'] for car in carros(car_data)}

    if modelo is not None:
        return carros_fabricantes.get(modelo)
    elif fabricante is not None:
        return [modelo for modelo, fab in carros_fabricantes.items() if fab == fabricante]
    else:
        return carros_fabricantes

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
# # 2.2 Consulta fechada: um carro antigo específico (exemplo: Fiat 1100 (True) e Lamborghini Aventador (False))
# print(carro_antigo(CARS_DATA, 'Fiat 1100'))
# print(carro_antigo(CARS_DATA, 'Lamborghini Aventador'))

# # 3. Consultas relacionadas a busca de carros (consulta aberta não faz sentido aqui):
# # 3.1 Consulta fechada: busca carros que contenham o termo da busca no nome do modelo (ex: 'Corolla')
# print(carros_busca(CARS_DATA, 'Corolla'))
# # 3.2 Consulta fechada: Consulta por modelo "Lamborghini" lançado em 2020
# print(carros_busca(CARS_DATA, 'Lamborghini', ano=2020))

# # 4. Consultas relacionadas a carros e seus respectivos fabricantes
# # 4.1 Consulta aberta: Retorna todos os modelos e seus fabricantes
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
# print(decada_de_lancamento_do_carro(CARS_DATA))
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