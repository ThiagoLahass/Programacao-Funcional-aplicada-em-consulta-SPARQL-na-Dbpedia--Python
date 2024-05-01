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
