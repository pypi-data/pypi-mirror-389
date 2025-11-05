import inspect
import json
import os
import re
import xml.sax.saxutils
import logging
from enum import Enum
from typing import List, Optional, Any

"""

FONCTIONS SPÉCIFIQUES CHAIN


"""


def search_wsp_code(portal, title: Optional[str] = None, title_fragment: Optional[str] = None, alias: Optional[str] = None, is_drf: Optional[bool] = None,
                    drf_Ref_wsp: Optional[str] = None, is_drv: Optional[bool] = None, drv_axis: Optional[str] = None, drv_master: Optional[str] = None,
                    is_public: Optional[bool] = None, wsp_key: Optional[str] = None, wsp_uri: Optional[str] = None, wsp_version: Optional[str] = None,
                    wsp_lang: Optional[str] = None, portlet_code: str = "chain") -> Optional[str]:
	"""
	Recherche le code d'un atelier (wspCode) par titre, alias, type d'atelier, modèle documentaire...
	Exemples d'appels
	```python
# Cherche un code d'atelier par son titre exact
wsp_code = scenaripy_api.search_wsp_code(server, title="Mon titre d'atelier de documentation complet")

# Cherche un code d'atelier en cherchant un fragment de texte dans son Titre.
wsp_code = scenaripy_api.search_wsp_code(server, title_fragment="documentation")

# Cherche uniquement parmi les ateliers draft
wsp_code = scenaripy_api.search_wsp_code(server, title_fragment="documentation", is_drf=True)

# Cherche un atelier utilisant du modèle Dokiel en français ayant pour fragment de titre documentation et étant un atelier public
wsp_code = scenaripy_api.search_wsp_code(server, title_fragment="documentation", wsp_key="dokiel", wsp_lang="fr-FR", is_public=True)
	```

	:param portal: l'objet ScPortal représentant le serveur Scenari visé
	:param title: recherche exacte par le titre de cet atelier
	:param title_fragment: recherche un wsp dont le titre contient title_fragment
	:param alias: recherche par l'alias de l'atelier
	:param is_drf: recherche un atelier calque de travail
	:param drf_Ref_wsp: recherche un atelier calque de travail par le code de l'atelier de référence
	:param is_drv: recherche un atelier dérivé
	:param drv_axis: recherche un atelier dérivé par le code de dérivation
	:param drv_master: recherche un atelier dérivé par le code de l'atelier maître
	:param is_public: recherche un atelier publique
	:param wsp_key: recherche un atelier par la clé du modèle documentaire (par exemple 'Opale')
	:param wsp_uri: recherche un atelier l'URI du modèle documentaire (par exemple 'Opale_fr-FR_5-0-3')
	:param wsp_version: recherche un atelier par la version du modèle documentaire (par exemple '5.0.3')
	:param wsp_lang: recherche un atelier par langue du modèle documentaire (par exemple 'fr-FR')
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: le code du wsp trouvé. `None` si aucun wsp trouvé.
	"""
	for wsp in __p(portal, portlet_code).adminWsp.list()["wsps"]:
		if title is not None and wsp["title"] != title:
			continue
		if title_fragment is not None and title_fragment not in wsp["title"]:
			continue
		if alias is not None and hasattr(wsp, "alias") and wsp["alias"] != alias:
			continue
		if is_drf is not None and "drfMasterWsp" not in wsp["props"]:
			continue
		if drf_Ref_wsp is not None and ("drfRefWsp" not in wsp["props"] or wsp["props"]["drfRefWsp"] != drf_Ref_wsp):
			continue
		if is_drv is not None and "drvAxis" not in wsp["props"]:
			continue
		if drv_axis is not None and ("drvAxis" not in wsp["props"] or wsp["props"]["drvAxis"] != drv_axis):
			continue
		if drv_master is not None and ("drvMasterWsp" not in wsp["props"] or wsp["props"]["drvMasterWsp"] != drv_master):
			continue
		if is_public is not None:
			if "publicWsp" not in wsp["props"]:
				if is_public:
					continue
			elif wsp["props"]["publicWsp"] == "false" and is_public or wsp["props"]["publicWsp"] == "true" and not is_public:
				continue
		if wsp_key is not None and wsp["wspType"]["key"] != wsp_key:
			continue
		if wsp_uri is not None and wsp["wspType"]["uri"] != wsp_uri:
			continue
		if wsp_version is not None and wsp["wspType"]["version"] != wsp_version:
			continue
		if wsp_lang is not None and wsp["wspType"]["lang"] != wsp_lang:
			continue
		return wsp["wspCd"]
	return None


def create_or_update_wsp(portal, wsp_type_key: str, wsp_type_version: Optional[str] = None, wsp_type_lang: Optional[str] = None, wsp_type_options: Optional[list[any]] = None,  # wsp type
                         title: Optional[str] = None, alias: Optional[str] = None, desc: Optional[str] = None,  # Optional generic attributes
                         code: Optional[str] = None, folder_content: Optional[str] = None, folder_gen: Optional[str] = None,  # FS backend
                         skins: Optional[list[str]] = None, public: Optional[bool] = None, support_air_item: Optional[bool] = None, support_ext_item: Optional[bool] = None,  # Db Backend
                         wsp_drf_ref: Optional[str] = None, drf_title: Optional[str] = None,  # draft wsp
                         wsp_drv_master: Optional[str] = None, drv_axis: Optional[str] = None, drv_axis_path: Optional[list[str]] = None,  # drv wsp
                         scwsp: Optional[bytes] = None, local_file_path: Optional[str] = None,  # Import scwsp
                         portlet_code: str = "chain") -> str:
	"""
	Crée ou met un atelier à jour.
	Exemple d'appels :
	```python
	# Création ou mise à jour d'un atelier avec la dernière version d'Opale installée sur le serveur et l'extension Tutoriel (ex-Émeraude).
	create_or_update_wsp(portal, wsp_type_key="Opale", wsp_type_options=[{"wsp_type_key":"OpaleExtEmeraude"}], title="Mon atelier Opale", alias="opale")

	# Création ou mise à jour d'un atelier avec la dernière version d'Opale 5 installée sur le serveur sans extension.
	create_or_update_wsp(portal, wsp_type_key="Opale", wsp_type_version="5", title="Mon atelier Opale", alias="opale")

	# Création d'un atelier brouillon.
	create_or_update_wsp(portal, wsp_type_key="Opale", alias="testDrf", wsp_drf_ref="opale", drf_title="Mon atelier brouillon")

	# Création d'un atelier dérivé.
	create_or_update_wsp(portal, wsp_type_key="Opale", alias="testDrv", wsp_drv_master="opale", drv_axis="fc")

	# Création d'un second atelier dérivé dont le chemin de dérivation passe par le premier avant d'aller sur le master.
	create_or_update_wsp(portal, wsp_type_key="Opale", alias="testDrv2", wsp_drv_master="opale", drv_axis="alternance", drv_axis_path=["fc"])
	```
	:param portal: l'objet ScPortal représentant le serveur Scenari visé
	:param wsp_type_key: la clé du modèle documentaire visé. Par exemple "Opale".
	:param wsp_type_version: la version cible du modèle documentaire. La dernière version est prise si ce paramètre est absent. Ce paramètre accepte au choix une version majeure ("5"), majeur et medium ("5.0") ou complète ("5.0.5"). Si la version n'est pas complète, la dernière version correspondante (la dernière 5 ou la dernière 5.0) sera utilisée.
	:param wsp_type_lang: la langue du modèle documentaire (par exemple "fr-FR" ou "en-US"). Si non précisé, le premier modèle correspondant aux autres critères est sélectionné.
	:param wsp_type_options: les extensions à utiliser. Ce paramètre attend un tableau de dict {wsp_type_key:str, wsp_type_version:Option[str], wsp_type_lang:Option[str]}
	:param title: le titre de l'atelier. Ce paramètre ne peut pas être utilisé lors de la création d'un atelier brouillon ou dérivé.
	:param alias: l'alias de cet atelier. L'alias se substitue au code de l'atelier. Il est unique et stable sur un même serveur. Fonction supportée uniquement en DB.
	:param desc: la description de l'atelier
	:param code: le code de cet atelier (FS uniquement). Le code est unique et stable sur un même serveur.
	:param folder_content: le chemin vers le dossier de l'atelier. Paramètre supporté uniquement pour la création d'un atelier sur un serveur FS.
	:param folder_gen: le chemin vers le répertoire des générations de cet atelier. Paramètre supporté uniquement pour la création d'un atelier sur un serveur FS.
	:param skins: les skins à utiliser avec cet atelier. Fonction supportée uniquement en DB.
	:param public: statut public de l'atelier. (pour être pointé par des items externes depuis d'autres ateliers). La fonction doit être permise dans la configuration du serveur. Fonction supportée uniquement en DB.
	:param support_air_item: activer la fonction des `air` items. La fonction doit être permise dans la configuration du serveur. Fonction supportée uniquement en DB.
	:param support_ext_item: activer la fonction des items externes. La fonction doit être permise dans la configuration du serveur. Fonction supportée uniquement en DB.
	:param wsp_drf_ref: ce paramètre permet de préciser que l'atelier créé est un atelier brouillon. Il doit contenir le wspCd ou l'alias vers l'atelier de référence. La fonction doit être permise dans la configuration du serveur. Fonction supportée uniquement en DB.
	:param drf_title: le titre de l'atelier brouillon.
	:param wsp_drv_master: ce paramètre permet de préciser que l'atelier créé est un atelier dérivé. Il doit contenir le wspCd ou l'alias vers l'atelier maître. La fonction doit être permise dans la configuration du serveur. Fonction supportée uniquement en DB.
	:param drv_axis: l'axe de dérivation d'un atelier dérivé.
	:param drv_axis_path: ce paramètre permet de définir le chemin de dérivation dans le cas où plusieurs ateliers sont dérivés d'un même atelier maître.
	:param scwsp: ce paramètre, valide uniquement pour une création d'atelier, permet d'importer un scwsp lors de la création de l'atelier (passé sous forme de `bytes`). Si ce paramètre est défini, les paramètres de wsp_type ne sont pas nécessaires. Si ce paramètre est défini, le paramètre local_file_path est ignoré.
	:param local_file_path: ce paramètre, valide uniquement pour une création d'atelier, permet d'importer un scwsp lors de la création de l'atelier (le paramètre contient le chemin vers le fichier scwsp). Si ce paramètre est défini, les paramètres de wsp_type ne sont pas nécessaires.
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer).
	:return: le code de l'atelier créé.
	"""

	wsp_type_inst = None

	if hasattr(__p(portal, portlet_code), "adminOdb"):
		if code is not None:
			raise ValueError("code parameter is not supported on ODB chain backend")
		if folder_content is not None:
			raise ValueError("folder_content parameter is not supported on ODB chain backend")
		if folder_gen is not None:
			raise ValueError("folder_gen parameter is not supported on ODV chain backend")

	else:
		if skins is not None:
			raise ValueError("skins parameter is not supported on FS chain backend")
		if public is not None:
			raise ValueError("public parameter is not supported on FS chain backend")
		if support_air_item is not None:
			raise ValueError("support_air_item parameter is not supported on FS chain backend")
		if support_ext_item is not None:
			raise ValueError("support_ext_item parameter is not supported on FS chain backend")
		if wsp_drf_ref is not None:
			raise ValueError("wsp_drf_ref parameter is not supported on FS chain backend")
		if drf_title is not None:
			raise ValueError("drf_title parameter is not supported on FS chain backend")
		if wsp_drv_master is not None:
			raise ValueError("wsp_drv_master parameter is not supported on FS chain backend")
		if drv_axis is not None:
			raise ValueError("drv_axis parameter is not supported on FS chain backend")
		if drv_axis_path is not None:
			raise ValueError("drv_axis_path parameter is not supported on FS chain backend")

	if wsp_drf_ref is not None:
		if title is not None:
			raise ValueError("title can not be set on a draft wsp. Use drf_title to set the draft title")
		if wsp_drv_master is not None:
			raise ValueError("wsp_drv_master and wsp_drf_ref parameters can not be defined together")
		if drv_axis is not None:
			raise ValueError("drv_axis and wsp_drf_ref parameters can not be defined together")
		if drv_axis_path is not None:
			raise ValueError("drv_axis and wsp_drf_ref parameters can not be defined together")
		if scwsp is not None:
			raise ValueError("scwsp and wsp_drf_ref parameters can not be defined together")
		if local_file_path is not None:
			raise ValueError("local_file_path and wsp_drf_ref parameters can not be defined together")
		ref = __p(portal, portlet_code).adminWsp.info_wsp(wsp_drf_ref)
		if ref["status"] == "noWsp":
			raise ValueError(f"impossible to find a ref wsp with code or alias '{wsp_drf_ref}'")
		wsp_drf_ref = ref["wspCd"]

	elif wsp_drv_master is not None:
		if title is not None:
			raise ValueError("title can not be set on a drv wsp")
		if drf_title is not None:
			raise ValueError("drf_title and wsp_drv_master parameters can not be defined together")
		if scwsp is not None:
			raise ValueError("scwsp and wsp_drv_master parameters can not be defined together")
		if local_file_path is not None:
			raise ValueError("local_file_path and wsp_drv_master parameters can not be defined together")
		if drv_axis is None:
			raise ValueError("drv_axis axis is mandatory with parameter wsp_drv_master")

		master = __p(portal, portlet_code).adminWsp.info_wsp(wsp_drv_master)
		if master["status"] == "noWsp":
			raise ValueError(f"impossible to find a master wsp with code or alias '{wsp_drv_master}'")
		wsp_drv_master = master["wspCd"]

	if scwsp is not None:
		if wsp_type_key is not None:
			raise ValueError("wsp_type_key and scwsp parameters can not be defined together")
		if wsp_type_version is not None:
			raise ValueError("wsp_type_version and scwsp parameters can not be defined together")
		if wsp_type_lang is not None:
			raise ValueError("wsp_type_lang and scwsp parameters can not be defined together")
		if wsp_type_options is not None:
			raise ValueError("wsp_type_options and scwsp parameters can not be defined together")
		if code is not None:
			raise ValueError("code and scwsp parameters can not be defined together")

	elif local_file_path is not None:
		if wsp_type_key is not None:
			raise ValueError("wsp_type_key and local_file_path parameters can not be defined together")
		if wsp_type_version is not None:
			raise ValueError("wsp_type_version and local_file_path parameters can not be defined together")
		if wsp_type_lang is not None:
			raise ValueError("wsp_type_lang and local_file_path parameters can not be defined together")
		if wsp_type_options is not None:
			raise ValueError("wsp_type_options and local_file_path parameters can not be defined together")
		if code is not None:
			raise ValueError("code and local_file_path parameters can not be defined together")

	else:
		wsp_type_inst = __search_wsp_type_inst(portal, wsp_type_key, wsp_type_version, wsp_type_lang, wsp_type_options, portlet_code)
		if wsp_type_inst is None:
			raise ValueError(
				"unable to find wsp type. Check the paramaters wsp_type_key, wsp_type_version, wsp_type_lang and wsp_type_options or the installed wsppacks on the server")
	props = {"title": title, "desc": desc,
	         "code": code, "folderContent": folder_content, "folderGen": folder_gen,  # FS Props
	         "alias": alias, "skins": skins, "publicWsp": public, "airIt": support_air_item, "extIt": support_ext_item,  # DB Props
	         "wspRef": wsp_drf_ref, "draftTitle": drf_title, "wspMaster": wsp_drv_master, "drvAxis": drv_axis, "drvDefaultSrcFindPath": drv_axis_path
	         }
	props = {k: v for k, v in props.items() if v is not None}

	create = True
	wsp = None
	if alias is not None or code is not None:
		wsp = __p(portal, portlet_code).adminWsp.info_wsp(alias if code is None else code)
		create = wsp["status"] == "noWsp"
	if create:
		if scwsp is not None or local_file_path is not None:
			return __p(portal, portlet_code).adminWsp.create_wsp_import(params=props, data=scwsp if scwsp is not None else local_file_path)["wspCd"]
		else:
			return __p(portal, portlet_code).adminWsp.create_wsp(wsp_type=wsp_type_inst, params=props)["wspCd"]
	else:
		if "drfRefWsp" in wsp["props"]:
			if wsp_drf_ref is not None and wsp_drf_ref != wsp["props"]["drfRefWsp"]:
				raise ValueError(f"drfRefWsp is set to '{wsp['props']['drfRefWsp']}' and wsp_drf_ref is '{wsp_drf_ref}'. Changing drfRefWsp is forbidden")
			if wsp_drv_master is not None:
				raise ValueError("the wsp exists and has a drf status. Impossible to set wsp_drv_master parameter")
			if drv_axis is not None:
				raise ValueError("the wsp exists and has a drf status. Impossible to set drv_axis parameter")
			if drv_axis_path is not None:
				raise ValueError("the wsp exists and has a drf status. Impossible to set drv_axis_path parameter")
		elif "drvMasterWsp" in wsp["props"]:
			if wsp_drf_ref is not None:
				raise ValueError("the wsp exists and has a drv status. Impossible to set wsp_drf_ref parameter")
			if drf_title is not None:
				raise ValueError("the wsp exists and has a drv status. Impossible to set drf_title parameter")
		__p(portal, portlet_code).adminWsp.update_wsp_props(wsp_code=wsp["wspCd"], params=props)
		__p(portal, portlet_code).adminWsp.update_wsp_type(wsp_code=wsp["wspCd"], wsp_type=wsp_type_inst)
		return wsp["wspCd"]


"""

FONCTIONS SUR LE WSP


"""


def wsp_search(portal, wsp_code: str, request, portlet_code: str = "chain") -> List[List[Any]]:
	"""
	Appel au moteur de recherche d'un atelier. Cet appel nécessite la création d'un objet [package-lib].api.search.Request.

	```python
# Recherche des items ayant le mot clé documentation
crit = SearchFullText("documentation")
search_request = Request(criterions=crit)
result = scenaripy_api.wsp_search(server, wsp_code, search_request)

# Spécifier ses propres champs à retourner
search_request = Request(criterions=crit, columns=[ESrcField.srcUri, ESrcField.itTi, ESrcField.itModel])

# Agrandir ou déplacer la fenêtre de recherche
search_request = Request(criterions=crit, columns=[ESrcField.srcUri, ESrcField.itTi, ESrcField.itModel], number_of_results=1000, start_offset=10)
	```

	:param portal: l'objet ScPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier ciblé
	:param request: l'objet Request à envoyer au serveur
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: une liste contenant une liste par résultat puis un champ par colonne définie dans la `request`.
	"""
	return __p(portal, portlet_code).search.search(wsp_code, request)["results"]


def wsp_get_item(portal, wsp_code: str, ref_uri: str, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> Optional[str]:
	"""
	Récupération d'un item XML.
	```python
# Récupération d'un item sous forme de String stocké dans une variable python
item_xml = scenaripy_api.wsp_get_item(server, wsp_code, ref_uri="/path/vers/mon/item.xml")

# Récupération d'un item dans un fichier sur disque
scenaripy_api.wsp_get_item(server, wsp_code, ref_uri="/path/vers/mon/item.xml", local_file_path="./item.xml")
	```

	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param ref_uri: le chemin vers l'item (ou l'ID de l'item)
	:param local_file_path: si spécifié, l'item est téléchargé sur disque vers ce chemin
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: Aucun retour si `local_file_path` est spécifié. Une `str` contenant l'item sinon.
	"""
	item = __p(portal, portlet_code).wspSrc.get_src(wsp_code, ref_uri)
	if local_file_path is not None:
		with open(local_file_path, "w") as file:
			file.write(item)
			return
	else:
		return item


def wsp_get_res(portal, wsp_code: str, src_uri: str, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> Optional[bytes]:
	"""
	Récupération d'une ressource binaire.
	```python
# Récupération d'un flux binaire dans une variable python
flux_binaire = scenaripy_api.wsp_get_res(server, wsp_code, src_uri="/path/vers/mon/image.png")

# Récupération d'un flux binaire dans un fichier sur disque
scenaripy_api.wsp_get_res(server, wsp_code, src_uri="/path/vers/mon/image.png", local_file_path="./mon-image.png")
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param src_uri: le chemin vers la ressource
	:param local_file_path: si spécifié, l'item est téléchargé sur disque vers ce chemin
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: Aucun retour si `local_file_path` est spécifié. la ressourc binaire sous forme de `bytes` sinon.
	"""
	uri = f"{src_uri}/{src_uri.split('/')[-1]}"
	binary = __p(portal, portlet_code).wspSrc.get_src_bytes(wsp_code, uri)
	if local_file_path is not None:
		with open(local_file_path, "wb") as file:
			file.write(binary)
			return
	else:
		return binary


def wsp_get_res_meta(portal, wsp_code: str, src_uri: str, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> Optional[str]:
	"""
	Récupération des métadonnées d'une ressource binaire.
	```python
# Récupération d'un fichier de méta sous forme de String dans une variable python
meta_xml = scenaripy_api.wsp_get_res_meta(server, wsp_code, src_uri="/path/vers/mon/image.png")

# Récupération d'un fichier de meta dans un fichier sur disque
scenaripy_api.wsp_get_res_meta(server, wsp_code, src_uri="/path/vers/mon/image.png", local_file_path="./meta.xml")
```

	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param src_uri: le chemin vers l'item
	:param local_file_path: si spécifié, l'item est téléchargé sur disque vers ce chemin
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: Aucun retour si `local_file_path` est spécifié. Une `str` contenant le fichier de métadonnées sinon.
	"""
	uri = f"{src_uri}/meta.xml"
	item = __p(portal, portlet_code).wspSrc.get_src(wsp_code, uri)
	if local_file_path is not None:
		with open(local_file_path, "w") as file:
			file.write(item)
			return
	else:
		return item


def wsp_set_item(portal, wsp_code: str, ref_uri: str, item: Optional[str | bytes] = None, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> None:
	"""
	Upload d'un item sur le serveur depuis une chaîne de caractères ou un fichier.
	```python
# Upload d'un item stocké dans une variable python
scenaripy_api.wsp_set_item(server, wsp_code, ref_uri="/path/vers/mon/item.xml", item=item_xml)

# Upload d'un item depuis un fichier sur disque
scenaripy_api.wsp_set_item(server, wsp_code, ref_uri="/path/vers/mon/item.xml", local_file_path="./item.xml")
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param ref_uri: le chemin vers l'item (ou l'ID de l'item)
	:param item: le contenu de l'item au format `str` ou `bytes`. Ne peut pas être spécifié en doublon avec le paramètre `local_file_path`
	:param local_file_path: le chemin local sur le disque où récupérer le fichier XML de l'item à envoyer.
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	"""
	if item is None and local_file_path is None or item is not None and local_file_path is not None:
		raise ValueError("Only one of the parameters item and local_path could be defined")
	if item is not None:
		content = item
	elif local_file_path is not None:
		with open(local_file_path, "rb") as file:
			content = file.read()
	__p(portal, portlet_code).wspSrc.put_src(wsp_code, ref_uri, content)


def wsp_set_res(portal, wsp_code: str, src_uri: str, res: Optional[bytes] = None, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> None:
	"""
	Upload d'un item sur le serveur depuis une chaîne de caractères ou un fichier.
	```python
# Upload d'un flux binaire depuis une variable python
scenaripy_api.wsp_set_res(server, wsp_code, src_uri="/path/vers/mon/image.png", res=flux_binaire)

# Upload d'un fichier binaire depuis un fichier sur disque
scenaripy_api.wsp_set_res(server, wsp_code, src_uri="/path/vers/mon/image.png", local_file_path="./mon-image.png")
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param src_uri: le chemin vers l'item
	:param res: le contenu du fichier binaire sous forme de `bytes`. Ne peut pas être spécifié en doublon avec le paramètre `local_file_path`
	:param local_file_path: le chemin local sur le disque où récupérer le fichier binaire à envoyer
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	"""
	if res is None and local_file_path is None or res is not None and local_file_path is not None:
		raise ValueError("Only one of the parameters item and local_path could be defined")
	if res is not None:
		content = res
	elif local_file_path is not None:
		with open(local_file_path, "rb") as file:
			content = file.read()
	__p(portal, portlet_code).wspSrc.put_src(wsp_code, src_uri, content)


def wsp_set_res_meta(portal, wsp_code: str, src_uri: str, meta: Optional[str | bytes] = None, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> None:
	"""
	Upload d'un item sur le serveur depuis une chaîne de caractères ou un fichier.
	```python
# Upload d'un fichier de métadonnées d'un flux binaire depuis une variable python
scenaripy_api.wsp_set_res_meta(server, wsp_code, src_uri="/path/vers/mon/image.png", meta=meta_xml)

# Upload d'un fichier de métadonnées d'un flux binaire depuis un fichier sur disque
scenaripy_api.wsp_set_res_meta(server, wsp_code,  src_uri="/path/vers/mon/image.png", local_file_path="./meta.xml")
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param src_uri: le chemin vers le fichier des métadonnées
	:param meta: le contenu des métadonnées au format `str` ou `bytes`. Ne peut pas être spécifié en doublon avec le paramètre `local_file_path`
	:param local_file_path: le chemin local sur le disque où récupérer le fichier XML de métadonnées à envoyer
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	"""
	uri = f"{src_uri}/meta.xml"
	if meta is None and local_file_path is None or meta is not None and local_file_path is not None:
		raise ValueError("Only one of the parameters item and local_path could be defined.")
	if meta is not None:
		content = meta
	elif local_file_path is not None:
		with open(local_file_path, "rb") as file:
			content = file.read()
	__p(portal, portlet_code).wspSrc.put_src(wsp_code, uri, content)


def wsp_send_scar(portal, wsp_code: str, ref_uri: str, send_props: dict[str, any], portlet_code: str = "chain") -> None:
	"""
	Envoie d'un scar par requête HTTP par le serveur depuis un portlet chain.
	```python
# Définition d'un objet SendProps pour réaliser l'envoi par le serveur
send_by_server_props = {
	"method": "PUT",
	"url": "https://mon-domaein.org/API/set/backup",
	"headerProps": {"Authorization:": "Bearer xxxx"}
	"addQSParams": {"token":"xxx"}
}

# Envoi du scar
scenaripy_api.wsp_send_scar(server, wsp_code, ref_uri="/path/vers/mon/item/racine.xml", send_props=send_by_server_props)
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param ref_uri: le chemin vers l'item (ou l'ID de l'item)
	:param send_props: ce paramètre optionnel permet d'envoyer le résultat de génération par une requête HTTP envoyée par le serveur. Valeur attendue : [package-lib].api.item.JSendProps
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	"""
	status_code = __p(portal, portlet_code).export.send_to(wsp_code, [ref_uri], send_props)
	if status_code != 200 and status_code != 204:
		logging.warning(f"The content has been sent by the serveur. The response is {status_code} (should be checked).")


def wsp_generate(portal, wsp_code: str, ref_uri: str, code_gen_stack: str, props: Optional[dict[str, Any]] = None,
                 send_props: Optional[dict[str, any]] = None, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> Optional[bytes]:
	"""
	Lance puis télécharge une génération.
	```python
# Pour télécharger la génération dans une variable python
flux_binaire = scenaripy_api.wsp_generate(server, wsp_code, ref_uri="/path/mon/item/de/publication.xml", code_gen_stack="web", props={"skin": "default"})

# Enregistrer le résultat de génération sur disque en utilisant un skin produit par SCENARIstyler (le code du skin doit alors être préfixé par le caractère ~).
scenaripy_api.wsp_generate(server, wsp_code, ref_uri="/path/mon/item/de/publication.xml", code_gen_stack="web", props={"skin": "~DokielTitania25"}, local_file_path="./mon-gen.zip")

# Envoyer le résultat de génération depuis le serveur
# Définition d'un objet SendProps pour réaliser l'envoi par le serveur
send_by_server_props = {
	"method": "PUT",
	"url": "https://mon-domaein.org/API/set/backup",
	"headerProps": {"Authorization:": "Bearer xxxx"}
	"addQSParams": {"token":"xxx"}
}
scenaripy_api.wsp_generate(server, wsp_code, ref_uri="/path/mon/item/de/publication.xml", code_gen_stack="web", props={"skin": "default"}, send_props=send_by_server_props)
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier concerné
	:param ref_uri: le chemin vers l'item (ou l'ID de l'item)
	:param code_gen_stack: le code du générateur (défini dans le modèle. À demander à votre modélisateur ou sur les forums pour un modèle libre)
	:param props: dict optionnel pour spécifier des propriétés de génération. Attention, pour utiliser un skin produit avec SCENARIstyler, le code du skin doit être préfixé par le caractère `~`. Par exemple : `{"skin": "~DokielTitania25"}`.
	:param send_props: ce paramètre optionnel permet d'envoyer le résultat de génération par une requête HTTP envoyée par le serveur. Valeur attendue : [package-lib].api.item.JSendProps
	:param local_file_path: si spécifié, la génération est téléchargée sur disque vers ce chemin
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: Aucun retour si `local_file_path` ou `send_props` sont spécifiés. Des `bytes` contenant la génération sinon.
	"""
	__p(portal, portlet_code).wspGen.generate(wsp_code, ref_uri, code_gen_stack, props)
	gen_infos = __p(portal, portlet_code).wspGen.wait_for_generation(wsp_code, ref_uri, code_gen_stack)
	gen_status = gen_infos["status"]

	if gen_status == "warning":
		logging.warning(f"Generator {code_gen_stack} on {ref_uri} ended in warning status.")
	elif gen_status in ["failed", "null"]:
		logging.error(f"Generator {code_gen_stack} on {ref_uri} ended in {gen_status} status. Unable to download.")
		return

	if send_props is not None:
		status_code = __p(portal, portlet_code).wspGen.send_gen_to(wsp_code, ref_uri, code_gen_stack, send_props)
		if status_code != 200 and status_code != 204:
			logging.warning(f"The content has been sent by the server. The response is {status_code} (should be checked).")
		return

	if "mimeDownload" not in gen_infos or gen_infos["mimeDownload"] == "":
		return

	if local_file_path is not None:
		with open(local_file_path, "wb") as file:
			file.write(__p(portal, portlet_code).wspGen.download(wsp_code, ref_uri, code_gen_stack))
			return

	if local_file_path is None and send_props is None:
		return __p(portal, portlet_code).wspGen.download(wsp_code, ref_uri, code_gen_stack)


def wsp_export_scwsp(portal, wsp_code: str, local_file_path: Optional[str] = None, portlet_code: str = "chain") -> Optional[bytes]:
	"""
	Export un scwsp d'un atelier.
	```python
# Téléchargement du scwsp dans une variable python
flux_binaire = scenaripy_api.wsp_export_scwsp(server, wsp_code)

# Enregistrement du scwsp sur disque
scenaripy_api.wsp_export_scwsp(server, wsp_code, local_file_path="./mon-atelier.scwsp")
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier
	:param local_file_path: si spécifié, l'item est téléchargé sur disque vers ce chemin
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: Aucun retour si `local_file_path` est spécifié. Le scwsp sous forme de `bytes` sinon.
	"""
	b = __p(portal, portlet_code).export.export(wsp_code, [""])
	if local_file_path is not None:
		with open(local_file_path, "wb") as file:
			file.write(b)
			return

	return b


def wsp_export_scar(portal, wsp_code: str, ref_uri: str | list[str], include_items_graph: bool = True, keep_spaces: bool = False, local_file_path: Optional[str] = None,
                    portlet_code: str = "chain") -> Optional[bytes]:
	"""
	Export un scar depuis un ref_uri (espace ou item).
	```python
# Téléchargement d'un scar incluant tout le réseau déscendant de l'item et respectant les espaces de l'atelier. Stockage du scar obtenu dans une variable python
flux_binaire = scenaripy_api.wsp_export_scar(server, wsp_code, ref_uri="/path/vers/mon/item.xml", include_items_graph=True, keep_spaces=True)

# Téléchargement de deux items dans un scar sans conserver les espaces de l'atelier et sans inclure le réseau descendant. Stockage du résultat sur disque
scenaripy_api.wsp_export_scar(server, wsp_code, ref_uri=["/path/vers/mon/item1.xml", "/path/vers/mon/item2.xml"], include_items_graph=False, keep_spaces=True, local_file_path="./mon-export.scar")
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier
	:param ref_uri: le chemin vers l'item ou l'espace (ou son ID) racine de l'export (un tableau de chemins peut être passé dans ce paramètre)
	:param include_items_graph: inclure le réseau descendant complet de cet item
	:param keep_spaces: préserver les espaces de l'atelier
	:param local_file_path: si spécifié, l'item est téléchargé sur disque vers ce chemin
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: Aucun retour si `local_file_path` est spécifié. Le scar sous forme de `bytes` sinon.
	"""
	b = __p(portal, portlet_code).export.export(wsp_code, ref_uris=[ref_uri] if ref_uri is str else ref_uri, scope="net" if include_items_graph else "node",
	                                            mode="wspTree" if keep_spaces else "rootAndRes")
	if local_file_path is not None:
		with open(local_file_path, "wb") as file:
			file.write(b)
			return
	return b


def wsp_import_scar(portal, wsp_code: str, scar: Optional[bytes] = None, local_file_path: Optional[str] = None, ref_uri: Optional[str] = None, replace_if_exist: bool = False,
                    portlet_code: str = "chain") -> None:
	"""
	Import d'un scar dans un atelier
	```python
# Import d'un scar dont le flux binaire est passé en variable. On remplace les items existants de l'atelier.
scenaripy_api.wsp_import_scar(server, wsp_code, scar=flux_binaire, replace_if_exist=True)

# Import d'un scar stocké sur disque. On remplace les items existants de l'atelier. On upload dans un dossier spécifique
scenaripy_api.wsp_import_scar(server, wsp_code, ref_uri="/path/vers/mon/espace", replace_if_exist=False, local_file_path="./mon-export.scar")
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param wsp_code: le code de l'atelier
	:param scar: le contenu du scar au format `bytes`. Ne peut pas être spécifié en doublon avec le paramètre `local_file_path`
	:param local_file_path: le chemin local sur le disque où récupérer le fichier scar à envoyer.
	:param ref_uri: le chemin vers le dossier vers lequel envoyer l'archive (par défaut, le contenu de l'archive est envoyé à la racine de l'atelier)
	:param replace_if_exist: Spécifier `True` pour permettre l'écrasement d'une ressource existante
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	"""
	__p(portal, portlet_code).importSvc.import_archive(wsp_code, content=scar if scar is not None else local_file_path, ref_uri_target=ref_uri, replace_if_exist=replace_if_exist)


"""

FONCTIONS SPÉCIFIQUES DÉPÔT


"""


def write_depot_request(portal, metas: dict[str, str], content: bytes | str = None, sync: bool = True, portlet_code: str = "depot") -> None:
	"""
	Envoi d'une requête en écriture sur le dépôt.
	```python
# Import d'une ressource dans le depot depuis un fichier sur disque
scenaripy_api.write_depot_request(server, metas={"path": "path/du/depot/res", "processing": "archive", "title": "Mon site"}, content="./monSite.zip")

# Import d'une ressource dans le depot avec passage de la ressource en variable
scenaripy_api.write_depot_request(server, metas={"path": "path/du/depot/res", "processing": "file", "title": "Mon titre"}, content=flux_binaire)
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param metas: les métadonnées de la requête (ne pas indiquer les métadonnées "system" scContent ou createMetas
	:param content: si la requête inclut un contenu binaire, le contenu binaire ou le chemin vers le fichier
	:param sync: indiquer False pour basculer sur un envoi asynchrone. Une requête est envoyée à intervalle régulier jusqu'à fin du traitement.
	:param portlet_code: le code du portlet sur lequel faire la recherche ("depot" par défaut, spécifier ce paramètre pour le changer)
	"""
	if sync:
		resp = __p(portal, portlet_code).cid.sync_cid_request(metas=metas, content=content, return_props=["scCidSessStatus"])
	else:
		resp = __p(portal, portlet_code).cid.async_cid_request(metas=metas, content=content, return_props=["scCidSessStatus"])
	if resp["scCidSessStatus"] != "commited":
		raise RuntimeError(f"Cid request is not commited. Server returns {resp['scCidSessStatus']} status\nmetas sent: {json.dumps(metas)}")


"""

FONCTIONS GÉNÉRIQUES


"""


def list_users_or_groups(portal, include_users: bool = True, include_groups: bool = True, portlet_code: str = "chain") -> list[dict[str, any]]:
	"""
	Retourne la liste des utilisateurs et/ou groupes.
	```python
# Liste des utilisateurs en excluant les groupes
scenaripy_api.list_users_or_groups(server, include_users=True, include_groups=False)

# Liste des groupes en excluant les utilisateurs
scenaripy_api.list_users_or_groups(server, include_users=True, include_groups=False)
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param include_users: si true, les accounts de type "user" seront inclus dans la liste retournée
	:param include_groups: si true, les accounts de type "group" seront inclus dans la liste retournée
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: La liste des utilisateurs ou groupes. Chaque objet est un dict contenant les propriétés retournées par le serveur.
	"""
	options = {}
	if not include_users and not include_groups:
		return []

	if include_groups and not include_users:
		options["filterType"] = "group"

	if include_users and not include_groups:
		options["filterType"] = "user"
	return __p(portal, portlet_code).adminUsers.list(options)["userList"]


def create_or_update_user(portal, account: str, nick_names: Optional[list[str]] = None, first_name: Optional[str] = None, last_name: Optional[str] = None,
                          email: Optional[str] = None,
                          groups: Optional[list[str]] = None, roles: Optional[list[str]] = None, auth_method: Optional[str] = None, other_props: Optional[dict[str, any]] = None,
                          portlet_code: str = "chain") -> dict[str, any]:
	"""
	Crée ou met un utilisateur à jour.

	```python
# Creation d'un user
scenaripy_api.create_or_update_user(portal, account="mon-compte-user", first_name="Prénom", last_name="Nom", roles=["main:reader"], other_props={"password" : "Mon-Password"})
```

	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param account: le compte de l'utilisateur
	:param nick_names: les surnoms (pseudos) de l'utilisateur (facultatif)
	:param first_name: le prénom de l'utilisateur (facultatif)
	:param last_name: le nom de famille de l'utilisateur (facultatif)
	:param email: l'email de l'utilisateur (facultatif)
	:param groups: les groupes de l'utilisateur (facultatif)
	:param roles: les rôles attribués à l'utilisateur (facultatif)
	:param auth_method: la méthode d'authentification de l'utilisateur (facultatif)
	:param other_props: dict contenant d'autres propriétés (facultatif). Ce paramètre n'est pas normalisé. Son contenu dépend de la configuration du système de gestion des utilisateurs (stockage en base de données ou système de fichier, méthode d'authentification locale ou centralisée via LDAP ou autre...). Dans le cas général d'une authentification locale, le mot de passe se définit dans ce champ `other_props` avec la clé `password`.

	:param portlet_code: Le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: l'utilisateur sous forme d'un Dict.
	"""
	props = {"nickNames": nick_names, "firstName": first_name, "lastName": last_name, "email": email, "groups": groups, "grantedRoles": roles, "authMethod": auth_method,
	         "userType": "user", **(other_props if other_props is not None else {})}
	props = {k: v for k, v in props.items() if v is not None}
	if __p(portal, portlet_code).adminUsers.display(account) is not None:
		return __p(portal, portlet_code).adminUsers.update_user(account, props)
	else:
		return __p(portal, portlet_code).adminUsers.create_user(account, props)


def create_or_update_group(portal, account: str, group_name: Optional[str] = None, email: Optional[str] = None, groups: Optional[list[str]] = None,
                           roles: Optional[list[str]] = None,
                           portlet_code: str = "chain") -> dict[str, any]:
	"""
	Crée ou met un groupe à jour.
	```python
# Création d'un groupe d'auteurs et ajout de ce groupe à 2 groupes existants
scenaripy_api.create_or_update_group(server, account="mon-groupe-auteurs", group_name="Mon Groupe d'auteurs", email="email@domain.org", groups=["site-Paris", "site-Montpellier"], roles=["main:author"])
```
	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param account: le compte du groupe
	:param group_name: le nom du groupe (facultatif)
	:param email: l'email du groupe (facultatif)
	:param groups: les groupes auxquels appartiennent ce groupe (facultatif)
	:param roles: les roles attribués au groupe (facultatif)
	:param portlet_code: le code du portlet sur lequel faire la recherche ("chain" par défaut, spécifier ce paramètre pour le changer)
	:return: Le groupe sous forme d'un Dict.
	"""
	props = {"groupName": group_name, "email": email, "groups": groups, "grantedRoles": roles}
	props = {k: v for k, v in props.items() if v is not None}
	if __p(portal, portlet_code).adminUsers.display(account) is not None:
		return __p(portal, portlet_code).adminUsers.update_group(account, props)
	else:
		return __p(portal, portlet_code).adminUsers.create_group(account, props)


def set_granted_roles(portal, account: str, granted_roles: list[str], on_wsp_code: str = None, on_wsp_path: str = "", on_urltree_path: str = None,
                      auth_portlet_code="chain", chain_portlet_code: str = "chain", depot_portlet_code: str = "depot") -> None:
	"""
	Définit les rôles associés à un utilisateur au niveau du portal, d'un atelier, d'un espace de l'atelier ou d'un dossier du dépôt.
	Si on_wsp_code et on_urltree_path sont à None, les rôles sont modifiés au niveau du portal.
	Si on_wsp_code est défini et on_wsp_path est à None, les rôles sont modifiés au niveau de l'atelier.
	Si on_wsp_code et on_wsp_path sont définis, les rôles sont modifiés au niveau de l'espace de l'atelier.
	Si on_urltree_path est défini, les rôles sont modifiés au niveau du dossier du dépôt.

	```python
# Association d'un role sur un atelier
scenaripy_api.set_granted_roles(server, account="user1", granted_roles=["main:author"], on_wsp_code=wsp_code)

# Association d'un role sur l'espace "/user1" d'un atelier
scenaripy_api.set_granted_roles(server, account="user1", granted_roles=["main:author"], on_wsp_code=wsp_code, on_wsp_path="/user1")

# Association d'un role sur un dossier "/user1" du depot
scenaripy_api.set_granted_roles(server, account="user1", granted_roles=["main:author"], on_urltree_path="/user1")
```

	:param portal: l'objet scPortal représentant le serveur Scenari visé
	:param account: le compte
	:param granted_roles: la liste des rôles associés à ce compte
	:param on_wsp_code: le code de l'atelier sur lequel définir les rôles
	:param on_wsp_path: l'espace de l'atelier sur lequel définir les rôles
	:param on_urltree_path: le path de l'URLtree sur lequel définir les rôles dans le dépôt
	:param auth_portlet_code: le code du portlet qui porte l'authentification (chain par défaut)
	:param chain_portlet_code: le code du portlet chain sur lequel définir les rôles d'un atelier ou espace (chain par défaut)
	:param depot_portlet_code: le code du portlet dépôt sur lequel définir les rôles d'un dossier de l'urlTree (depot par défaut)
	"""
	if on_wsp_code is None and on_urltree_path is None:
		__p(portal, auth_portlet_code).adminUsers.update_user(account, {"grantedRoles": granted_roles})

	if on_wsp_code is not None:
		__p(portal, chain_portlet_code).wspSrc.set_specified_roles(on_wsp_code, {account: {"allowedRoles": granted_roles}}, ref_uri=on_wsp_path)

	if on_urltree_path is not None:
		roles = __p(portal, depot_portlet_code).adminTree(on_urltree_path, "userRolesMap")
		roles[account] = {"allowedRoles": granted_roles}
		write_depot_request(portal, metas={"olderPath": on_urltree_path, "userRolesMap": roles}, portlet_code=depot_portlet_code)
	return


"""

FONCTIONS INTERNES


"""


def __search_wsp_type_inst(portal, wsp_type_key: str, wsp_type_version: Optional[str] = None, wsp_type_lang: Optional[str] = None, wsp_type_options: Optional[list[any]] = None,
                           portlet_code: str = "chain") -> Optional[any]:
	editor = __p(portal, portlet_code).wspMetaEditor.get_new_editor()
	candidate = None
	for wsp_type in editor:
		wsp_type.attrib["parsed-version"] = list(map(int, wsp_type.attrib["version"].split(".")))
		if wsp_type_key != wsp_type.attrib["key"]:
			continue
		if wsp_type_version is not None and not wsp_type.attrib["version"].startswith(wsp_type_version):
			continue
		if wsp_type_lang is not None and wsp_type_lang != wsp_type.attrib["lang"]:
			continue

		if candidate is None:
			candidate = wsp_type
		else:
			for i in range(0, len(candidate.attrib["parsed-version"])):
				if wsp_type.attrib["parsed-version"][i] > candidate.attrib["parsed-version"][i]:
					candidate = wsp_type
					break
				elif wsp_type.attrib["parsed-version"][i] < candidate.attrib["parsed-version"][i]:
					break

	if candidate is None:
		logging.error(f"No wsp type found for params wsp_type_key: '{wsp_type_key}', wsp_type_version= '{wsp_type_version}' and wsp_type_lang= '{wsp_type_lang}'.")
		return None

	# Recherche des options
	options = []
	if wsp_type_options is not None:
		for wsp_type_option in wsp_type_options:
			candidate_opt = None
			for wsp_type in candidate:
				wsp_type.attrib["parsed-version"] = list(map(int, wsp_type.attrib["version"].split(".")))
				if wsp_type_option["wsp_type_key"] != wsp_type.attrib["key"]:
					continue
				if "wsp_type_version" in wsp_type_option and not wsp_type.attrib["version"].startswith(wsp_type_option["wsp_type_version"]):
					continue
				if "wsp_type_lang" in wsp_type_option and wsp_type_lang != wsp_type_option["wsp_type_lang"]:
					continue

				if candidate_opt is None:
					candidate_opt = wsp_type
				else:
					for i in enumerate(candidate_opt.attrib["parsed-version"]):
						if wsp_type.attrib["parsed-version"][i] > candidate_opt.attrib["parsed-version"][i]:
							candidate_opt = wsp_type
							break
			if candidate_opt is None:
				logging.error(f"No wsp type option found for wsp type uri '{candidate.attrib['uri']}' and option params '{wsp_type_option}'.")
			else:
				options.append(candidate_opt)

	# Construction du wsp_type_inst
	wsp_type_inst = {"wspType": candidate.attrib}
	if len(options) > 0:
		wsp_type_inst["wspOptions"] = []
	for option in options:
		wsp_type_inst["wspOptions"].append(option.attrib)
	return wsp_type_inst


def __p(portal, portlet_code: str):
	"""
	Extrait le portlet depuis un ScPortal et le portlet code. Envoie une exception si le portlet n'est pas trouvé.
	"""
	if portlet_code not in portal:
		raise ValueError(f"Portlet {portlet_code} not found in ScPortal. The Portlet_code attribute should be specified")
	return portal[portlet_code]


def __docstring2dokiel(module, file_path, sub_docs_dir, sub_docs_prefix, samples_dir, samples_path_prefix, opts):
	"""
	Fonction racine pour convertir les docstring d'un module en items Dokiel.

Exemple du code Python permettant de générer les pages de la doc en ligne :
	```python
wsp = scapi.search_wsp_code(portal, title_fragment="Builder  - 6-4")
item = "item.xml"
sub_docs_api_local_dir = "docs.api"
sub_docs_api_wsp_dir = "/docPython/6_package_api"
sub_docs_portal_local_dir = "docs.portal"
sub_docs_portal_wsp_dir = "/docPython/7_package_portal"
samples_local_dir = "samples"
samples_wsp_dir = "/docPython/code/pyt_samples"

opts = {
	"links": {
		"[package-lib].api.search.Request": "/docPython/6_package_api/Request.scen",
		"[package-lib].api.item.JSendProps": "/docPython/6_package_api/JSendProps.scen",
		"[package-lib].portal.ScPortal": "/docPython/7_package_portal/ScPortal.scen",
		"scenaripy_lib.api.search.ELinkAxis": "/docPython/6_package_api/ELinkAxis.scen",
		"scenaripy_lib.api.item.EDrvState": "/docPython/6_package_api/EDrvState.scen",
		"scenaripy_lib.api.item.EDrfState": "/docPython/6_package_api/EDrfState.scen",
		"scenaripy_lib.api.item.ESrcField": "/docPython/6_package_api/ESrcField.scen",
		"scenaripy_lib.portal.new_portal": "/docPython/7_package_portal.scen"
	},
	"variables": {
		"[package-lib]": "/docPython/cond/package.var",
		"scenaripy_lib": "/docPython/cond/package.var"
	},
	"conds": {
		"assets_gc": "/docPython/cond/app_cond/has-assets.cond",
		"backup_pre": "/docPython/cond/app_cond/has-backup.cond",
		"backup_post": "/docPython/cond/app_cond/has-backup.cond",
		"backupinplace_pre": "/docPython/cond/app_cond/has-backupinplace.cond",
		"backupinplace_post": "/docPython/cond/app_cond/has-backupinplace.cond",
		"cmd_subportal": "/docPython/cond/app_cond/has-saas-prl.cond",
		"depot_backup_cleanup": "/docPython/cond/app_cond/has-depot-prl.cond",
		"depot_backup_delete": "/docPython/cond/app_cond/has-depot-prl.cond",
		"depot_backup_list": "/docPython/cond/app_cond/has-depot-prl.cond",
		"depot_backup_restore": "/docPython/cond/app_cond/has-depot-prl.cond",
		"list_clusters": "/docPython/cond/app_cond/has-clusters.cond",
		"list_edit_sessions": "/docPython/cond/app_cond/has-editSession.cond",
		"odb_checkauto": "/docPython/cond/app_cond/has-odb.cond",
		"odb_rebuild": "/docPython/cond/app_cond/has-odb.cond",
		"reload_clusters_conf": "/docPython/cond/app_cond/has-clusters.cond",
		"store_gc": "/docPython/cond/app_cond/has-store.cond",
		"strongbox_reset_scaccountpw": "/docPython/cond/app_cond/has-svcAccountInSb.cond"
	}
}

os.makedirs(samples_local_dir, exist_ok=True)
os.makedirs(sub_docs_api_local_dir, exist_ok=True)
os.makedirs(sub_docs_portal_local_dir, exist_ok=True)

scapi.__docstring2dokiel(module=scapi, file_path=item, sub_docs_dir=sub_docs_api_local_dir, sub_docs_prefix=sub_docs_api_wsp_dir, samples_dir=samples_local_dir, samples_path_prefix=samples_wsp_dir, opts=opts)
scapi.wsp_set_item(portal, wsp_code=wsp, ref_uri="/docPython/5_scenaripy_api.scen", local_file_path=item)

scapi.__docstring2dokiel(module=portal_api, file_path=item, sub_docs_dir=sub_docs_api_local_dir, sub_docs_prefix=sub_docs_api_wsp_dir, samples_dir=samples_local_dir, samples_path_prefix=samples_wsp_dir, opts=opts)
scapi.wsp_set_item(portal, wsp_code=wsp, ref_uri="/docPython/6_package_api.scen", local_file_path=item)

# Ajout du lien scenaripy_api pour faire référence à l'API
opts["links"]["scenaripy_api"] = "/docPython/5_scenaripy_api.scen"
scapi.__docstring2dokiel(module=scportal, file_path=item, sub_docs_dir=sub_docs_portal_local_dir, sub_docs_prefix=sub_docs_portal_wsp_dir, samples_dir=samples_local_dir, samples_path_prefix=samples_wsp_dir, opts=opts)
scapi.wsp_set_item(portal, wsp_code=wsp, ref_uri="/docPython/7_package_portal.scen", local_file_path=item)

for file in os.listdir(samples_local_dir):
	scapi.wsp_set_item(portal, wsp_code=wsp, ref_uri=f"{samples_wsp_dir}/{file}", local_file_path=f"{samples_local_dir}/{file}")

for file in os.listdir(sub_docs_api_local_dir):
	scapi.wsp_set_item(portal, wsp_code=wsp, ref_uri=f"{sub_docs_api_wsp_dir}/{file}", local_file_path=f"{sub_docs_api_local_dir}/{file}")

for file in os.listdir(sub_docs_portal_local_dir):
	scapi.wsp_set_item(portal, wsp_code=wsp, ref_uri=f"{sub_docs_portal_wsp_dir}/{file}", local_file_path=f"{sub_docs_portal_local_dir}/{file}")

shutil.rmtree(samples_local_dir)
shutil.rmtree(sub_docs_api_local_dir)
shutil.rmtree(sub_docs_portal_local_dir)
os.remove(item)
	```
	"""
	os.makedirs(samples_dir, exist_ok=True)
	with open(file_path, "w") as output:
		# 1 print module File
		output.write('<?xml version="1.0"?><sc:item xmlns:dk="kelis.fr:dokiel" xmlns:sc="http://www.utc.fr/ics/scenari/v3/core" xmlns:sp="http://www.utc.fr/ics/scenari/v3/primitive"><dk:section>')
		output.write(f'<dk:sectionM><sp:title><dk:richTitle><sc:para xml:space="preserve">Documentation : Module <sc:inlineStyle role="term">{__print_text(module.__name__[4:], opts)}</sc:inlineStyle></sc:para></dk:richTitle></sp:title></dk:sectionM>')

		__browse_module_docstring2dokiel(module, output, sub_docs_dir, sub_docs_prefix, samples_dir, samples_path_prefix, opts)

		output.write('</dk:section></sc:item>')


def __browse_module_docstring2dokiel(module, output, sub_docs_dir, sub_docs_prefix, samples_dir, samples_path_prefix, opts):
	# module is file. print module content
	for name, obj in inspect.getmembers(module):
		if (inspect.isfunction(obj) or inspect.isclass(obj)) and obj.__module__ == module.__name__:
			__print_module_docstring2dokiel(module, output, sub_docs_dir, sub_docs_prefix, samples_dir, samples_path_prefix, opts)
			break

	# module is package. Browse submodules
	for name, obj in inspect.getmembers(module):
		if inspect.ismodule(obj) and hasattr(obj, '__package__') and obj.__package__ == module.__name__:
			output.write('<sp:subSection><dk:section>')
			output.write(f'<dk:sectionM><sp:title><dk:richTitle><sc:para xml:space="preserve">Module <sc:inlineStyle role="term">{__print_text(obj.__name__[4:], opts)}</sc:inlineStyle></sc:para></dk:richTitle></sp:title></dk:sectionM>')
			__browse_module_docstring2dokiel(obj, output, sub_docs_dir, sub_docs_prefix, samples_dir, samples_path_prefix, opts)
			output.write('</dk:section></sp:subSection>')


def __print_module_docstring2dokiel(module, output, sub_docs_dir, sub_docs_prefix, samples_dir, samples_path_prefix, opts):
	# On affiche d'abord les fonctions
	output.write('<sp:content><dk:content>')
	if module.__doc__:
		output.write("<sp:infobloc><dk:blocTi/><dk:flowAll><sp:txt><dk:text>")
		lines = module.__doc__.split("\n")
		for line in lines:
			output.write(f'<sc:para xml:space="preserve">{__print_text(line, opts)}</sc:para>')
		output.write("</dk:text></sp:txt></dk:flowAll></sp:infobloc>")

	for name, obj in inspect.getmembers(module):
		if hasattr(obj, '__doc__') and obj.__doc__ is not None and inspect.isfunction(obj) and not name.startswith("_") and obj.__module__ == module.__name__:
			output.write('<sp:complement>')
			output.write(f'<dk:blocTi>')
			if name in opts["conds"]:
				output.write(f'<sp:filters><dk:filter><sp:condition><sp:cond sc:refUri="{opts["conds"][name]}"/></sp:condition></dk:filter></sp:filters>')
			output.write(f'<sp:rTitle><dk:richTitle><sc:para xml:space="preserve"><sc:inlineStyle role="term">{name}</sc:inlineStyle></sc:para></dk:richTitle></sp:rTitle></dk:blocTi>')
			output.write('<dk:flowAll><sp:txt><dk:text>')

			lines = getattr(module, name).__doc__.split("\n")

			sample_output = None
			for line in lines:
				if ":param" not in line and ":return:" not in line:
					if "```python" in line:
						sample_output = open(f"{samples_dir}/{name}.unit", "w")
						sample_output.write('<?xml version="1.0"?><sc:item xmlns:dk="kelis.fr:dokiel" xmlns:sc="http://www.utc.fr/ics/scenari/v3/core" xmlns:sp="http://www.utc.fr/ics/scenari/v3/primitive"><dk:code>')
						sample_output.write(f'<dk:codeM/><sc:code mimeType="text/x-python" xml:space="preserve">')
						output.write(f'<sc:extBlock role="fig" sc:refUri="{samples_path_prefix}/{name}.unit"/>')
					elif "```" in line and sample_output is not None:
						sample_output.write("</sc:code></dk:code></sc:item>")
						sample_output.close()
						sample_output = None
					elif sample_output is not None:
						sample_output.write(__print_text(line.strip()))
						sample_output.write("\n")
					else:
						output.write(f'<sc:para xml:space="preserve">{__print_text(line, opts)}</sc:para>')
			output.write('<sc:para xml:space="preserve">Paramètre(s) :</sc:para><sc:itemizedList>')
			for line in lines:
				if ":param" in line:
					extract_param_part = re.search(':param ([^:]+):(.+)', line)
					key = extract_param_part.group(1)
					doc = extract_param_part.group(2).strip()
					output.write(f'<sc:listItem><sc:para xml:space="preserve"><sc:inlineStyle role="term">{__print_text(key, opts)}</sc:inlineStyle> <sc:inlineStyle role="term">')
					if key in obj.__annotations__:
						type_name = str(obj.__annotations__[key])
						if type_name.startswith("<"):
							type_name = obj.__annotations__[key].__name__
						if type_name.startswith("typing"):
							type_name = type_name[7:]
						output.write(__print_text(f'<{type_name}>', opts))
					elif key == "portal":
						output.write(__print_text(f'<[package-lib].portal.ScPortal>', opts))
					elif key == "request":
						output.write(__print_text(f'<[package-lib].api.search.Request>', opts))
					output.write(f'</sc:inlineStyle> : {__print_text(doc, opts)}</sc:para></sc:listItem>')
			output.write('</sc:itemizedList>')
			for line in lines:
				if ":return:" in line:
					output.write(f'<sc:para xml:space="preserve">Retour : {__print_text(line[9:], opts)}</sc:para>')
			output.write('</dk:text></sp:txt></dk:flowAll></sp:complement>')
	output.write('</dk:content></sp:content>')

	# Puis les classes en sub section externalisée (pour y faire référence ailleurs dans la doc)
	for name, obj in inspect.getmembers(module):
		if hasattr(obj, '__doc__') and inspect.isclass(obj) and obj.__doc__ is not None and obj.__module__ == module.__name__ and obj.__doc__ != "An enumeration.":
			output.write(f'<sp:subSection sc:refUri="{sub_docs_prefix}/{name}.scen"/>')
			with open(f"{sub_docs_dir}/{name}.scen", "w") as sub_doc_output:
				sub_doc_output.write('<?xml version="1.0"?><sc:item xmlns:dk="kelis.fr:dokiel" xmlns:sc="http://www.utc.fr/ics/scenari/v3/core" xmlns:sp="http://www.utc.fr/ics/scenari/v3/primitive">')
				sub_doc_output.write('<dk:section>')
				sub_doc_output.write(f'<dk:sectionM><sp:title><dk:richTitle><sc:para xml:space="preserve">Classe : <sc:inlineStyle role="term">{name}</sc:inlineStyle></sc:para></dk:richTitle></sp:title></dk:sectionM>')
				sub_doc_output.write('<sp:content><dk:content>')

				sub_doc_output.write('<sp:infobloc><dk:blocTi/><dk:flowAll><sp:txt><dk:text>')
				lines = getattr(module, name).__doc__.split("\n")
				has_params = False
				sample_output = None
				for line in lines:
					if ":param" not in line:
						if "```python" in line:
							sample_output = open(f"{samples_dir}/{name}.unit", "w")
							sample_output.write('<?xml version="1.0"?><sc:item xmlns:dk="kelis.fr:dokiel" xmlns:sc="http://www.utc.fr/ics/scenari/v3/core" xmlns:sp="http://www.utc.fr/ics/scenari/v3/primitive"><dk:code>')
							sample_output.write(f'<dk:codeM/><sc:code mimeType="text/x-python" xml:space="preserve">')
							sub_doc_output.write(f'<sc:extBlock role="fig" sc:refUri="{samples_path_prefix}/{name}.unit"/>')
						elif "```" in line and sample_output is not None:
							sample_output.write("</sc:code></dk:code></sc:item>")
							sample_output.close()
							sample_output = None
						elif sample_output is not None:
							sample_output.write(__print_text(line.strip()))
							sample_output.write("\n")
						else:
							sub_doc_output.write(f'<sc:para xml:space="preserve">{__print_text(line, opts)}</sc:para>')
					else:
						has_params = True
				if has_params:
					sub_doc_output.write('<sc:para xml:space="preserve">Paramètre(s) accepté(s) par le constructeur :</sc:para><sc:itemizedList>')
					for line in lines:
						if ":param" in line:
							param = __print_text(line.split(":param ")[1], opts).split(":", 1)
							sub_doc_output.write(f'<sc:listItem><sc:para xml:space="preserve"><sc:inlineStyle role="term">{param[0]}</sc:inlineStyle> :{param[1]}</sc:para></sc:listItem>')
					sub_doc_output.write('</sc:itemizedList>')

				if issubclass(obj, Enum):
					sub_doc_output.write(f'<sc:para xml:space="preserve">Valeurs possibles : </sc:para><sc:itemizedList>')
					for field in obj:
						att_doc = __get_field_doc(obj, field.name)
						if att_doc is None or att_doc == "":
							continue
						if field.name == field.value:
							sub_doc_output.write(f'<sc:listItem><sc:para xml:space="preserve"><sc:inlineStyle role="term">{__print_text(field.name, opts)}</sc:inlineStyle>')
						else:
							sub_doc_output.write(f'<sc:listItem><sc:para xml:space="preserve"><sc:inlineStyle role="term">{__print_text(field.name, opts)}</sc:inlineStyle> (<sc:inlineStyle role="term">"{__print_text(str(field.value), opts)}"</sc:inlineStyle>)')

						sub_doc_output.write(f" : {__print_text(att_doc, opts)}")
						sub_doc_output.write("</sc:para></sc:listItem>")
					sub_doc_output.write('</sc:itemizedList>')

				elif obj.__class__.__name__ == "_TypedDictMeta":
					sub_doc_output.write(f'<sc:para xml:space="preserve">Champs de la structure de données : </sc:para><sc:itemizedList>')
					for key in obj.__annotations__:
						type_name = str(obj.__annotations__[key])
						if type_name.startswith("<"):
							type_name = obj.__annotations__[key].__name__
						if type_name.startswith("typing"):
							type_name = type_name[7:]
						sub_doc_output.write(f'<sc:listItem><sc:para xml:space="preserve"><sc:inlineStyle role="term">{__print_text(key, opts)}</sc:inlineStyle> ')
						sub_doc_output.write(f'<sc:inlineStyle role="term">{__print_text("<")}{__print_text(type_name, opts)}{__print_text(">")}</sc:inlineStyle>')
						att_doc = __get_field_doc(obj, key)
						if att_doc is not None and att_doc != "":
							sub_doc_output.write(f" : {__print_text(att_doc, opts)}")
						sub_doc_output.write("</sc:para></sc:listItem>")

					sub_doc_output.write('</sc:itemizedList>')
				has_methods = False
				for fun_name, fun_obj in inspect.getmembers(obj):
					if hasattr(fun_obj, '__doc__') and fun_obj.__doc__ is not None and inspect.isfunction(fun_obj) and not fun_name.startswith(
							"_") and fun_obj.__module__ == module.__name__:
						if not has_methods:
							sub_doc_output.write(f'<sc:para xml:space="preserve"><sc:inlineStyle role="emphasis">Méthodes disponibles :</sc:inlineStyle></sc:para>')
							sub_doc_output.write('</dk:text></sp:txt></dk:flowAll></sp:infobloc>')
							has_methods = True
						sub_doc_output.write('<sp:complement>')
						sub_doc_output.write(f'<dk:blocTi>')
						if fun_name in opts["conds"]:
							sub_doc_output.write(f'<sp:filters><dk:filter><sp:condition><sp:cond sc:refUri="{opts["conds"][fun_name]}"/></sp:condition></dk:filter></sp:filters>')
						sub_doc_output.write(f'<sp:rTitle><dk:richTitle><sc:para xml:space="preserve"><sc:inlineStyle role="term">{fun_name}</sc:inlineStyle></sc:para></dk:richTitle></sp:rTitle></dk:blocTi>')
						sub_doc_output.write('<dk:flowAll><sp:txt><dk:text>')

						lines = getattr(obj, fun_name).__doc__.split("\n")
						for line in lines:
							if ":param" not in line and ":return:" not in line:
								sub_doc_output.write(f'<sc:para xml:space="preserve">{__print_text(line, opts)}</sc:para>')
						sub_doc_output.write('<sc:para xml:space="preserve">Paramètre(s) :</sc:para><sc:itemizedList>')
						for line in lines:
							if ":param" in line:
								param = __print_text(line.split(":param ")[1], opts).split(":", 1)
								sub_doc_output.write(f'<sc:listItem><sc:para xml:space="preserve"><sc:inlineStyle role="term">{param[0]}</sc:inlineStyle>')
								annotations = getattr(obj, fun_name).__annotations__
								if param[0] in annotations:
									type_name = str(annotations[param[0]])
									if type_name.startswith("<"):
										type_name = annotations[param[0]].__name__
									if type_name.startswith("typing"):
										type_name = type_name[7:]
									sub_doc_output.write(__print_text(f' <{type_name}>', opts))
								sub_doc_output.write(f' :{param[1]}</sc:para></sc:listItem>')
						sub_doc_output.write('</sc:itemizedList>')
						for line in lines:
							if ":return:" in line:
								sub_doc_output.write(f'<sc:para xml:space="preserve">Retour : {__print_text(line.split(":return: ")[1], opts)}</sc:para>')
						sub_doc_output.write('</dk:text></sp:txt></dk:flowAll></sp:complement>')

				if not has_methods:
					sub_doc_output.write('</dk:text></sp:txt></dk:flowAll></sp:infobloc>')
				sub_doc_output.write('</dk:content></sp:content></dk:section></sc:item>')
	return


def __print_text(text, opts=None):
	escaped = xml.sax.saxutils.escape(text.replace(" [exclude]", ""))
	if opts is not None:
		if opts["links"] is not None:
			for lnk in opts["links"]:
				escaped = escaped.replace(lnk, f'<sc:uLink role="coLnk" sc:refUri="{opts["links"][lnk]}">{lnk}</sc:uLink>')
		if opts["variables"] is not None:
			for var in opts["variables"]:
				escaped = escaped.replace(var, f'<sc:objectLeaf role="variable" sc:refUri="{opts["variables"][var]}"/>')
	escaped = re.sub('`([^`]+)`', r'<sc:inlineStyle role="term">\1</sc:inlineStyle>', escaped)
	return escaped


def __get_field_doc(obj, field_name):
	for line in inspect.getsourcelines(obj)[0]:
		if line.lstrip().startswith(field_name) and "[NON API]" not in line and "#" in line:
			return line[line.index("#") + 1:].lstrip()
	return None
