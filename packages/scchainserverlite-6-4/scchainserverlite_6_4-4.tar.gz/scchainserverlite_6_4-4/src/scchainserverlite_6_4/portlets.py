# -*- coding: UTF-8 -*-
import logging
import sys
from typing import Optional, Any, TypedDict

import requests

from .appsaas.admininst import AdminInst
from .common.utils import StrEnum
from .core.adminserver import AdminServer
from .core.adminuser import AdminUser
from .appsaas.dptresinstmgr import DptResInstMgr
from .appsaas.instsbackupinplace import InstsBackupInPlace
from .appsaas.instsclustermgr import InstsClusterMgr
from .core.actlogjson import ActlogJson
from .core.backup import Backup
from .core.backupinplace import BackupInPlace
from .core.executor import Executor
from .core.maintenance import Maintenance
from .core.ping import Ping
from .core.strongbox import Strongbox
from .distrib.actor import Actor
from .distrib.engine import DistribEngine
from .distrib.participant import Participant
from .distrib.projectAdmin import ProjectAdmin
from .distrib.projectsonres import ProjectsOnResMgr
from .orient.adminodb import AdminOdb
from .store.assetsctrl import AssetsCtrl
from .store.cidserver import CidServer
from .store.storesquare import StoreSquare
from .urltree.servlets import UrlTreeRenderer, UrlTreeEsSearchServlet
from .wsp.adminwsp import AdminWsp
from .wsp.adminpack import AdminPack
from .wsp.export import Export
from .wsp.importSvc import Import
from .wsp.gen import WspGen
from .wsp.history import History
from .wsp.itemdyngen import ItemDynGen
from .wsp.search import Search
from .wsp.wspmetaeditor import WspMetaEditor
from .wsp.wspsrc import WspSrc


class JPortletOpt(TypedDict):
    strongbox: Optional[bool]
    remoteUsersMgrPortlet: Optional[str]


class JChainOpt(JPortletOpt):
    adminOdb: Optional[bool]
    history: Optional[bool]
    backupInPlace: Optional[bool]


class JSearchOpt(TypedDict):
    index: str


class JDepotOpt(JPortletOpt):
    adminOdb: Optional[bool]
    adminPack: Optional[bool]
    assets: Optional[bool]
    search: Optional[JSearchOpt]
    backup: Optional[bool]
    backupInPlace: Optional[bool]


class JDistribOpt(JPortletOpt):
    store: Optional[bool]
    backupInPlace: Optional[bool]
    projectsOnRes: Optional[bool]


class EPortletName(StrEnum):
    chain = "chain;1",
    depot = "depot;1",
    distrib = "distrib;1",
    saas = "saas;1"


class JPortletConf(TypedDict):
    portlet: EPortletName
    url: str
    opt: Optional[dict[str, Any]]
    execframe: Optional[str]


class JSaasPortalsAccess(TypedDict):
    """ configuration de l'accès aux portals constitués des instances du saas """
    vars: dict[str, str]
    portlets: dict[str, JPortletConf]


class JSaasOpt(JPortletOpt):
    adminPack: Optional[bool]
    assets: Optional[bool]
    clusterMgr: Optional[bool]
    dptResInstMgr: Optional[bool]
    backupInPlace: Optional[bool]
    portalsAccess: Optional[JSaasPortalsAccess]


class Portlet:
    def __init__(self, url: str, session: requests.Session, default_exec_frame_code: str, opt: JPortletOpt):
        self._url: str = url  # Url d'accès au portlet
        self._s: requests.Session = session  # Session d'interraction avec le portlet
        self._execFrame: str = default_exec_frame_code  # execFrame par défaut
        self._remoteAuthPortlet: Optional[str] = None  # code d'un autre portlet qui porte l'auth

        # Svc toujours présents
        self.adminServer: AdminServer = AdminServer(self._url, self._execFrame, "adminServer", self._s)
        self.adminUsers: AdminUser = AdminUser(self._url, self._execFrame, "adminUsers", self._s)
        self.executor: Executor = Executor(self._url, self._execFrame, "executor", self._s)
        self.ping: Ping = Ping(self._url, self._execFrame, "ping", self._s)
        self.universeActLog: ActlogJson = ActlogJson(self._url, self._execFrame, "universeActLog", self._s)

        # Svc optionnels
        self.strongbox: Optional[Strongbox] = None

        if "strongbox" in opt:
            self.strongbox = Strongbox(self._url, self._execFrame, "strongbox", self._s)

        if "remoteUsersMgrPortlet" in opt:
            self._remoteAuthPortlet = opt["remoteUsersMgrPortlet"]

    def __contains__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        else:
            return None

    def get_remote_auth_portlet(self) -> str:
        return self._remoteAuthPortlet


class Chain(Portlet):
    def __init__(self, url, session: requests.Session, opt: JChainOpt, exec_frame: str):
        super().__init__(url, session, exec_frame, opt)

        # Svc toujours présents
        self.adminWsp: AdminWsp = AdminWsp(self._url, self._execFrame, "adminWsp", self._s)
        self.adminPack: AdminPack = AdminPack(self._url, self._execFrame, "adminPack", self._s)
        self.itemDynGen: ItemDynGen = ItemDynGen(self._url, self._execFrame, "itemDynGen", self._s)
        self.export: Export = Export(self._url, self._execFrame, "export", self._s)
        self.importSvc: Import = Import(self._url, self._execFrame, "import", self._s)  # Suffix Svc car import est un mot réservé en Python
        self.maintenance: Maintenance = Maintenance(self._url, self._execFrame, "maintenance", self._s)
        self.search: Search = Search(self._url, self._execFrame, "search", self._s)
        self.wspGen: WspGen = WspGen(self._url, self._execFrame, "wspGen", self._s)
        self.wspMetaEditor: WspMetaEditor = WspMetaEditor(self._url, self._execFrame, "wspMetaEditor", self._s)
        self.wspSrc: WspSrc = WspSrc(self._url, self._execFrame, "wspSrc", self._s)

        # Svc optionnels
        self.adminOdb: Optional[AdminOdb] = None
        self.history: Optional[History] = None
        self.backupInPlace: Optional[BackupInPlace] = None

        if "adminOdb" in opt and opt["adminOdb"]:
            self.adminOdb = AdminOdb(self._url, self._execFrame, "adminOdb", self._s)

        if "history" in opt and opt["history"]:
            self.history = History(self._url, self._execFrame, "history", self._s)

        if "backupInPlace" in opt and opt["backupInPlace"]:
            self.backupInPlace = BackupInPlace(self._url, self._execFrame, "backupInPlace", self._s)


class Depot(Portlet):
    def __init__(self, url, session: requests.Session, opt: JDepotOpt, exec_frame: str):
        super().__init__(url, session, exec_frame, opt)

        # Svc toujours présents
        self.adminTree: UrlTreeRenderer = UrlTreeRenderer(self._url, "adminTree", self._s)
        self.cid: CidServer = CidServer(self._url, self._execFrame, "cid", self._s)
        self.maintenance: Maintenance = Maintenance(self._url, self._execFrame, "maintenance", self._s)
        self.store: StoreSquare = StoreSquare(self._url, self._execFrame, "store", self._s)
        self.tree: UrlTreeRenderer = UrlTreeRenderer(self._url, "tree", self._s)

        # Svc optionnels
        self.adminOdb: Optional[AdminOdb] = None
        self.adminPack: Optional[AdminPack] = None
        self.assetsCtrl: Optional[AssetsCtrl] = None
        self.backup: Optional[Backup] = None
        self.backupInPlace: Optional[BackupInPlace] = None
        self.search: Optional[UrlTreeEsSearchServlet] = None

        if "adminOdb" in opt and opt["adminOdb"]:
            self.adminOdb: AdminOdb = AdminOdb(self._url, self._execFrame, "adminOdb", self._s)

        if "adminPack" in opt and opt["adminPack"]:
            self.adminPack: AdminPack = AdminPack(self._url, self._execFrame, "adminPack", self._s)

        if "assets" in opt and opt["assets"]:
            self.assetsCtrl: AssetsCtrl = AssetsCtrl(self._url, self._execFrame, "assetsCtrl", self._s)

        if "backup" in opt and opt["backup"]:
            self.backup: Backup = Backup(self._url, self._execFrame, "backup", self._s)

        if "backupInPlace" in opt and opt["backupInPlace"]:
            self.backupInPlace: BackupInPlace = BackupInPlace(self._url, self._execFrame, "backupInPlace", self._s)

        if "search" in opt and opt["search"] is not None:
            self.search: UrlTreeEsSearchServlet = UrlTreeEsSearchServlet(self._url, "search", self._s, index=opt["search"]["indexes"][0])


class Saas(Portlet):
    def __init__(self, url, session: requests.Session, opt: JSaasOpt, exec_frame: str):
        super().__init__(url, session, exec_frame, opt)
        self._portalsAccess: Optional[JSaasPortalsAccess] = opt["portalsAccess"]

        # Svc toujours présents
        self.adminInst: AdminInst = AdminInst(self._url, self._execFrame, "adminInst", self._s)
        self.backupInstsInPlace: InstsBackupInPlace = InstsBackupInPlace(self._url, self._execFrame, "backupInstsInPlace", self._s)
        self.maintenance: Maintenance = Maintenance(self._url, self._execFrame, "maintenance", self._s)

        # Svc optionnels
        self.adminPack: Optional[AdminPack] = None
        self.assetsCtrl: Optional[AssetsCtrl] = None
        self.backupInPlace: Optional[BackupInPlace] = None
        self.instsClusterMgr: Optional[InstsClusterMgr] = None
        self.dptResInstMgr: Optional[DptResInstMgr] = None

        if "adminPack" in opt and opt["adminPack"]:
            self.adminPack: AdminPack = AdminPack(self._url, self._execFrame, "adminPack", self._s)

        if "assets" in opt and opt["assets"]:
            self.assetsCtrl: AssetsCtrl = AssetsCtrl(self._url, self._execFrame, "assetsCtrl", self._s)

        if "backupInPlace" in opt and opt["backupInPlace"]:
            self.backupInPlace: BackupInPlace = BackupInPlace(self._url, self._execFrame, "backupInPlace", self._s)

        if "clusterMgr" in opt and opt["clusterMgr"]:
            self.instsClusterMgr: InstsClusterMgr = InstsClusterMgr(self._url, self._execFrame, "instsClusterMgr", self._s)

        if "dptResInstMgr" in opt and opt["dptResInstMgr"]:
            self.dptResInstMgr: DptResInstMgr = DptResInstMgr(self._url, self._execFrame, "dptResInstMgr", self._s)

    def get_portal(self, user: str = None, pw=None, portal_vars: dict[str:Any] = None) -> Any:
        """
        :return: Un objet ScPortal. Il faudra caster le retour pour avoir l'autocomplétion.
        ex:
        portal:ScPortal = saas.get_portaJClusterInstInfol(user="admin", pw="admin", args={})
        """
        if self._portalsAccess is None:
            raise ValueError("portalsAccess conf is None. Unable to create a portal for saas instances")
        if portal_vars is None:
            portal_vars = {}
        variables = {**self._portalsAccess["vars"], **portal_vars}
        conf = Saas._format_prop(self._portalsAccess["portlets"], variables)

        from .portal import ScPortal
        portal = ScPortal(user=user, pw=pw)
        for code in conf:
            portlet: JPortletConf = conf[code]
            execframe = "script" if "execframe" not in portlet else portlet["execframe"]
            if portlet["portlet"] == EPortletName.chain.value:
                portal.add_chain_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
            elif portlet["portlet"] == EPortletName.depot.value:
                portal.add_depot_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
            elif portlet["portlet"] == EPortletName.distrib.value:
                portal.add_distrib_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
            elif portlet["portlet"] == EPortletName.saas.value:
                portal.add_saas_portlet(url=portlet["url"], code=code, opt=portlet["opt"], exec_frame=execframe)
            else:
                logging.error(f"unknown portlet {portlet}")
                sys.exit(1)

        return portal

    @staticmethod
    def _format_prop(prop: Any, variables: dict):
        if type(prop) is dict:
            formatted_props = {}
            for key in prop:
                formatted_props[key] = Saas._format_prop(prop[key], variables)
            return formatted_props
        elif type(prop) is list:
            formatted_props = []
            for val in prop:
                formatted_props.append(Saas._format_prop(val, variables))
            return formatted_props
        elif type(prop) is str:
            return prop.format(vars=variables)
        else:
            return prop


class Distrib(Portlet):
    def __init__(self, url, session: requests.Session, opt: JDistribOpt, exec_frame: str):
        super().__init__(url, session, exec_frame, opt)
        self._runExecFrame: str = "run"
        self._runSession: requests.Session = requests.Session()

        # Svc toujours présents
        self.distribEngine = DistribEngine(self._url, self._runExecFrame, "distribEngine", self._runSession)
        self.participant = Participant(self._url, self._runExecFrame, "participant", self._runSession)
        self.actor = Actor(self._url, self._runExecFrame, "actor", self._runSession)
        self.distribAdminUsers: AdminUser = AdminUser(self._url, self._execFrame, "distribAdminUsers", self._s)
        self.projectAdmin: ProjectAdmin = ProjectAdmin(self._url, self._execFrame, "projectAdmin", self._s)

        # Svc optionnels
        self.store: Optional[StoreSquare] = None
        self.backupInPlace: Optional[BackupInPlace] = None

        if "projectsOnRes" in opt and opt["projectsOnRes"]:
            self.projectsOnRes: ProjectsOnResMgr = ProjectsOnResMgr(self._url, self._execFrame, "projectsOnRes", self._s)

        if "store" in opt and opt["store"]:
            self.store: StoreSquare = StoreSquare(self._url, self._execFrame, "store", self._s)

        if "backupInPlace" in opt and opt["backupInPlace"]:
            self.backupInPlace: BackupInPlace = BackupInPlace(self._url, self._execFrame, "backupInPlace", self._s)
