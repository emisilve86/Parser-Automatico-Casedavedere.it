# Parser Automatico di Annunci Immobiliari su Casesavedere.it #

----------

## Perché? ##

Molte applicazioni e motori di ricerca di annunci immobiliari già offrono all'utente la possibilità di effettuare ricerche con filtri avanzati, per poi notificare puntualmente l'utente, tramite email e/o notifica *push*, dell'inserimento di nuovi annunci che soddisfano i criteri di ricerca inseriti. E' questo il caso dei ben noti `Idealista`, `Immobiliare.it`, `Casa.it`, ecc.

Ad ogni modo, sono solito consultare anche un'altra piattaforma sul Web molto utilizzata da privati e agenzie immobiliari che operano sul mio territorio. Si tratta di [`Casedavedere.it`](https://www.casedavedere.it/) che offre all'utente una semplice *form* di ricerca con alcuni campi quali, ad esempio, la provincia, il comune, il prezzo massimo, i metri quadri, e pochi altri criteri di base.

D'altro canto, questa piattaforma non permette di filtrare per <u>numero di locali</u>, <u>piani intermedi</u>, <u>presenza di box</u>/<u>garage</u>, <u>numero minimo di balconi</u> e <u>ascensore</u>. Alcune informazioni che vorrei poter avere filtrate nella mia ricerca, ma che attualmente è possibile solo capire aprendo il *link* di ogni singolo annuncio presente nel risultato di una ricerca che include centinaia di anteprime distribuite tra decine di pagine da navigare in sequenza.

Inoltre, la piattaforma Web in questione non offre l'iscrizione ad alcun tipo di *newsletter* che possa permettere all'utente interessato di ricevere aggiornamenti in merito ai più recenti annunci inseriti che soddisfino il filtro impostato. Ad aggravare tale carenza, c'è poi la difficoltà nel poter discernere i vecchi dai nuovi annunci, in quanto le anteprime delle ricerche effettuate non sono sempre presentate nello stesso ordine.

Per superare tali limitazioni, ho deciso di sviluppare uno *script* Python (>=3.6) che implementa un <u>*parser* con filtro avanzato</u> che può essere facilmente configurato per esplorare gli annunci di immobili presenti in <u>più di un comune e provincia</u>, e che permette di <u>ricevere notifiche tramite email</u> contenenti nel corpo le anteprime degli annunci immobiliari che soddisfano i criteri di ricerca inseriti, ma non ancora notificati in passato. Lo *script* può essere quindi lanciato in modo programmatico come *task* di Cron per <u>eseguire automaticamente</u> in background ad intervalli di tempo determinati.

> **Nota**.
> Clonando questo repository viene clonato in locale tutto il sorgente necessario a lanciare il *parser*. In ogni caso, sarà necessario seguire alcuni step fondamentali per preparare l'ambiente a funzionare correttamente e che viene spiegato nel seguito.

----------

## Come? ##

Come prima cosa, è necessario verificare di avere installato Python3 sul proprio sistema. Sono poi necessari i seguenti moduli Python per poter lanciare lo script: `os`, `re`, `json`, `socket`, `validators`, `http`, `base64`, `datetime`, `bs4` e `email`.

Molti di questi saranno già disponibili nell'ambiente base una volta installato Python, mentre altre dovranno essere installate manualmente, ad esempio, tramite il *package installer* di Python `pip`.

Inoltre, per permettere a questa applicazione di inviare le email in maniera programmatica, dovranno essere installati anche i seguenti moduli

> ```pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib```

Ad ogni modo, per utilizzare i servizi offerti tramite API Google, è necessario creare prima un progetto Google Cloud Platform come spiegato a questo [link](https://developers.google.com/workspace/guides/create-project), per poi creare anche le credenziali per applicazioni desktop come spiegato a questo secondo [link](https://developers.google.com/workspace/guides/create-credentials). Quest'ultimo step è indispensabile per l'autenticazione e quindi l'utilizzo dei servizi offerti tramite API di Google.

> **Nota**.
> Tenere bene a mente che, per poter inviare email sfrutando le apposite API, bisogna specificare i seguenti ambiti all'atto della creazione delle credenziali

> ```.../auth/gmail.compose```	--- *(Gestire le bozze e inviare le email)*

> ```.../auth/gmail.readonly```	--- *(Visualizzare le tue email e impostazioni)*

Una volta completati i passi descritti nei due link riportati sopra, sarà possibile scaricare un file `credential.json` che deve essere inserito nella stessa directory dove risiede lo *script* `CaseDaVedere.py`.

A questo punto abbiamo tutto, e possiamo procedere con la configurazione vera e propria dell'applicazione. Dobbiamo innanzitutto specificare gli indirizzi di posta ai quali si desidera inviare le email. Per fare questo basta inserire uno o più indirizzi di posta elettronica all'interno del file `email_list.json`, all'interno della lista puntata dalla chiave `"email"`, come mostrato sotto

> ```json
> "email" : [
> 	"esempio1@serv.it",
> 	"esempio2@serv.it",
> 	...
> ]
> ```

> **Nota**.
> Tenere presente che, se la lista rimane vuota, non verrà generata nessuna email, ma sarà sempre possibile consultare il file `casedavedere.html` che viene generato in maniera automatica dallo *script* e che contiene le anteprime di tutti gli annunci che soddisfano i criteri di ricerca impostati.

I campi da aggiornare per impostare il filtro desiderato sono tutti inclusi nel file `property_filter.json` che sono impostati di base a valori di default. Questi sono

> `min_area` : un valore intero che rappresenta la superficie minima in metri quadri dell'immobile

> `max_area` : un valore intero che rappresenta la superficie massima in metri quadri dell'immobile

> `min_price` : un valore intero che rappresenta il prezzo minimo di vendita dell'immobile

> `max_price` : un valore intero che rappresenta il prezzo massimo che si intende sborsare per l'acquisto dell'immobile

> `intermediate_floor` : un booleano da impostare con il valore 0 o 1 per escludere o meno dalla ricerca tutti gli immobili siti all'ultimo piano ed al piano terra

> `min_rooms` : un valore intero che rappresenta il numero minimo di locali di cui deve essere dotato l'immobile

> `min_balconies` : un valore intero che rappresenta il numero minimo di balconi di cui deve essere dotato l'immobile

> `need_box` : un booleano da impostare con il valore 0 o 1 per includere tra i risultati della ricerca solo gli immobili venduti insieme ad un garage/box auto

> `need_elevator` : un booleano da impostare con il valore 0 o 1 per includere tra i risultati della ricarca solo gli immobili siti in stabili dotati di ascensore

Come ultima operazione, c'è da impostare la provincia ed il comune dove si sta cercando l'immobile da acquistare. Per fare questo bisogna aprire il file `provinces_and_municipalities.json` ed includere nell'insieme `SELECTED` uno o più liste e/o campi che rappresentano provincie e comuni tra quelli già presenti nell'insieme `ALL`.

----------

## Eseguire lo Script ##

Per eseguire lo script è sufficiente lanciare il seguente comando da *shell*

> ```sh
> python CaseDaVedere.py > /dev/null 2>&1
> ```

Se si omette il redirezionamento di `stdout` e `stderr` a `/dev/null`, lo *script* stampa a schermo la pagina della ricerca correntemente esplorata ed il codice dell'immobile correntemente parsato e che ha soddisfatto i requisiti della ricerca. Una volta completato, all'interno della working directory sarà poi possibile reperire ed aprire il file `casedavedere.html`. Se è stata poi impostato almeno un'indirizzo email, dovrà poter essere anche ricevuto un messaggio sulla relativa casella di posta.

> **Nota**.
> Non modificare o cancellare il file autogenerato `property_code.txt`, in quanto mantiene i codici degli immobili che soddisfano i criteri di ricerca impostati, e per i quali è già stata inoltrata la notifica a mezzo di posta elettronica e che non devono essere notificati una seconda volta.

----------

## Automatizzare lo Script ##

Su sistemi Linux-based è normalmente disponibile il servizio *cron* che altro non è che uno *scheduler* di *cron-jobs*. Questi ultimi possono essere un qualsivoglia eseguibile o *script* da lanciare ad intervalli di tempo ben definiti ed in accordo a determinate regole che possono essere specificate con la sintassi *cron*.

Se per esempio si vuole lanciare lo *script* ogni ora tra le 8:00 e le 20:00 nei soli giorni della settimana che vanno da lunedì a venerdì, è sufficiente eseguire da terminale `crontab -e` per aprire l'editor ed inserire in fondo la regola che segue

> ```sh
> 0 8-20 * * 1-5  cd /path/to/the/folder/containing/the/script  &&  python CaseDaVedere.py > /dev/null 2>&1
> ```

quindi salvare e chiudere il file.