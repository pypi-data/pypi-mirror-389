"""Ce module contient les classes permettant de construire une requête pour le moteur de recherche d'un atelier. Une requête est matérialisée par un objet `Request` et est composée de critère (objets Search...)."""

from typing import List, Optional

from .item import EItemPrefix, EDrfState, EDrvState, ESrcField
from ..common.utils import StrEnum
from xml.sax.saxutils import escape


class ELinkAxis(StrEnum):
	"""Axes de recherche dans le réseau d'item"""
	LinkChildren = "LinkChildren"  # Parcours vers les items fils (items référencés par l'item passé en paramètre).
	LinkParents = "LinkParents"  # Parcours vers les items parents (items qui font un lien vers l'item passé en paramètre).
	LinkAsc = "LinkAsc"  # Parcours de toute l'arborescence ascendantes.
	LinkDesc = "LinkDesc"  # Parcours de toute l'arborescence descendante.


class EResultType(StrEnum):
	entries = "entries"
	count = "count"


class ISearchCrit:
	def serialize(self) -> str:
		pass


class Request:
	"""
	Objet à passer en paramètre au moteur de recherche pour lancer une requête.
	Exemple d'appels :
	```python
	crit = SearchItemComment()
	request = Request(criterions=crit)
	request = Request(criterions=crit, number_of_results=10)
	request = Request(criterions=crit, number_of_results=10, start_offset=10)
	request = Request(criterions=crit, columns = [ESrcField.srcUri, ESrcField.itTi, ESrcField.lcSt])
	```

	:param criterions: critère ou liste de critères de recherche
	:param number_of_results: nombre de résultats demandés (100 par défaut)
	:param start_offset: premier résultat à partir duquel récupérer les réponses (0 par défaut)
	:param columns: liste des champs à récupérer (par défaut, le chemin, le titre de l'item et le modèle associé à l'item). Voir la liste des champs disponibles dans item scenaripy_lib.api.item.ESrcField
	"""
	def __init__(self, criterions: List[ISearchCrit] | ISearchCrit, number_of_results: int = 100, start_offset: int = 0, columns: Optional[List[ESrcField]] = None):
		self._searchCrits: List[ISearchCrit] = []
		if isinstance(criterions, list):
			self._searchCrits = criterions
		else:
			self._searchCrits.append(criterions)
		self._columns: List[ESrcField] = [ESrcField.srcUri, ESrcField.itTi, ESrcField.itModel] if columns is None else columns
		self._max: int = number_of_results
		self._startOffset: int = start_offset

	def serialize(self, result_type: EResultType = EResultType.entries) -> str:
		request = f'<request><select resultType="{result_type}" max="{self._max}" startOffset="{self._startOffset}">'
		for field in self._columns:
			request += f'<column dataKey="{field}"/>'
		request += "</select><where>"
		for searchCrit in self._searchCrits:
			request += searchCrit.serialize()
		request += "</where></request>"
		return request


class SearchAnd(ISearchCrit):
	"""
	Liste de sous-critères devant tous être satisfaits pour qu'une source soit sélectionnée.
	Exemple :
	```python
	critA = ...
	critB = ...
	crit = SearchAnd()
	crit.append(critA)
	crit.append(critB)
	```
	"""
	_searchCrits: List[ISearchCrit] = []

	def append(self, crit: ISearchCrit):
		""" Ajout d'un critère de recherche à ce critère AND.

		:param crit: Le critère à ajouter
		"""
		self._searchCrits.append(crit)

	def serialize(self) -> str:
		request = "<and>"
		for searchCrit in self._searchCrits:
			request += searchCrit.serialize()
		request += "</and>"
		return request


class SearchOr(ISearchCrit):
	"""
		Liste de sous-critères dont au moins un doit être satisfait pour qu'une source soit sélectionnée.
		Exemple :
		```python
		critA = ...
		critB = ...
		crit = SearchOr()
		crit.append(critA)
		crit.append(critB)
		```
		"""
	_searchCrits: List[ISearchCrit] = []

	def append(self, crit: ISearchCrit):
		""" Ajout d'un critère de recherche à ce critère OR.

		:param crit: Le critère à ajouter
		"""
		self._searchCrits.append(crit)

	def serialize(self) -> str:
		request = "<or>"
		for searchCrit in self._searchCrits:
			request += searchCrit.serialize()
		request += "</or>"
		return request


class SearchNot(ISearchCrit):
	"""
		Liste de sous-critères ne devant pas être satisfaits pour qu'une source soit sélectionnée.
		Exemple :
		```python
		critA = ...
		critB = ...
		crit = SearchNot()
		crit.append(critA)
		crit.append(critB)
		```
		"""
	_searchCrits: List[ISearchCrit] = []

	def append(self, crit: ISearchCrit):
		""" Ajout d'un critère de recherche à ce critère NOT.

		:param crit: Le critère à ajouter
		"""
		self._searchCrits.append(crit)

	def serialize(self) -> str:
		request = "<not>"
		for searchCrit in self._searchCrits:
			request += searchCrit.serialize()
		request += "</not>"
		return request


class SearchFree(ISearchCrit):
	"""
	Critère "free" en XML.
	Exemple :
	```python
	crit = SearchFree("<and>...</and>")
	```
	"""
	def __init__(self, request: str):
		self._request: str = request

	def serialize(self) -> str:
		return self._request


class SearchAirItems(ISearchCrit):
	"""Recherche d'un air item.
	Exemple :
	```python
	crit = SearchAirItems()
	```
	"""
	def serialize(self) -> str:
		return '<exp type="ItemsInAir"/>'


class SearchForeignItems(ISearchCrit):
	"""Recherche d'un item étranger (item public importé dans l'atelier.
	Exemple :
	```python
	crit = SearchForeignItems()
	```
	"""
	def serialize(self) -> str:
		return '<exp type="ItemExternals"/>'


class SearchItemModel(ISearchCrit):
	"""
	Recherche d'un item par son modèle.
	Le constructeur accepte une string ou une liste en paramètre.
	Exemple :
	```python
	crit = SearchItemModel(models = "dk_concept")
	crit = SearchItemModel(models = ["dk_concept", "dk_screen"])
	```
	"""
	def __init__(self, models: str | List[str]):
		self._models: List[str] = []
		if type(models) is str:
			self._models.append(models)
		else:
			self._models.extend(models)

	def serialize(self) -> str:
		return f'<exp type="ItemModel" models="{escape(" ".join(self._models))}"/>'


class SearchLastUser(ISearchCrit):
	"""Recherche par le dernier utilisateur ayant modifié l'item.
	Exemple :
	```python
	crit = SearchLastUser(users="mon-user")
	crit = SearchLastUser(users=["mon-user1", "mon-user2"])
	```

	:param users: string ou liste de string avec les comptes ou pseudo des utilisateurs.
	"""
	def __init__(self, users: List[str] | str):
		self._users: List[str] = []
		if type(users) is str:
			self._users.append(users)
		else:
			for user in users:
				self._users.append(user)

	def serialize(self) -> str:
		return f'<exp type="LastUser" users="{escape(" ".join(self._users))}"/>'


class SearchItems(ISearchCrit):
	"""Critère générique pour définir une portée de recherche sur un ensemble d'item.
	Exemple :
	```python
	crit = SearchItems()
	crit.in_space("/mon_espace")
	crit...
	```
	"""
	def __init__(self, after_uri: Optional[str] = "/", before_uri: Optional[str] = None, exclude: Optional[List[str]] = None, exclude_except: Optional[List[str]] = None,  with_drf_erased: Optional[bool] = None):
		self._afterUri: Optional[str] = after_uri
		self._beforeUri: Optional[str] = before_uri
		self._exclude: Optional[List[str]] = exclude
		self._excludeExcept: Optional[List[str]] = exclude_except
		self._withDrfErased: Optional[bool] = with_drf_erased
		self._beforeEndFolder: Optional[str] = None

	def in_space(self, uri: str):
		"""
		Pour rechercher dans un espace.
		:param uri: chemin vers l'espace dans lequel rechercher
		"""
		self._afterUri = uri + '/'
		self._beforeUri = None
		self._beforeEndFolder = self._afterUri

	def exclude_tilde_root(self):
		if self._exclude is not None:
			for u in self._exclude:
				if u.startswith("/~"):
					self._exclude.remove(u)
		else:
			self._exclude = []
		self._exclude.append("/~")

	def set_air_items_inclusion(self, exclude: bool = True):
		"""
		Exclut ou réinclut (si isTildeRootExcluded()) les airItems.
		:param exclude: `True` par défaut
		"""
		if "/~" in self._exclude:
			if not exclude:
				self.exclude_except_spaces(EItemPrefix.AIR_PREFIX.value)
			elif self._excludeExcept is not None:
				self._excludeExcept.remove(EItemPrefix.AIR_PREFIX.value)
		else:
			if self._exclude is None:
				self._exclude = []
				self._exclude.append(EItemPrefix.ANNOT_PREFIX.value)
			if exclude:
				self._exclude.append(EItemPrefix.AIR_PREFIX.value)
			else:
				self._exclude.remove(EItemPrefix.AIR_PREFIX.value)

	def set_ext_items_inclusion(self, exclude: bool = True):
		"""
		Exclut ou réinclut (si isTildeRootExcluded()) les extItems.
		:param exclude: `True` par défaut
		"""
		if "/~" in self._exclude:
			if not exclude:
				self.exclude_except_spaces(EItemPrefix.EXT_PREFIX.value)
			elif self._excludeExcept is not None:
				self._excludeExcept.remove(EItemPrefix.EXT_PREFIX.value)
		else:
			if self._exclude is None:
				self._exclude = []
				self._exclude.append(EItemPrefix.ANNOT_PREFIX.value)
			if exclude:
				self._exclude.append(EItemPrefix.EXT_PREFIX.value)
			else:
				self._exclude.remove(EItemPrefix.EXT_PREFIX.value)

	def exclude_spaces(self, *space_uris: str | List[str]):
		"""
		Exclut n'importe quel espace (voir un item).
		:param space_uris: string ou liste contenant les chemins vers les espaces à exclure
		"""
		for space_uri in space_uris:
			if self._exclude is None:
				self._exclude = []
				self._exclude.append(EItemPrefix.ANNOT_PREFIX.value)
			if type(space_uri) is str:
				self._exclude.append(space_uri if space_uri.endswith("/") else space_uri + "/")
			else:
				for uri in space_uri:
					self._exclude.append(uri if uri.endswith("/") else uri + "/")

	def exclude_except_spaces(self, *space_uris: str | List[str]):
		"""
		Exception dans les espaces à exclure.
		:param space_uris: string ou liste contenant les chemins vers les espaces à exclure
		"""
		for space_uri in space_uris:
			if self._excludeExcept is None:
				self._excludeExcept = []
			if type(space_uri) is str:
				self._excludeExcept.append(space_uri if space_uri.endswith("/") else space_uri + "/")
			else:
				for uri in space_uri:
					self._excludeExcept.append(uri if uri.endswith("/") else uri + "/")

	def serialize(self) -> str:
		exp = '<exp type="Items" '
		if self._afterUri is not None:
			exp += f'afterUri="{escape(self._afterUri)}" '
		if self._beforeUri is not None:
			exp += f'beforeUri="{escape(self._beforeUri)}" '
		if self._beforeEndFolder is not None:
			exp += f'beforeEndFolder="{escape(self._beforeEndFolder)}" '
		if self._exclude is not None:
			exp += f'exclude="{escape(";".join(self._exclude))}" '
		if self._excludeExcept is not None:
			exp += f'excludeExcept="{escape(";".join(self._excludeExcept))}" '
		if self._withDrfErased is not None:
			exp += f'includeDrfErased="{self._withDrfErased}" '
		exp += "/>"
		return exp


class SearchItemLinks(ISearchCrit):
	"""Critère de parcours du réseau d'items.

	Exemple :
	```python
	crit = SearchItemLinks(link_axis=ELinkAxis.LinkAsc, ref_uri="/path/vers/ma/ressource")
	crit.set_link_name("filter")
	crit...
	```

	:param link_axis: un axe de parcours dur réseau (voir scenaripy_lib.api.search.ELinkAxis pour les axes disponibles)
	:param ref_uri: chemin ou identifiant de l'item à partir duquel parcourir le réseau d'items
	"""
	def __init__(self, link_axis: ELinkAxis, path: Optional[str] = None, ref_uri: Optional[str] = None, link_name: Optional[str] = None, link_name_pattern: Optional[str] = None, link_trait_filter: Optional[str] = None):
		self._linkAxis: ELinkAxis = link_axis

		if path is not None and ref_uri is not None:
			raise ValueError("Only one of the path or ref_uri parameters could be defined")

		self._path: Optional[str] = path
		self._refUri: Optional[str] = ref_uri

		if link_name is not None and link_name_pattern is not None or link_name_pattern is not None and link_trait_filter is not None or link_name is not None and link_trait_filter is not None:
			raise ValueError("Only one of the link_name, link_name_pattern or link_trait_filter parameters could be defined")

		self._linkName: Optional[str] = link_name
		self._linkNamePattern: Optional[str] = link_name_pattern
		self._linkTraitFilter: Optional[str] = link_trait_filter

	def set_link_name(self, link_name: str):
		"""
		Restriction sur le nom du lien (ce nom peut être défini dans le modèle documentaire).
		:param link_name: string contenant le nom du lien.
		"""
		self._linkName = link_name
		self._linkNamePattern = None
		self._linkTraitFilter = None

	def set_link_name_pattern(self, link_name_pattern: str):
		"""
		Expression régulière pour exprimer des restrictions sur les noms des liens (ces noms peuvent être définis dans le modèle documentaire).
		:param link_name_pattern: string contenant l'expression régulière (Java) sur les noms de liens.
		"""
		self._linkName = None
		self._linkNamePattern = link_name_pattern
		self._linkTraitFilter = None

	def set_link_trait_filter(self, link_trait_filter: str):
		"""
		Restriction sur le caractère du lien (ce caractère peut être défini dans le modèle documentaire).
		:param link_trait_filter: string contenant le caractère du lien
		"""
		self._linkName = None
		self._linkNamePattern = None
		self._linkTraitFilter = link_trait_filter

	def serialize(self) -> str:
		exp = f'<exp type="{escape(self._linkAxis.value)}" '
		if self._linkName is not None:
			exp += f'linkName="{escape(self._linkName)}" '
		if self._linkNamePattern is not None:
			exp += f'linkNamePattern="{escape(self._linkNamePattern)}" '
		if self._linkTraitFilter is not None:
			exp += f'linkTraitFilter="{escape(self._linkTraitFilter)}" '
		if self._refUri is None:
			exp += f'path="{"" if self._path is None else escape(self._path)}" '
		exp += ">"

		if self._refUri is not None:
			exp += f'<path func="RefUri2Path" sc:refUri="{escape(self._refUri)}"/>'
		exp += "</exp>"

		return exp


class SearchFullText(ISearchCrit):
	"""
	Recherche plein texte dans les items.
	```python
	crit = SearchFullText(text_search="Thé", ignore_case=True, whole_word=True)
	crit = SearchFullText(text_search="Thé")
	```
	:param text_search: le texte recherché
	:param ignore_case: indiquer `True` pour ignorer la casse dans la recherche (`False` par défaut)
	:param whole_word: indiquer `True` pour ne chercher que des mots complets (`False` par défaut)
	"""
	def __init__(self, text_search: str, ignore_case: bool = False, whole_word: bool = False):
		self._textSearch: str = text_search
		self._ignoreCase: bool = ignore_case
		self._wholeWord: bool = whole_word

	def serialize(self) -> str:
		if self._ignoreCase:
			opts = ";c;w;" if self._wholeWord else ";c;"
		elif self._wholeWord:
			opts = ";w;"
		else:
			opts = ""
		return f'<exp type="FullText" textSearch="{escape(self._textSearch)}" options="{opts}"/>'


class SearchRegExpUri(ISearchCrit):
	"""
	Recherche par une expression régulière sur le chemin vers l'item.

	```python
	crit = SearchRegExpUri(regexp="/.*.png",)
	```

	:param regexp: string contenant l'expression régulière (pour Java)
	"""
	def __init__(self, regexp: str):
		self._regexp: str = regexp

	def serialize(self) -> str:
		return f'<exp type="RegexpUri" regexp="{escape(self._regexp)}"/>'


class SearchFullXPath(ISearchCrit):
	"""
	Recherche par XPath.

	```python
	crit = SearchFullXPath(xpath="//sc:inlineStyle[@role='textCheckBox']")
	crit = SearchFullXPath(xpath="//dk:part", ns={"dk":"kelis.fr:dokiel"})
	```

	:param xpath: string contenant l'XPath de recherche.
	:param ns: dictionnaire contenant les namespaces du modèle sous la forme `"code":"uri"` (les namespaces du cœur SCENARI sont déjà déclarés)
	"""
	def __init__(self, xpath: str, ns: Optional[dict[str, str]] = None):
		self._xpath: str = xpath
		self._ns: dict[str, str] = {
			"sp": "http://www.utc.fr/ics/scenari/v3/primitive",
			"sc": "http://www.utc.fr/ics/scenari/v3/core"
		}
		if ns is not None:
			for key in ns:
				self._ns[key] = ns[key]

	def serialize(self) -> str:
		exp = f'<exp type="FullXPath" xpathSearch="{escape(self._xpath)}">'
		for ns in self._ns:
			exp += f'<ns prefix="{escape(ns)}" uri="{escape(self._ns[ns])}"/>'
		exp += "</exp>"
		return exp


class SearchItemTitleRegexp(ISearchCrit):
	"""
	Recherche par expression régulière dans les titres des items.
	```python
	crit = SearchItemTitleRegexp(regexp="Th(é|e)")
	```

	:param regexp: string contenant l'expression régulière (pour Java)
	"""
	_regexp: str

	def __init__(self, regexp: str):
		"""
		:param regexp: string contenant l'expression régulière (pour Java)
		"""
		self._regexp = regexp

	def serialize(self) -> str:
		return f'<exp type="ItemTitleRegexp" regexp="{escape(self._regexp)}"/>'


class SearchItemCodeOrTitle(SearchItemTitleRegexp):
	"""
	Recherche par expression régulière dans les codes ou titre des items.
	```python
	crit = SearchItemCodeOrTitle(regexp="(T|t)h(é|e)")
	```

	:param regexp: string contenant l'expression régulière (pour Java)
	"""
	def serialize(self) -> str:
		return f'<exp type="ItemCodeOrTitle" regexp="{escape(self._regexp)}"/>'


class SearchOrphan(ISearchCrit):
	"""
	Recherche d'items orphelins (items qui ne sont référencés par aucun autre item).
	```python
	crit = SearchOrphan()
	```
	"""
	def serialize(self) -> str:
		return '<exp type="ItemOrphan"/>'


class SearchItemComment(ISearchCrit):
	"""
	Recherche d'item contenant des commentaires.
	```python
	crit = SearchItemComment()
	```
	:param with_open_comments: Booléen pour inclure/exclure les commentaires ouverts
	:param with_closed_comments: Booléen pour inclure/exclure les commentaires ouverts
	"""
	def __init__(self, with_open_comments: bool = True, with_closed_comments: bool = True):
		self._withOpenComments: bool = with_open_comments
		self._withClosedComments: bool = with_closed_comments
		if with_open_comments and not with_closed_comments:
			raise ValueError("One of the parameters with with_open_comments or with_closed_comments must be True")

	def serialize(self) -> str:
		if self._withOpenComments and not self._withClosedComments:
			raise ValueError("One of parameters with with_open_comments or with_closed_comments must be True")
		xpath = "descendant::comment()[matchesRegex(normalize-space(.), '<comment.*')]"
		if self._withClosedComments and not self._withOpenComments:
			xpath += "[matchesRegex(normalize-space(.), '<comment[^>]*threadClosed=.true.[^>]*>.*')]"
		elif not self._withClosedComments and self._withOpenComments:
			xpath += "[not(matchesRegex(normalize-space(.), '<comment[^>]*threadClosed=.true.[^>]*>.*'))]"
		return f'<exp type="FullXPath" xpathSearch="{escape(xpath)}"/>'


class SearchDrfStates(ISearchCrit):
	"""
	Recherche par l'état de surcharge dans l'atelier calque de travail.
	```python
	crit = SearchDrfStates(drf_states=EDrfState.overriden)
	crit = SearchDrfStates(drf_states=[EDrfState.overriden, EDrfState.erased])
	```

	:param drf_states: un état ou une liste d'états dans lesquels rechercher (voir scenaripy_lib.api.item.EDrfState pour la liste des états)
	"""
	def __init__(self, *drf_states: EDrfState | List[EDrfState]):
		self._drfStates: List[EDrfState] = []
		for state in drf_states:
			if type(state) is EDrfState:
				self._drfStates.append(state)
			else:
				self._drfStates.extend(state)

	def serialize(self) -> str:
		strings: List[str] = []
		for state in self._drfStates:
			strings.append(state.value)
		return f'<exp type="DrfStates" drfStates="{escape(" ".join(strings))}"/>'


class SearchDrvStates(ISearchCrit):
	"""
	Recherche par l'état de surcharge dans l'atelier de dérivation.
	```python
	crit = SearchDrfStates(drv_states=EDrvState.overridenDone)
	crit = SearchDrfStates(drv_states=[EDrvState.overridenDone, EDrvState.overridenDirty])
	```

	:param drv_states: un état ou une liste d'états dans lesquels rechercher (voir scenaripy_lib.api.item.EDrvState pour la liste des états)
	"""

	_drvStates: List[EDrvState] = []

	def __init__(self, *drv_states: EDrvState | List[EDrvState]):
		for state in drv_states:
			if type(state) is EDrvState:
				self._drvStates.append(state)
			else:
				self._drvStates.extend(state)

	def serialize(self) -> str:
		strings: List[str] = []
		for state in self._drvStates:
			strings.append(state.value)
		return f'<exp type="DrvStates" drvStates="{escape(" ".join(strings))}"/>'
