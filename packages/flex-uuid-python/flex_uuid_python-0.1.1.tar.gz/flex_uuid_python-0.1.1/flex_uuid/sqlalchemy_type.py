import uuid
from typing import Union, Optional
from sqlalchemy.types import TypeDecorator, BINARY
from sqlalchemy.dialects.mysql import BINARY as MYSQL_BINARY
from sqlalchemy.dialects.postgresql import BYTEA as PG_BYTEA
from .types import UUIDStorage

class UUIDFlexType(TypeDecorator):
	"""
	SQLAlchemy custom column type:
	- Accepts str / bytes / uuid.UUID as Python-side input
	- Internal storage: bytes(16) or string, controlled by options
	- DB column type uses BINARY(16), BYTEA, etc., depending on dialect
	"""
	# Default impl: common 16-byte binary
	impl = BINARY(16)
	cache_ok = True

	def __init__(self, store_as_bytes: bool = True, return_uuid_object: bool = False, *args, **kwargs):
		"""
		:setting store_as_bytes: If True, store as bytes(16) in DB; if False, store as string
		:return_uuid_object: If True, return a uuid.UUID on read; if False, return a string
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
			# Use BINARY(16) by default
			return dialect.type_descriptor(BINARY(16))

	def process_bind_param(self, value: Optional[Union[str, bytes, bytearray, uuid.UUID]], dialect):
		if value is None:
			return None
		# Normalize via UUIDStorage
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
				# If stored internally as bytes, return string on read
				return storage.to_str()
			else:
				# If stored internally as string, return string as-is
				return storage.to_str()

	def copy(self, **kw):
		return UUIDFlexType(
			store_as_bytes=self.store_as_bytes,
			return_uuid_object=self.return_uuid_object,
			**kw
		)


