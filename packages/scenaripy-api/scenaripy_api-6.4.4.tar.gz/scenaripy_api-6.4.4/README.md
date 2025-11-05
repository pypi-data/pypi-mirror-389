# Une API cliente pour les produits Scenari

`scenaripy_api` propose des fonctions d'API appelable en Python pour intéragir avec un serveur Scenari. Pour fonctionner, `scenaripy_api` nécessite l'installation d'un package client d'une application Scenari (comme scchainserver_6_4, scchainserverlite_6_4, scsuitestarter_6_4 ou ltisuite_2_0).

## Compatibilité

Il est recommandé de toujours utiliser la dernière version de ce package. Elle est compatible avec **tous les packages clients produits par Scenari 6.3 et 6.4.**

## Exemple d'utilisation
```python
import scenaripy_api
import scchainserver_6_4.portal

# Création de l'objet portal
portal = scchainserver_6_4.portal.new_portal(overridden_conf_file="conf.json")

# Appel d'une méthode de l'API
scenaripy_api.create_or_update_user(portal, account="mon-compte-user", first_name="Prénom", last_name="Nom", roles=["main:reader"], other_props={"password" : "Mon-Password"})
```

## Quelles actions sont possibles avec l'API

### Fonctions génériques : 
 * Lister les utilisateurs ou groupe (`list_users_or_groups`)
 * Créer ou éditer les propriétés d'un utilisateur ou groupe (`create_or_update_user`, `create_or_update_group`)
 * Associer un role à un utilisateur ou groupe (`set_granted_roles`)

### Sur un portlet chain :
 * Créer ou éditer les propriétés d'un atelier (`create_or_update_wsp`)
 * Rechercher dans un atelier (`wsp_search`)
 * Télécharger ou uploader un item, d'une ressource binaire ou de ses métadonnées (`wsp_get_item`, `wsp_get_res`, `wsp_get_res_meta`, `wsp_set_item`, `wsp_set_res`, `wsp_set_res_meta`)
 * Télécharger ou uploader un scar (sous ensemble d'un atelier) ou scwsp (atelier complet) (`wsp_export_scwsp`, `wsp_export_scar`, `wsp_import_scar`)
 * Lancer une génération et télécharger du fichier généré (`wsp_generate`)

### Sur une suite contenant un chain et un depot
 * Envoyer un scar depuis un portlet chain vers un portlet depot (`wsp_send_scar`)

### Sur un portlet depot
 * Uploader une ressource dans un depot (`write_depot_request`)
