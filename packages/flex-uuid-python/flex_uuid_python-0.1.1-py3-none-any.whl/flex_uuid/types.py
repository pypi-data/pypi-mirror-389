import uuid
from typing import Union, Optional

class UUIDStorage:
	"""
	Description:
	- Accepts str, bytes (including bytearray), or uuid.UUID as input
	- Internally always stored as 16-byte bytes
	- Can return as uuid.UUID, str, or bytes
	"""
	def __init__(
		self,
		value: Union[str, bytes, bytearray, uuid.UUID],
		store_as_bytes: bool = True
	):
		if value is None:
			raise ValueError("value must not be None")
		
		if isinstance(value, (bytes, bytearray)):
			b = bytes(value)
			if len(b) != 16:
				raise ValueError("bytes value must be exactly 16 bytes for UUIDStorage")
			self._bytes = b
			self._uuid = uuid.UUID(bytes=b)
		elif isinstance(value, uuid.UUID):
			self._uuid = value
			self._bytes = value.bytes
		elif isinstance(value, str):
			v = value.strip()
			try:
				# Allow 32-hex (without hyphens)
				if len(v) == 32:
					u = uuid.UUID(hex=v)
				else:
					u = uuid.UUID(v)
			except Exception as exc:
				raise ValueError(f"Invalid UUID string: {value}") from exc
			self._uuid = u
			self._bytes = u.bytes
		else:
			raise TypeError(f"Unsupported type for UUIDStorage: {type(value)}")
		
		self._store_as_bytes = store_as_bytes

	@property
	def bytes(self) -> bytes:
		return self._bytes

	@property
	def uuid(self) -> uuid.UUID:
		return self._uuid

	def to_str(self) -> str:
		return str(self._uuid)

	def get_storage_value(self) -> Union[bytes, str]:
		if self._store_as_bytes:
			return self._bytes
		else:
			return self.to_str()

	def __str__(self) -> str:
		return self.to_str()

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}(bytes={self._bytes!r}, store_as_bytes={self._store_as_bytes})"


