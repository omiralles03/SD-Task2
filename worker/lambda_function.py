# La Lambda rebrà un JSON (esdeveniment) amb les dades del tiquet i ha de fer:

# 1.Artificial Delay (Requisit 4 obligatori): Clavar un time.sleep(0.1) (100 ms) a dins de la lògica abans d'executar el tiquet per simular la passarel·la de pagament.

# 2. Connexió a Base de Dades (Punt 3): Connectar-se al PostgreSQL que tenim corrent a la EC2 (necessitaràs les credencials del .env).

# 3. Lògica de Compra i Concurrència (Punt 2):

    # Si el tiquet és Unnumbered, fer un UPDATE restant 1 al total de tiquets disponibles (assegura't que no quedi en negatiu, No overselling).

    # Si és Numbered, fer un INSERT a una taula de seients ocupats. Si el seient ja existeix, controlar l'error per no vendre'l dos cops.

# 4. Mètriques (Punt 9 obligatori): Guardar a una taula de la Base de Dades (o un log) l'hora exacta d'inici i de finalització de cada transacció per 
# poder calcular després el Throughput real i la Latència (p50, p95, p99).


# Esto de aqui ns q porras es habra que mirarlo XD

#2. Configurar la connexió nativa a AWS (Event Source Mapping)

#. Com que el controlador només escala la concurrència des de fora per no saturar la xarxa, has de configurar a la consola d'AWS 
# (o afegir-ho al Terraform si t'atreveixes) el connector perquè AWS Lambda llegeixi directament de la nostra cua de RabbitMQ.

# El nom de la cua és ticket_queue.

# S'ha de configurar amb un Batch size gran perquè AWS buidi RabbitMQ en ràfegues quan hi hagi pics de càrrega.

# Posa't amb el fitxer a la carpeta worker/ i digue'm quan ho tinguis per fer el push a la branca main, ajuntar-ho tot i llançar el test de estrès definitiu!"
