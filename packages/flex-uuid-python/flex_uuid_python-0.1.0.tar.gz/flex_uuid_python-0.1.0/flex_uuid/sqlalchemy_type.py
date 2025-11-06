import uuid
from typing import Union, Optional
from sqlalchemy.types import TypeDecorator, BINARY
from sqlalchemy.dialects.mysql import BINARY as MYSQL_BINARY
from sqlalchemy.dialects.postgresql import BYTEA as PG_BYTEA
from .types import UUIDStorage

class UUIDFlexType(TypeDecorator):
	"""
	SQLAlchemy 커스텀 컬럼 타입:
	- Python 측 입력으로 str / bytes / uuid.UUID 허용
	- 내부 저장: bytes(16) 혹은 문자열 형태, 옵션으로 제어 가능
	- DB 컬럼형은 dialect에 따라 적절히 BINARY(16), BYTEA 등 사용
	"""
	# 기본 impl은 가장 일반적인 바이너리 16바이트
	impl = BINARY(16)
	cache_ok = True

	def __init__(self, store_as_bytes: bool = True, return_uuid_object: bool = False, *args, **kwargs):
		"""
		:setting store_as_bytes: True이면 DB 저장 값을 bytes(16)로, False이면 문자열 형태 저장
		:return_uuid_object: True이면 조회 시 uuid.UUID 객체 반환, False이면 문자열 반환
		"""
		super().__init__(*args, **kwargs)
		self.store_as_bytes = store_as_bytes
		self.return_uuid_object = return_uuid_object

	def load_dialect_impl(self, dialect):
		name = dialect.name
		if name == "mysql":
			return dialect.type_descriptor(MYSQL_BINARY(16))
		elif name in ("postgresql", "postgres"):
			return dialect.type_descriptor(PG_BYTEA())
		else:
			# 기본적으로 BINARY(16) 사용
			return dialect.type_descriptor(BINARY(16))

	def process_bind_param(self, value: Optional[Union[str, bytes, bytearray, uuid.UUID]], dialect):
		if value is None:
			return None
		# UUIDStorage로 통일 처리
		storage = UUIDStorage(value, store_as_bytes=True)
		if self.store_as_bytes:
			return storage.bytes
		else:
			return storage.to_str()

	def process_result_value(self, value: Optional[Union[bytes, str]], dialect):
		if value is None:
			return None
		if isinstance(value, (bytes, bytearray)):
			storage = UUIDStorage(value, store_as_bytes=True)
		elif isinstance(value, str):
			storage = UUIDStorage(value, store_as_bytes=True)
		else:
			raise TypeError(f"Unexpected return type for UUIDFlexType: {type(value)}")

		if self.return_uuid_object:
			return storage.uuid
		else:
			if self.store_as_bytes:
				# 내부 저장가 bytes였으면 문자열 반환
				return storage.to_str()
			else:
				# 내부 저장가 문자열이면 문자열 그대로 반환
				return storage.to_str()

	def copy(self, **kw):
		return UUIDFlexType(
			store_as_bytes=self.store_as_bytes,
			return_uuid_object=self.return_uuid_object,
			**kw
		)


