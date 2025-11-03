
1- Afegeixo model, data  i View per res_config sttings per tal que es puguin emmagatzemar variables a nivel lde companyia 
* usuari 
* password 
* producte per importacions
* impost usat per defecte (entenc que quasi sempre serà el IVA 21 però que ho seleccioni cada companyia.)
* instància: url del coopcycle a sincronitzar
* maxim dies per obtenir la informació de Coopccycle

2- Afegeixo camp a sale order que em digui si prové d'una importació de coopcycle

3- Afegeixo camp a sale order line per mantenir la línia de Coopcycle que s'ha carregat. Compte. seria el "order_number" associat a la instància.
Vull dir la instància de mensakas pot tenir el orderID "ORD-0001" que correspon a un enviament.
La instància lacleta (lacleta.coopcycle.org) pot tenir també un ORD-0001 que correspon a un altre enviament.
PEr tant a aquest id hem d'emmagatzemar la concatenació dels dos valors: la instància i la "order_number"

4 - No crec que el Binding ens aporti res. Tot plegat es pe rtenir diferents connectors per un sola instància. Més aviat ens molesta ja que volem tenir un per companyia i que siguin excloents entre ells

- per tant em sobra el coopcycle_binding.py

5- El partner.py actual té molta pellofa que no em serveix i altres coses que no sé ni de què van.

- per tant el substitueixo per el res_partner.py que és on hi haurà el conjunt de procés

En ell hi haurà:

El nou identificador de partner: coopcycle_bind_id
Aquest camp caldrà


A - @api-model: update_partners_list : S'encarrega de crear els partners que no existeixin a Odoo per tal de tenir-los identificats
- Càrrega de tots els shop_id endpoint: api/stores (compte paginació)
- Per cadascun mmira si tè línies de venda
    - Si en té mira si hi ha un res_partner amb aquest coopcycle_bind_id
        - Si no hi comencem a buscar partner, primer per nom i si no per email
            - Si el trobem perfecte li informem el coopcycle_bind_id
            - Si no creem un res partner amb la info de coopcycle


B- get_unprocessed_order_lines(partner_id) : Obté totes les línies processed d'un determinat partner (a trvés del endpoint )
Cridem el endpoint: /api/invoice_line_items/export/odoo amb els filtres de dates que ja tenim (avui-) 
- PEr cada una comparem si hi ha cap sale_order_line si ja té informat aquell codi
    - Si ja hi és no fem res.
    - Si no mirem si hem creat comanda per aquell partner
        - Si cal la creem 
        - Afegim la linia a la comanda.


6- És important que en la fusió de dos contactes es fusioni el id de Coopcycle. PEr aquest mtiu cal el codi de base_partner_merge.py

7- el mètode cron_import_sale_orders (no sé si cridarà un mètode de partner o si ho fara ell):
Obtindrà tots els partners amb comandes a Coopcycle:
- Crida a update_partners_list
- Obtenció de tots els partners amb el Id de coopcycle informat
- Per cadascun, crida a get_unprocessed_order_lines



### Resumint: 
- data: 
    - default_coopcycle_product: Afegeix el producte per defecte que usarem per les importacions de Coopcycle
    - ir_cron: Crea el cron 
- models:
    - base_partner_merge : permet que quan fusionem dos partners es mantingui el Id de Coopcycle
    - coopcycle_backend :cal definir bé les crides que fan falta. Tu ens saps més que jo.
    - coopcycle_bindings : No sé realment si el fem servir per res, no tenim comunicació bidireccional. Jo faria neteja i deixem només allào ue ens interessi (entenc que encapsular les crides a Coopcycle o potser ni això) Em preoucpa perque bàsicament està pensat per que cada instància tingui n connectors del mateix tipus (tot i que les connexions es llegeixen des de variables d'entorn!). En el nostre cas necessitem un sol connector per companyia així que no és el nostre cas. Evaluem-ne la necessitat i idoneitat.
    - exceptions: només veig que pot fer més mal que bé (de fet crec que és el motiu pel que no veiem els errors de sinergiacrm).
    - partner : Tot i que potser podem reciclar alguna cosa de codi crec que cal plantejar-ho d'una manera diferent. he creat el res_partner per substituir-lo
    - res_config_settings: Tota la configuració l'hem de fer a partir de interfície! res de variables d'entorn! I ha de ser company_dependant.
    - res_partner: On hi ha tota la guerra (el comentari 5 i segurament alguna cosa més). 
    - Sale order: afegim un camp a sale order per saber si ve de importació i un a sale_order_line per saber de quina línia de Coopcycle ve.
. Vistes:
    - res config: fer que es pugui modificar la configuració
    - slae_order: potser no és necessari però podria ser interessant fer que es pugui visualitzar el camp de id de Coopcycle en la comanda. No hi dediquem més de 10 minuts, si es complica, fora.

### Estrany:
Fent proves sobre la Api m'ha extranyat que una mateixa consulta a:
- /api/invoice_line_items/export/odoo
- /api/invoice_line_items/export
Amb els mateixos filtres em retornen una quantitat diferent de línies (26 en el primer cas i 19 en el segon). Si anem avançant i veiem coses rares preguntem al Paul.


### Pendents

- Fer aparèixer labels al Config settings i un icon al menu
- Tota la informació de connexió (API URL, password, ...) treure-la per config parameters
- Informar camps de sale order line (preu (via api) i impost (via param))
- Activar base partner merge
- Buscar si ja existeix el partner i si existeix, informar només el coopcycle bind id
