from typing import TypedDict, Optional, List
from ..common.utils import StrEnum, serialize_cdm, json
from ..common.svc import Svc


class EUserType(StrEnum):
	user = "user"
	group = "group"


class EUserDisabledFilters(StrEnum):
	enabled = "enabled"
	enabledPermanent = "enabledPermanent"
	NotEnabledPermanent = "NotEnabledPermanent"
	enabledTemporary = "enabledTemporary"
	NotEnabledTemporary = "NotEnabledTemporary"
	disabled = "disabled"
	disabledPermanent = "disabledPermanent"
	NotDisabledPermanent = "NotDisabledPermanent"
	disabledTemporary = "disabledTemporary"
	NotDisabledTemporary = "NotDisabledTemporary"


class JUserRoles(TypedDict):
	grantedRoles: Optional[List[str]]
	refusedRoles: Optional[List[str]]
	inheritedRoles: Optional[List[str]]


class JUserBase(JUserRoles):
	account: Optional[str]
	userType: Optional[EUserType]
	nickNames: Optional[List[str]]
	lastName: Optional[str]
	firstName: Optional[str]
	groupName: Optional[str]
	email: Optional[str]
	categ: Optional[str]
	groups: Optional[List[str]]
	pwdEndDt: Optional[int]
	authMethod: Optional[str]
	disabledEndDt: Optional[int]
	isUnknown: Optional[bool]


class JUserUpdate(JUserBase):
	password: Optional[str]


class JUser(JUserBase):
	"""Props d'un user (accessibles en lecture)."""
	isAnonymous: Optional[bool]
	isSuperAdmin: Optional[bool]
	isDisabled: Optional[bool]
	isReadOnly: Optional[bool]
	isHidden: Optional[bool]
	flattenedGroups: Optional[List[str]]
	pwdDt: Optional[int]  # Date de dernière modif du password.


class JUsersSet(TypedDict):
	userList: Optional[List[JUser]]
	more: Optional[bool]


class JListUserParam(TypedDict):
	firstChars: Optional[str]
	filterType: Optional[EUserType]
	filterHidden: Optional[bool]
	filterGroupsMembers: Optional[list[str]]
	filterRoles: Optional[list[str]]
	filterDisabled: Optional[EUserDisabledFilters]
	maxResults: Optional[int]
	fieldMatchRegExp: Optional[str]
	fieldsContainsList: Optional[str]


# filterGroupsMembers?: string[], maxResults?: number, fieldMatchRegExp?: RegExp, fieldMatchList?: string, addFields?: ('flattenedGroups')[], removeFields?: string[], filterRoles?: string[], filterDisabled?: EUserDisabledFilters
class AdminUser(Svc):
	def list(self, options: Optional[JListUserParam] = None, add_fields: Optional[list[str]] = None, remove_fields: Optional[list[str]] = None) -> JUsersSet:
		fields = [] if add_fields is None else add_fields
		if remove_fields is not None:
			for field in remove_fields:
				fields.append(f"-{field}")
		qs = {"cdaction": "List", "fields": fields}
		if options is not None:
			qs["options"] = serialize_cdm(options)

		return json(self._s.get(self._url, params=qs))

	def display(self, account: str) -> Optional[JUser]:
		resp = json(self._s.get(self._url, params={"cdaction": "Display", "param": account}))
		return None if "user" not in resp else resp["user"]

	def create_user(self, account: str, props: JUserUpdate) -> JUser:
		return json(self._s.post(self._url, params={"cdaction": "CreateUser", "param":account}, data={"userProps": serialize_cdm(props)}, headers={"Sccsrf": "1"}))["user"]

	def create_group(self, account: str, props: JUserUpdate) -> JUser:
		return json(self._s.post(self._url, params={"cdaction": "CreateGroup", "param": account}, data={"userProps": serialize_cdm(props)}, headers={"Sccsrf": "1"}))["user"]

	def update_user(self, account: str, props: JUserUpdate) -> JUser:
		return json(self._s.post(self._url, params={"cdaction": "UpdateUser", "param": account}, data={"userProps": serialize_cdm(props)}, headers={"Sccsrf": "1"}))["user"]

	def update_group(self, account: str, props: JUserUpdate) -> JUser:
		return json(self._s.post(self._url, params={"cdaction": "UpdateGroup", "param": account}, data={"userProps": serialize_cdm(props)}, headers={"Sccsrf": "1"}))["user"]
