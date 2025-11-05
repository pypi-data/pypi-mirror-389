from ctypes import byref as _byref, cast as _cast, memset as _memset, c_uint as _c_uint, py_object as _py_object
from ctypes import sizeof as _sizeof, POINTER as _POINTER, c_ubyte as _c_ubyte, c_float as _c_float, c_bool as _c_bool
from ctypes import c_void_p as _c_void_p, WINFUNCTYPE as _WINFUNCTYPE, pointer as _pointer
from enum import Enum as _Enum

from .mvs_native import MV_CC_DEVICE_INFO_LIST as _MV_CC_DEVICE_INFO_LIST
from .mvs_native import MV_CC_DEVICE_INFO as _MV_CC_DEVICE_INFO
from .mvs_native import MV_FRAME_OUT_INFO_EX as _MV_FRAME_OUT_INFO_EX, MV_FRAME_OUT as _MV_FRAME_OUT
from .mvs_native import MV_GIGE_DEVICE as _MV_GIGE_DEVICE, MV_USB_DEVICE as _MV_USB_DEVICE
from .mvs_native import MvCamera as _MvCamera, MVCC_INTVALUE as _MVCC_INTVALUE
from .mvs_native import MV_ACCESS_Exclusive as _MV_ACCESS_Exclusive
from .mvs_native import MV_TRIGGER_MODE_OFF as _MV_TRIGGER_MODE_OFF
from .mvs_native import PixelType_header as _PixelTypeHeader
import numpy as _np
from typing import Any as _Any, Callable as _Callable, Optional as _Optional, Union as _Union


class Transform(_Enum):
	NONE = 0
	FLIP_HORIZONTAL = 1
	FLIP_VERTICAL = 2
	ROTATE_90_CLOCKWISE = 3
	ROTATE_90_COUNTERCLOCKWISE = 4
	ROTATE_180 = 5
	FLIP_BOTH = 5  # FLIP_BOTH DOES equal to ROTATE_180
	TRANSPOSE = 6
	FLIP_BOTH_AND_TRANSPOSE = 7


def _is_mono(pixel_type) -> bool:
	return pixel_type in (
		_PixelTypeHeader.PixelType_Gvsp_Mono8,
		_PixelTypeHeader.PixelType_Gvsp_Mono10,
		_PixelTypeHeader.PixelType_Gvsp_Mono10_Packed,
		_PixelTypeHeader.PixelType_Gvsp_Mono12,
		_PixelTypeHeader.PixelType_Gvsp_Mono12_Packed,
		_PixelTypeHeader.PixelType_Gvsp_Mono14,
		_PixelTypeHeader.PixelType_Gvsp_Mono16
	)


class MVSException(Exception):
	pass


class MVSInterface(_Enum):
	GIGE = _MV_GIGE_DEVICE
	USB = _MV_USB_DEVICE


_PStructFrameOut = _POINTER(_MV_FRAME_OUT)
FrameOutCallBack = _WINFUNCTYPE(None, _PStructFrameOut, _c_void_p, _c_bool)
def _image_ready_callback_2(p_frame_out: _PStructFrameOut, p_user_data: _c_void_p, auto_free: _c_bool):
	frame_out: _MV_FRAME_OUT = p_frame_out.contents
	frame_info: _MV_FRAME_OUT_INFO_EX = frame_out.stFrameInfo
	channel = 1 if _is_mono(frame_info.enPixelType) else 3
	width, height = frame_info.nWidth, frame_info.nHeight
	count = width * height * channel
	ArrayType = _c_ubyte * count
	p_frame_buffer: _POINTER(_c_ubyte) = frame_out.pBufAddr
	buffer = _cast(p_frame_buffer, _POINTER(ArrayType)).contents
	image = _np.frombuffer(buffer, _np.ubyte).reshape((height, width, channel))
	p_camera: _py_object = _cast(p_user_data, _POINTER(_py_object)).contents
	camera: Camera = p_camera.value
	camera.event_callback(image, frame_info)
	if not auto_free:
		camera.native_handle.MV_CC_FreeImageBuffer(p_frame_out)
_FRAME_OUT_CALL_BACK_FUN = FrameOutCallBack(_image_ready_callback_2)

_ExceptionCallBack = _WINFUNCTYPE(None, _c_uint, _c_void_p)
def _exception_callback(message_type, p_user_data):
	p_camera: _py_object = _cast(p_user_data, _POINTER(_py_object)).contents
	camera: Camera = p_camera.value
	camera.event_callback(message_type, None)
_EXCEPTION_CALL_BACK_FUN = _ExceptionCallBack(_exception_callback)


class Camera:
	def __init__(
			self, camera_info: 'CameraInfo',
			transform: Transform = Transform.NONE
	):
		native_handle = camera_info.native_handle
		camera = _MvCamera()
		ret = camera.MV_CC_CreateHandle(native_handle)
		if ret != 0:
			raise MVSException(f'Create camera from camera info failed. ret[0x{ret:0x}].')
		ret = camera.MV_CC_OpenDevice(_MV_ACCESS_Exclusive, 0)
		if ret != 0:
			camera.MV_CC_DestroyHandle()
			raise MVSException(f'Open camera failed. ret[0x{ret:0x}].')

		self.__camera = camera
		self.__camera_info = camera_info
		self.__frame_buffer = None
		self.__transform = transform
		self.__transpose_needed = transform in [
			Transform.ROTATE_90_CLOCKWISE, Transform.ROTATE_90_COUNTERCLOCKWISE,
			Transform.TRANSPOSE, Transform.FLIP_BOTH_AND_TRANSPOSE
		]

		self.__event_callback = None
		self.__event_callback_user_data = None

		try:
			payload = self.__initialize_camera(camera_info)
			self.__frame_buffer = (_c_ubyte * payload)()
		except Exception as _e:
			self.close()
			raise

		self.__frame_info = _MV_FRAME_OUT_INFO_EX()
		_memset(_byref(self.__frame_info), 0, _sizeof(self.__frame_info))
		self.__timeout = 1.0

	@property
	def native_handle(self):
		return self.__camera

	def event_callback(self, image: _Optional[_Union[_np.ndarray, int]], frame_info: _Any):
		if isinstance(image, _np.ndarray):
			if self.__transpose_needed:
				image = image.transpose((1, 0, 2))
		self.__event_callback(image, frame_info, self.__event_callback_user_data)

	@property
	def transform(self):
		return self.__transform

	@property
	def timeout(self):
		return self.__timeout

	@timeout.setter
	def timeout(self, value: float):
		self.__timeout = value

	def __set_reverse_x(self, value: bool):
		ret = self.__camera.MV_CC_SetBoolValue('ReverseX', value)
		if ret != 0:
			raise MVSException(f'Camera failed: could not set attribute "ReverseX" to {value}. ret[0x{ret:0x}]')

	def __set_reverse_y(self, value: bool):
		ret = self.__camera.MV_CC_SetBoolValue('ReverseY', value)
		if ret != 0:
			raise MVSException(f'Camera failed: could not set attribute "ReverseY" to {value}. ret[0x{ret:0x}]')

	def __do_start_grabbing(self):
		ret = self.__camera.MV_CC_StartGrabbing()
		if ret != 0:
			raise MVSException(f'Initialize camera failed: could not start grabbing. ret[0x{ret:0x}]')

	def stop_grabbing(self, raise_if_fail: bool = False):
		ret = self.__camera.MV_CC_StopGrabbing()
		if ret != 0 and raise_if_fail:
			raise MVSException(f'Camera failed: could not stop grabbing. ret[0x{ret:0x}]')

	def start_grabbing(
			self,
			event_callback: _Optional[_Callable[[_Any, _Any, _Any], None]] = None,
			event_callback_data: _Any = None
	):
		self.__event_callback = event_callback
		self.__event_callback_user_data = event_callback_data

		if event_callback is not None:
			user_data = _py_object(self)
			p_user_data = _cast(_pointer(user_data), _c_void_p)
			self.__camera.MV_CC_RegisterImageCallBackEx2(_FRAME_OUT_CALL_BACK_FUN, p_user_data, True)
			self.__camera.MV_CC_RegisterExceptionCallBack(_EXCEPTION_CALL_BACK_FUN, p_user_data)
		else:
			self.__camera.MV_CC_RegisterImageCallBackEx2(None, None, True)
			self.__camera.MV_CC_RegisterExceptionCallBack(None, None)

		self.__do_start_grabbing()

	def __initialize_camera(self, camera_info: 'CameraInfo'):
		self.__camera.MV_CC_SetEnumValue('TriggerMode', _MV_TRIGGER_MODE_OFF)

		if camera_info.interface == MVSInterface.GIGE:
			package_size = self.__camera.MV_CC_GetOptimalPacketSize()
			if int(package_size) > 0:
				self.__camera.MV_CC_SetIntValue('GevSCPSPacketSize', package_size)

		para = _MVCC_INTVALUE()
		_memset(_byref(para), 0, _sizeof(_MVCC_INTVALUE))
		ret = self.__camera.MV_CC_GetIntValue('PayloadSize', para)
		if ret != 0:
			raise MVSException(f'Initialize camera failed: could not get PayloadSize. ret[0x{ret:0x}]')

		if self.transform in [
			Transform.FLIP_BOTH,
			Transform.FLIP_HORIZONTAL,
			Transform.FLIP_BOTH_AND_TRANSPOSE,
			Transform.ROTATE_90_COUNTERCLOCKWISE
		]:
			self.__set_reverse_x(True)

		if self.transform in [
			Transform.FLIP_BOTH,
			Transform.FLIP_VERTICAL,
			Transform.FLIP_BOTH_AND_TRANSPOSE,
			Transform.ROTATE_90_CLOCKWISE
		]:
			self.__set_reverse_y(True)

		if self.transform in [
			Transform.NONE, Transform.TRANSPOSE
		]:
			self.__set_reverse_x(False)
			self.__set_reverse_y(False)

		return para.nCurValue

	@property
	def camera_info(self):
		return self.__camera_info

	@property
	def exposure_time(self) -> float:
		value = _c_float()
		ret = self.__camera.MV_CC_GetFloatValue('ExposureTime', value)
		if ret != 0:
			raise MVSException(f'Get camera exposure time failed. ret[0x{ret}]')
		return value.value

	@exposure_time.setter
	def exposure_time(self, value: float):
		ret = self.__camera.MV_CC_SetFloatValue('ExposureTime', value)
		if ret != 0:
			raise MVSException(f'Set camera exposure time failed. Target value: {value}. ret[0x{ret}]')

	@property
	def gain(self) -> float:
		value = _c_float()
		ret = self.__camera.MV_CC_GetFloatValue('Gain', value)
		if ret != 0:
			raise MVSException(f'Get camera gain failed. ret[0x{ret}]')
		return value.value

	@gain.setter
	def gain(self, value: float):
		ret = self.__camera.MV_CC_SetFloatValue('Gain', value)
		if ret != 0:
			raise MVSException(f'Set camera gain failed. Target value: {value}. ret[0x{ret}]')

	def snap(self):
		assert self.__event_callback is None, 'ImageReadyCallback is set. Snapping is forbidden.'

		ms = int(self.timeout * 1000)
		buffer = self.__frame_buffer
		ret = self.__camera.MV_CC_GetOneFrameTimeout(
			_byref(buffer), _sizeof(buffer), self.__frame_info, nMsec=ms
		)
		if ret != 0:
			raise MVSException(f'Grab frame failed. ret[0x{ret}]. Camera: [{self.camera_info.serial_number}]')

		width = self.__frame_info.nWidth
		height = self.__frame_info.nHeight
		channel = 1 if _is_mono(self.__frame_info.enPixelType) else 3

		image = _np.frombuffer(buffer, dtype=_np.ubyte)
		image = image.reshape(height, width, channel)

		if self.__transpose_needed:
			image = image.transpose((1, 0, 2))

		return image

	def close(self):
		if self.__camera is not None:
			self.__camera.MV_CC_StopGrabbing()
			self.__camera.MV_CC_CloseDevice()
			self.__camera.MV_CC_DestroyHandle()
			self.__camera = None

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()


class CameraInfo:
	InfoAttrNameMap = {
		_MV_GIGE_DEVICE: 'stGigEInfo',
		_MV_USB_DEVICE: 'stUsb3VInfo'
	}

	def __init__(self, dev_list: _MV_CC_DEVICE_INFO_LIST, index: int):
		self.__dev_list = dev_list
		self.__index = index

	@property
	def native_handle(self) -> _MV_CC_DEVICE_INFO:
		info = _cast(self.__dev_list.pDeviceInfo[self.__index], _POINTER(_MV_CC_DEVICE_INFO)).contents
		return info

	@property
	def interface(self) -> MVSInterface:
		return MVSInterface(self.native_handle.nTLayerType)

	@property
	def serial_number(self) -> str:
		info = getattr(self.native_handle.SpecialInfo, CameraInfo.InfoAttrNameMap[self.native_handle.nTLayerType])
		sn = bytes(info.chSerialNumber).strip(b'\x00')
		return sn.decode(encoding='latin')

	@property
	def model(self) -> str:
		info = getattr(self.native_handle.SpecialInfo, CameraInfo.InfoAttrNameMap[self.native_handle.nTLayerType])
		sn = bytes(info.chModelName).strip(b'\x00')
		return sn.decode(encoding='latin')

	@property
	def ipv4(self) -> str:
		if self.interface != MVSInterface.GIGE:
			return ''
		else:
			ip = self.native_handle.SpecialInfo.stGigEInfo.nCurrentIp
			return f'{(ip & 0xff000000) >> 24}.{(ip & 0xff0000) >> 16}.{(ip & 0xff00) >> 8}.{ip & 0xff}'

	def open_camera(self):
		return Camera(self)

	def __str__(self):
		return f'MVS Camera\nS/N: {self.serial_number}\nModel: {self.model}\nI/F: {self.interface}\nIPv4: {self.ipv4}'


class CameraIterator:
	def __init__(self, enumerator: 'CameraEnumerator', info_name: str = ''):
		self.__enumerator = enumerator
		self.__index = 0
		self.__info_name = info_name

	def __iter__(self):
		return self

	def __next__(self):
		if self.__index < self.__enumerator.count:
			item = self.__enumerator[self.__index]
			self.__index += 1
			if self.__info_name and hasattr(item, self.__info_name):
				return getattr(item, self.__info_name)
			return item
		raise StopIteration


class CameraEnumerator:
	def __init__(self):
		dev_list = _MV_CC_DEVICE_INFO_LIST()
		ret = _MvCamera.MV_CC_EnumDevices(_MV_GIGE_DEVICE | _MV_USB_DEVICE, dev_list)
		if ret != 0:
			raise MVSException(f'Enum devices fail. ret[0x{ret:0x}]')

		self.__dev_list = dev_list

	@property
	def count(self) -> int:
		"""
		找到的所有相机的数量
		"""
		return self.__dev_list.nDeviceNum

	def __getitem__(self, item):
		if item < 0 or item >= self.count:
			raise MVSException(f'Index out of range: {item}')

		return CameraInfo(self.__dev_list, item)

	def serial_numbers(self):
		"""
		返回一个迭代器，可迭代找到的所有相机的序列号。注意：根据实际运行结果，可能会有重复的条目。
		"""
		return CameraIterator(self, 'serial_number')

	def items(self):
		"""
		返回一个迭代器，可迭代找到的所有相机信息。注意：根据实际运行结果，可能会有重复的条目。
		"""
		return CameraIterator(self)

	def open_first_camera(self):
		"""
		打开第一个找到的相机，如果有的话，否则，抛出一个 ValueError
		"""
		if self.count > 0:
			return self[0].open_camera()
		raise ValueError('No camera found.')

	def get_camera_info_by_serial_number(self, serial_number: str):
		"""
		根据序列号找到对应相机的 CameraInfo 对象。如果相机不存在，抛出一个 ValueError
		"""
		for i in range(self.count):
			info = self[i]
			if info.serial_number == serial_number:
				return info
		raise MVSException(f'Camera with serial number [{serial_number}] not found.')

	def open_camera_by_serial_number(self, serial_number: str):
		"""
		打开指定序列号的那个相机，如果存在的话，否则，抛出一个 ValueError
		"""
		return self.get_camera_info_by_serial_number(serial_number).open_camera()


class MVSCamera:
	def __init__(self, identify: _Union[str, CameraInfo], transform: Transform = Transform.NONE, name: str = ''):
		if isinstance(identify, str):
			info = CameraEnumerator().get_camera_info_by_serial_number(identify)
		elif isinstance(identify, CameraInfo):
			info = identify
		else:
			raise MVSException('Invalid MVS Camera Identity.')

		self.__camera: _Optional[Camera] = None
		self.__name = name
		self.open(info, transform)

	@property
	def name(self):
		return self.__name

	@name.setter
	def name(self, value: str):
		self.__name = value

	@property
	def info(self) -> CameraInfo:
		return self.__camera.camera_info

	@property
	def timeout(self):
		return self.__camera.timeout

	@timeout.setter
	def timeout(self, value: float):
		self.__camera.timeout = value

	@property
	def transform(self):
		return self.__camera.transform

	@transform.setter
	def transform(self, value: Transform):
		self.__camera.transform = value

	@property
	def serial_number(self) -> str:
		return self.info.serial_number

	@property
	def ipv4(self) -> str:
		return self.info.ipv4

	@property
	def exposure_time(self) -> float:
		if self.closed:
			raise MVSException('Camera is closed')
		return self.__camera.exposure_time

	@exposure_time.setter
	def exposure_time(self, value: float):
		if self.closed:
			raise MVSException('Camera is closed')
		self.__camera.exposure_time = value

	@property
	def gain(self) -> float:
		if self.closed:
			raise MVSException('Camera is closed')
		return self.__camera.gain

	@gain.setter
	def gain(self, value: float):
		if self.closed:
			raise MVSException('Camera is closed')
		self.__camera.gain = value

	@property
	def closed(self) -> bool:
		return self.__camera is None

	def close(self):
		if self.__camera is not None:
			self.__camera.close()
			self.__camera = None

	def open(self, info: CameraInfo, transform: Transform):
		if not self.closed:
			raise MVSException('Camera is already opened.')
		self.__camera = Camera(info, transform)

	def start_grabbing(
			self,
			event_callback: _Optional[_Callable[[_Any, _Any, _Any], None]] = None,
			event_callback_user_data: _Any = None
	):
		self.__camera.start_grabbing(event_callback, event_callback_user_data)

	def stop_grabbing(self, raise_if_fail = False):
		self.__camera.stop_grabbing(raise_if_fail)

	def snap(self):
		if self.closed:
			raise MVSException('Camera is closed')
		return self.__camera.snap()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()
