import uuid
from typing import Union, Optional

class UUIDStorage:
	"""
	클래스 설명:
	- 입력으로 str, bytes(bytearray 포함), uuid.UUID 객체 모두 허용
	- 내부 저장은 항상 bytes(16)로 유지
	- 반환 형태는 uuid.UUID 객체나 str 혹은 bytes 형태로 변환 가능
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
				# 32-hex (하이픈 없이) 허용
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


