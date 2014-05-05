/**
 * FreeRDP: A Remote Desktop Protocol Implementation
 * Graphics Pipeline Extension
 *
 * Copyright 2013 Marc-Andre Moreau <marcandre.moreau@gmail.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef FREERDP_CHANNEL_RDPGFX_H
#define FREERDP_CHANNEL_RDPGFX_H

#include <freerdp/api.h>
#include <freerdp/dvc.h>
#include <freerdp/types.h>

#define RDPGFX_DVC_CHANNEL_NAME	"Microsoft::Windows::RDS::Graphics"

/**
 * Common Data Types
 */

struct _RDPGFX_POINT16
{
	UINT16 x;
	UINT16 y;
};
typedef struct _RDPGFX_POINT16 RDPGFX_POINT16;

struct _RDPGFX_RECT16
{
	UINT16 left;
	UINT16 top;
	UINT16 right;
	UINT16 bottom;
};
typedef struct _RDPGFX_RECT16 RDPGFX_RECT16;

struct _RDPGFX_COLOR32
{
	BYTE B;
	BYTE G;
	BYTE R;
	BYTE XA;
};
typedef struct _RDPGFX_COLOR32 RDPGFX_COLOR32;

#define PIXEL_FORMAT_XRGB_8888		0x20
#define PIXEL_FORMAT_ARGB_8888		0x21

typedef BYTE RDPGFX_PIXELFORMAT;

#define RDPGFX_CMDID_WIRETOSURFACE_1		0x0001
#define RDPGFX_CMDID_WIRETOSURFACE_2		0x0002
#define RDPGFX_CMDID_DELETEENCODINGCONTEXT	0x0003
#define RDPGFX_CMDID_SOLIDFILL			0x0004
#define RDPGFX_CMDID_SURFACETOSURFACE		0x0005
#define RDPGFX_CMDID_SURFACETOCACHE		0x0006
#define RDPGFX_CMDID_CACHETOSURFACE		0x0007
#define RDPGFX_CMDID_EVICTCACHEENTRY		0x0008
#define RDPGFX_CMDID_CREATESURFACE		0x0009
#define RDPGFX_CMDID_DELETESURFACE		0x000A
#define RDPGFX_CMDID_STARTFRAME			0x000B
#define RDPGFX_CMDID_ENDFRAME			0x000C
#define RDPGFX_CMDID_FRAMEACKNOWLEDGE		0x000D
#define RDPGFX_CMDID_RESETGRAPHICS		0x000E
#define RDPGFX_CMDID_MAPSURFACETOOUTPUT		0x000F
#define RDPGFX_CMDID_CACHEIMPORTOFFER		0x0010
#define RDPGFX_CMDID_CACHEIMPORTREPLY		0x0011
#define RDPGFX_CMDID_CAPSADVERTISE		0x0012
#define RDPGFX_CMDID_CAPSCONFIRM		0x0013
#define RDPGFX_CMDID_MAPSURFACETOWINDOW		0x0015

struct _RDPGFX_HEADER
{
	UINT16 cmdId;
	UINT16 flags;
	UINT32 pduLength;
};
typedef struct _RDPGFX_HEADER RDPGFX_HEADER;

/**
 * Capability Sets
 */

#define RDPGFX_CAPVERSION_8			0x00080004
#define RDPGFX_CAPVERSION_81			0x00080105

struct _RDPGFX_CAPSET
{
	UINT32 version;
	UINT32 capsDataLength;
	/* capsData (variable) */
};
typedef struct _RDPGFX_CAPSET RDPGFX_CAPSET;

#define RDPGFX_CAPS_FLAG_THINCLIENT		0x00000001 /* 8.0+ */
#define RDPGFX_CAPS_FLAG_SMALL_CACHE		0x00000002 /* 8.0+ */
#define RDPGFX_CAPS_FLAG_H264ENABLED		0x00000010 /* 8.1+ */

struct _RDPGFX_CAPSET_VERSION8
{
	UINT32 version;
	UINT32 capsDataLength;
	UINT32 flags;
};
typedef struct _RDPGFX_CAPSET_VERSION8 RDPGFX_CAPSET_VERSION8;

struct _RDPGFX_CAPSET_VERSION81
{
	UINT32 version;
	UINT32 capsDataLength;
	UINT32 flags;
};
typedef struct _RDPGFX_CAPSET_VERSION81 RDPGFX_CAPSET_VERSION81;

/**
 * Graphics Messages
 */

#define RDPGFX_CODECID_UNCOMPRESSED		0x0000
#define RDPGFX_CODECID_CAVIDEO			0x0003
#define RDPGFX_CODECID_CLEARCODEC		0x0008
#define RDPGFX_CODECID_PLANAR			0x000A
#define RDPGFX_CODECID_H264			0x000B
#define RDPGFX_CODECID_ALPHA			0x000C

struct _RDPGFX_WIRE_TO_SURFACE_PDU_1
{
	UINT16 surfaceId;
	UINT16 codecId;
	RDPGFX_PIXELFORMAT pixelFormat;
	RDPGFX_RECT16 destRect;
	UINT32 bitmapDataLength;
	BYTE* bitmapData;
};
typedef struct _RDPGFX_WIRE_TO_SURFACE_PDU_1 RDPGFX_WIRE_TO_SURFACE_PDU_1;

#define RDPGFX_CODECID_CAPROGRESSIVE		0x0009
#define RDPGFX_CODECID_CAPROGRESSIVE_V2		0x000D

struct _RDPGFX_WIRE_TO_SURFACE_PDU_2
{
	UINT16 surfaceId;
	UINT16 codecId;
	UINT32 codecContextId;
	RDPGFX_PIXELFORMAT pixelFormat;
	UINT32 bitmapDataLength;
	BYTE* bitmapData;
};
typedef struct _RDPGFX_WIRE_TO_SURFACE_PDU_2 RDPGFX_WIRE_TO_SURFACE_PDU_2;

struct _RDPGFX_DELETE_ENCODING_CONTEXT_PDU
{
	UINT16 surfaceId;
	UINT32 codecContextId;
};
typedef struct _RDPGFX_DELETE_ENCODING_CONTEXT_PDU RDPGFX_DELETE_ENCODING_CONTEXT_PDU;

struct _RDPGFX_SOLIDFILL_PDU
{
	UINT16 surfaceId;
	RDPGFX_COLOR32 fillPixel;
	UINT16 fillRectCount;
	RDPGFX_RECT16* fillRects;
};
typedef struct _RDPGFX_SOLIDFILL_PDU RDPGFX_SOLIDFILL_PDU;

struct _RDPGFX_SURFACE_TO_SURFACE_PDU
{
	UINT16 surfaceIdSrc;
	UINT16 surfaceIdDest;
	RDPGFX_RECT16 rectSrc;
	UINT16 destPtsCount;
	RDPGFX_POINT16* destPts;
};
typedef struct _RDPGFX_SURFACE_TO_SURFACE_PDU RDPGFX_SURFACE_TO_SURFACE_PDU;

struct _RDPGFX_SURFACE_TO_CACHE_PDU
{
	UINT16 surfaceId;
	UINT64 cacheKey;
	UINT16 cacheSlot;
	RDPGFX_RECT16 rectSrc;
};
typedef struct _RDPGFX_SURFACE_TO_CACHE_PDU RDPGFX_SURFACE_TO_CACHE_PDU;

struct _RDPGFX_CACHE_TO_SURFACE_PDU
{
	UINT16 cacheSlot;
	UINT16 surfaceId;
	UINT16 destPtsCount;
	RDPGFX_POINT16* destPts;
};
typedef struct _RDPGFX_CACHE_TO_SURFACE_PDU RDPGFX_CACHE_TO_SURFACE_PDU;

struct _RDPGFX_EVICT_CACHE_ENTRY_PDU
{
	UINT16 cacheSlot;
};
typedef struct _RDPGFX_EVICT_CACHE_ENTRY_PDU RDPGFX_EVICT_CACHE_ENTRY_PDU;

struct _RDPGFX_CREATE_SURFACE_PDU
{
	UINT16 surfaceId;
	UINT16 width;
	UINT16 height;
	RDPGFX_PIXELFORMAT pixelFormat;
};
typedef struct _RDPGFX_CREATE_SURFACE_PDU RDPGFX_CREATE_SURFACE_PDU;

struct _RDPGFX_DELETE_SURFACE_PDU
{
	UINT16 surfaceId;
};
typedef struct _RDPGFX_DELETE_SURFACE_PDU RDPGFX_DELETE_SURFACE_PDU;

struct _RDPGFX_START_FRAME_PDU
{
	UINT32 timestamp;
	UINT32 frameId;
};
typedef struct _RDPGFX_START_FRAME_PDU RDPGFX_START_FRAME_PDU;

struct _RDPGFX_END_FRAME_PDU
{
	UINT32 frameId;
};
typedef struct _RDPGFX_END_FRAME_PDU RDPGFX_END_FRAME_PDU;

#define QUEUE_DEPTH_UNAVAILABLE			0x00000000
#define SUSPEND_FRAME_ACKNOWLEDGEMENT		0xFFFFFFFF

struct _RDPGFX_FRAME_ACKNOWLEDGE_PDU
{
	UINT32 queueDepth;
	UINT32 frameId;
	UINT32 totalFramesDecoded;
};
typedef struct _RDPGFX_FRAME_ACKNOWLEDGE_PDU RDPGFX_FRAME_ACKNOWLEDGE_PDU;

struct _RDPGFX_RESET_GRAPHICS_PDU
{
	UINT32 width;
	UINT32 height;
	UINT32 monitorCount;
	/* monitorDefArray */
	/* pad */
};
typedef struct _RDPGFX_RESET_GRAPHICS_PDU RDPGFX_RESET_GRAPHICS_PDU;

struct _RDPGFX_MAP_SURFACE_TO_OUTPUT_PDU
{
	UINT16 surfaceId;
	UINT16 reserved;
	UINT32 outputOriginX;
	UINT32 outputOriginY;
};
typedef struct _RDPGFX_MAP_SURFACE_TO_OUTPUT_PDU RDPGFX_MAP_SURFACE_TO_OUTPUT_PDU;

struct _RDPGFX_CACHE_ENTRY_METADATA
{
	UINT64 cacheKey;
	UINT32 bitmapLength;
};
typedef struct _RDPGFX_CACHE_ENTRY_METADATA RDPGFX_CACHE_ENTRY_METADATA;

struct _RDPGFX_CACHE_IMPORT_OFFER_PDU
{
	UINT16 cacheEntriesCount;
	RDPGFX_CACHE_ENTRY_METADATA* cacheEntries;
};
typedef struct _RDPGFX_CACHE_IMPORT_OFFER_PDU RDPGFX_CACHE_IMPORT_OFFER_PDU;

struct _RDPGFX_CACHE_IMPORT_REPLY_PDU
{
	UINT16 importedEntriesCount;
	UINT16* cacheSlots;
};
typedef struct _RDPGFX_CACHE_IMPORT_REPLY_PDU RDPGFX_CACHE_IMPORT_REPLY_PDU;

struct _RDPGFX_CAPS_ADVERTISE_PDU
{
	UINT16 capsSetCount;
	/* capsSets */
};
typedef struct _RDPGFX_CAPS_ADVERTISE_PDU RDPGFX_CAPS_ADVERTISE_PDU;

struct _RDPGFX_CAPS_CONFIRM_PDU
{
	RDPGFX_CAPSET* capSet;
	/* capSet */
};
typedef struct _RDPGFX_CAPS_CONFIRM_PDU RDPGFX_CAPS_CONFIRM_PDU;

struct _RDPGFX_MAP_SURFACE_TO_WINDOW_PDU
{
	UINT16 surfaceId;
	UINT64 windowId;
	UINT32 mappedWidth;
	UINT32 mappedHeight;
};
typedef struct _RDPGFX_MAP_SURFACE_TO_WINDOW_PDU RDPGFX_MAP_SURFACE_TO_WINDOW_PDU;

#endif /* FREERDP_CHANNEL_RDPGFX_H */

