Librairie CAErp pour la gestion des encaissements
======================================================

NB : À parir de la version 2.0, cette librairie ne supporte plus python 2

Cette librairie a pour objectif de fournir un ensemble cohérent pour la gestion
des encaissements, ce afin de répondre aux exigences de la loi de finance 2018.
Le texte suivant `http://bofip.impots.gouv.fr/bofip/10691-PGP` décrit plus en
détail le besoin à couvrir

Elle fonctionne comme suit :

- Les opérations d'encaissement sont effectuées au travers d'une API publique
- Pour chaque opération d'encaissement, une entrée est écrite dans le journal

Le journal est le garant de l'intégrité des opérations d'encaissement.

Activation du module
---------------------

L'api publique est configurable dans CAErp au travers du fichier de
configuration .ini.

Assurez-vous que la librairie caerp_payment est bien dans les caerp.includes

.. code-block:: console

   caerp.includes = ...
                      ...
                      caerp_payment

Configurez le service caerp.interfaces.IPaymentRecordService

.. code-block:: console

   caerp.interfaces.IPaymentRecordService = caerp_payment.public.PaymentService

Configurez les journaux de 'caerp_payment'. Voir la documentation sur le module
python logging pour le détail : https://docs.python.org/2/library/logging.html
ainsi que les exemples dans le fichier development.ini.sample.


Configurez le service de journalisation
caerp_payment.interfaces.IPaymentRecordHistoryService à utiliser.

caerp_payment propose deux services de journalisation


   HistoryLogService : Service par défaut, prévu pour le mode développement, se
   content de journaliser les actions sans détails.

   HistoryDBService : Journalise les actions effectuées dans une base de données
   spécifiques (pas forcément sur le même serveur mysql)

HistoryDBService
------------------

Pour activer la journalisation détaillée dans une base de données spécifiques
ajouter la ligne suivante dans la section [app:caerp] du fichier .ini

.. code-block:: console

   caerp_payment.interfaces.IPaymentRecordHistoryService = caerp_payment.history.caerp_payment.history.HistoryDBService

Créer une nouvelle base de données, vous pouvez utiliser l'utilitaire
./tools/add_payment_database.sh fournit dans le repository caerp.

.. code-block:: console

   cd caerp/
   ./tools/add_payment_database.sh
   # Suivez les instructions

Puis saisissez les informations de connexion de la nouvelle base de données dans
la section [app:caerp] du fichier .ini

.. code-block:: console

   caerp_payment_db.url = mysql://caerp_payment:caerp_payment@localhost/caerp_payment?charset=utf8


Archivage
-----------

Afin de certifier l'historique des actions sur les encaissements, caerp_payment
permet l'utilisation d'un service d'archivage.

Version locale, ajouter la ligne suivante à la configuration .ini du service
caerp dans la section [app:caerp]

.. code-block:: console

    caerp_payment.interfaces.IPaymentArchiveService=caerp_payment.archive.FileArchiveService
    caerp_payment_archive_storage_path=<chemin sur disque pour le stockage des journaux>

La version locale fournie une solution acceptable de certification des journaux
d'encaissement.

Afin d'obtenir une solution plus endurcie, on préfèrera l'utilisation d'un
service distant avec un tiers certifié.


Une configuration complète contient donc les informations suivantes


.. code-block::

    caerp.includes =
                ....
                caerp_payment

    # Accès à la bdd de traitement des paiements
    caerp_payment_db.url = mysql://caerp_payment:caerp_payment@localhost/caerp_payment?charset=utf8

    # Le service qui sera utilisé depuis caerp pour agir sur les encaissements
    caerp.interfaces.IPaymentRecordService = caerp_payment.public.PaymentService

    # Le service qui sera utilisé par caerp_payment pour stocker l'historique des actions d'encaissement
    caerp_payment.interfaces.IPaymentRecordHistoryService = caerp_payment.history.HistoryDBService

    # Le service en charge de la génération d'une archive avec un peu de certification d'intégrité des journaux
    caerp_payment.interfaces.IPaymentArchiveService = caerp_payment.archive.FileArchiveService

    # Le chemin utilisé par le service d'archivage pour le stockage sur disque
    caerp_payment_archive_storage_path = /var/caerp/files/treasury/payment_storage


Consultation des journaux
--------------------------

Si le service HistoryDBService est utilisé, caerp_payment ajoute automatiquement
une entrée dans le menu Comptabilité d'CAErp permettant la consultation du
journal des modifications apportées aux encaissements.
