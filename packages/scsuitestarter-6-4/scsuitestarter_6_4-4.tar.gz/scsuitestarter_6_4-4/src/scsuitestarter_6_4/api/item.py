"""Ce module contient des constantes (sous forme d'Enum) et structures de données (préfixe pour items spécifiques, statuts de dérivation ou de calque de travail, champs de description d'un item et structure de données spécifique aux exports pour envoi des données)."""

from typing import TypedDict, Optional

from ..common.utils import StrEnum

class EItemPrefix(StrEnum):
    """Liste de valeurs de préfixe d'un chemin vers un item (src_uri). Les fonctions adressées par ces préfixes sont disponibles en DB uniquement."""
    AIR_PREFIX = "/~air/"  # Préfixe d'un air item
    """Test attribute doc"""
    EXT_PREFIX = "/~ext/"  # Préfixe d'un item externe
    TRANSIENT_PREFIX = "/~transient/"
    ANNOT_PREFIX = "/~annot/"
    HISTORY_PREFIX = "/~history/"  # Préfixe d'un item en historique
    TRASH_PREFIX = "/~history~trash/"  # Préfixe d'un item en corbeille


class EDrvState(StrEnum):
    """État d'un item dans un atelier dérivé."""
    erased = "erased"  # Item supprimé
    notOverriden = "notOverriden"  # Item non surchargé, jamais marqué "achevé"
    notOverridenDone = "notOverridenDone"  # Item non surchargé, marqué achevé
    createdDone = "createdDone"  # Item spécifique à l'atelier dérivé, marqué achevé
    overridenDone = "overridenDone"  # Item surchargé dans l'atelier dérivé, marqué achevé
    createdNew = "createdNew"  # Item spécifique à l'atelier dérivé, mais non marqué achevé
    overridenNew = "overridenNew"  # Item surchargé dans l'atelier dérivé, mais non marqué achevé
    notOverridenDirty = "notOverridenDirty"  # Item non surchargé, marqué achevé puis déphasé
    createdDirty = "createdDirty"  # Item spécifique à l'atelier dérivé, marqué achevé puis déphasé
    overridenDirty = "overridenDirty"  # Item surchargé dans l'atelier dérivé, marqué achevé puis déphasé
    createdNotComputed = "createdNotComputed"  # Item spécifique à l'atelier dérivé, état inconnu
    notComputed = "notComputed"  # État de l'item inconnu


class EDrfState(StrEnum):
    """État d'un item dans un atelier calque de travail."""
    erased = "erased"  # Item supprimé
    notOverriden = "notOverriden"  # Item inchangé
    overriden = "overriden"  # Item modifié
    created = "created"  # Item créé dans l'atelier calque
    createdDeleted = "createdDeleted"  # Item créé puis supprimé
    notComputed = "notComputed"  # État de l'item inconnu


class ESrcField(StrEnum):
    """Liste des champs de données possiblement associés à un item."""
    # NB : seuls les champs commentés avec le caractère # ont valeur d'API.
    srcUri = "srcUri"  # Chemin de l'item.
    srcId = "srcId"  # ID d'un item (attention, un ID n'est pas stable). [NON API]
    itSubItem = "itSubItem"  # XML ID d'un sub-item. Supporté par certains modèles uniquement. [NON API]

    item = "item"  # demande à a fois : itSt, itSgn, itModel [NON API]
    sdOdb = "sdOdb"  # demande à la fois : srcUri, srcSt, srcDt, srcRi, srcRoles, srcId, srcStamp, srcUser, itSt, itSgn et itModel [NON API]

    srcNm = "srcNm"  # Retourne le nom de la ressource. [NON API]
    srcSt = "srcSt"  # Retourne le status de la ressource (de type int, 1 pour un fichier, 2 pour un dossier et -1 si la ressource n'existe pas). [NON API]
    srcDt = "srcDt"  # `Timestamp` de dernière modification.
    srcStamp = "srcStamp"  # Retourne une chaîne d'empreinte (hash) du contenu. [NON API]
    srcTreeDt = "srcTreeDt"  # Retourne la date de dernière modification de la ressource et son arborescence fille. [NON API]
    srcSi = "srcSi"  # Retourne la taille du contenu. [NON API]
    srcTy = "srcTy"  # Retourne le content-type associé à ce contenu. [NON API]
    srcRi = "srcRi"  # Retourne les droits d'accès sous la forme d'un int. Ce champ est un indice utilisé par l'IHM Scenari. Ne pas utiliser en dehors. [NON API]
    srcRoles = "srcRoles"  # Retourne les rôles résolus pour cette ressource. [NON API]
    srcUser = "srcUser"  # Utilisateur ayant effectué la dernière modification.
    srcLiveUri = "srcLiveUri"  # URL "live" d'un nœud placé en historique ou supprimé. [NON API]
    srcTrashed = "srcTrashed"  # srcTrashed pour savoir si ce nœud a été explicitement placé en corbeille (contrairement à `srcSt` qui renvoie -1 si le nœud OU au moins un nœud de son contexte ascendant a été supprimé). [NON API]
    metaComment = "metaComment"  # Pour récupérer un commentaire associé à cet item (pour une entrée d'historique par exemple). [NON API]
    metaFlag = "metaFlag"  # Flag (retourné sous forme de int) associé à cet item (pour une entrée d'historique par exemple). [NON API]

    cidEndPoints = "cidEndPoints"  # Liste des dernières destination d'envoi via CID de cet item. [NON API]

    drvState = "drvState"  # État de dérivation.
    drvAxisDefCo = "drvAxisDefCo"  # Axis auquel appartient le contenu par défaut de cette dérivation.

    drfState = "drfState"  # État de surcharge dans un atelier calque de travail.

    itTi = "itTi"  # Titre d'un item.
    itSt = "itSt"  # Statut d'un item (-1 : n'existe pas, -2 : item en conflit, -99 : statut inconnu, 1 : statut ok, 2 : contient des warnings, 3, item en erreur, 11 : état asynchrone d'un item en cours de validation). [NON API]
    itSgn = "itSgn"  # Signature de l'item. [NON API]
    itModel = "itModel"  # Code du modèle associé à l'item
    itFullUriInOwnerWsp = "itFullUriInOwnerWsp"  # fullUri d'un item dans son atelier propriétaire. Utilisé par l'atelier qui inclut un item externe. [NON API]
    itSubItems = "itSubItems"  # Liste des sub-items contenu dans cet item. [NON API]
    itSubItemAnc = "itSubItemAnc"  # Permet d'obtenir la liste des propriétés des subItems ancêtres du subItem pointé. [NON API]

    lcSt = "lcSt"  # État du cycle de vie.
    lcDt = "lcDt"  # Date du dernier changement de cycle de vie.
    lcBy = "lcBy"  # Utilisateur ayant déclenché le dernier changement de cycle de vie.
    lcTrP = "lcTrP"  # True si une transition est en cours. [NON API]

    rspUsrs = "rspUsrs"  # Pour obtenir une liste des users et de leurs responsabilités associés à un item donné. [NON API]
    rspSt = "rspSt"  # Statut des responsabilité de l'item (-1 : inconnu, 1 : ok, 3 : en erreur). [NON API]

    tkPending = "tkPending"  # La tâche est en cours. [NON API]
    tkPendingCount = "tkPendingCount"  # Nombre de tâches en cours associées à une source. [NON API]
    tkForthcoming = "tkForthcoming"  # La tâche est planifiée. [NON API]
    tkForthcomingCount = "tkForthcomingCount"  # Nombre de tâches planifiées associées à une source. [NON API]

    tkDeadline = "tkDeadline"  # Deadline de la tâche. [NON API]
    tkCompletedDt = "tkCompletedDt"  # Date du passage à l'état complété de la tâche. [NON API]
    tkCompletedBy = "tkCompletedBy"  # User qui a passé la tâche à l'état complété. [NON API]

    actStage = "actStage"  # État de l'action (completed, pending, forthcoming). [NON API]
    actTi = "actTi"  # Titre de l'action. [NON API]
    actCts = "actCts"  # Liste des source liées à cette action. [NON API]

    wspOwner = "wspOwner"  # Code de l'atelier propriétaire de la source. [NON API]


class JSendProps(TypedDict):
    """
    Structure de données permettant de spécifier un envoi de contenu HTTP via le service remoteContent de Scenari.
    """
    url: str
    method: Optional[str]  # Valeur par défaut : "GET"
    timeout: Optional[int]  # Pas de `timeout` par défaut
    headerProps: Optional[dict[str, str | list[str]]]
    addQSParams: Optional[dict[str, str]]  # Ajout de querystring en plus de ceux possiblement présents dans l'URL
    setQSParams: Optional[dict[str, str]]  # Remplacement de querystring déjà présent dans l'URL
