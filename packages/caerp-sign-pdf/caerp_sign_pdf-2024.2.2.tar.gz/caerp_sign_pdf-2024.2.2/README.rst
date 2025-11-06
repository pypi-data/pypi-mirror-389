CAERP Sign PDF
======================================================

Cette librairie a pour objectif de fournir un ensemble cohérent pour la signature et l'horodatage électronique des fichiers PDF issus de [CAERP](https://framagit.org/caerp/caerp).



Activation du module
---------------------

L'API publique est configurable dans CAERP au travers du fichier de configuration .ini.


** Assurez-vous que la librairie `caerp_sign_pdf` est bien dans les `pyramid.includes` **

.. code-block:: console

   pyramid.includes = ...
                      ...
                      caerp_sign_pdf


** Configurez le service **

.. code-block:: console

   caerp.services.sign_pdf_service = caerp_sign_pdf.public.SignPDFService


** Configurez le chemin vers le certificat à utiliser pour signer et sa clé secrète **

.. code-block:: console

   caerp.sign_certificate_path = /path/to/certificate.p12
   caerp.sign_certificate_passphrase = **************************


** Configurez les journaux de `caerp_sign_pdf` **

Voir la [documentation sur le module Python `logging`](https://docs.python.org/2/library/logging.html) pour le détail ainsi que les exemples dans le fichier development.ini.sample.



Vérification de la signature d'un document
------------------------------------------

La plupart des clients PDF permettent de visualiser et contrôler la signature numérique des documents, mais pas tous : les navigateurs web ne les affichent pas par défaut, de même pour certaines applications mobiles ou volontairement très simple.

Sous linux la signature d'un document PDF peut être vérifiée facilement en ligne de commande grâce à l'utilitaire `pdfsig` de la librairie `poppler-utils` :

.. code-block:: console

   pdfsig <monfichierpdf.pdf>

