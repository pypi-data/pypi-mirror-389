# Copyright 2025-present Erioon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Visit www.erioon.com/dev-docs for more information about the python SDK

import datetime
import msgpack
from io import BytesIO
from azure.storage.blob.aio import ContainerClient
import asyncio

async def _write_ops_async(db, collection, container_url, count, op_type):
    container_client = ContainerClient.from_container_url(container_url)
    ops_filename = f"{db}/{collection}/ops.msgpack"
    blob_client = container_client.get_blob_client(ops_filename)

    try:
        existing_data = msgpack.unpackb(await (await blob_client.download_blob()).readall(), raw=False)
    except Exception:
        existing_data = {}

    today = datetime.datetime.utcnow().date().isoformat()

    if today not in existing_data:
        existing_data[today] = {}
    if op_type not in existing_data[today]:
        existing_data[today][op_type] = 0

    existing_data[today][op_type] += count

    with BytesIO() as buf:
        buf.write(msgpack.packb(existing_data, use_bin_type=True))
        buf.seek(0)
        await blob_client.upload_blob(buf, overwrite=True)

    await container_client.close()
    return f"Cached {count} '{op_type}' operations for {today} in {db}/{collection}."


def cache_ops(db, collection, container_url, count, op_type):
    """
    Asynchronously cache and persist operation counts.

    Args:
        db (str): Database name.
        collection (str): Collection name.
        container_url (str): Azure Blob container URL.
        count (int): Number of operations to add.
        op_type (str): Operation type, e.g. "R", "W", "U", "D".
    """

    async def _background_task():
        try:
            await _write_ops_async(db, collection, container_url, count, op_type)
        except Exception as e:
            print(f"[cache_error] async error: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_background_task())
    except RuntimeError:
        asyncio.run(_background_task())
