import enum
import json
import math
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Union

import aiohttp
import dateutil.parser
import geopandas as gpd
import numpy as np
import pyproj
import rasterio as rio
import shapely.geometry
import snappy
import typer
from dateutil import parser
from rasterio.windows import from_bounds
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from ..exceptions import (
    CancelAllTasksError,
    CancelCollectionTasksError,
    CancelTaskError,
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    CreateCollectionError,
    DeleteCollectionError,
    DownloadFilesError,
    GetCollectionError,
    GetTaskError,
    InvalidCollectionTypeError,
    ListCollectionsError,
    ListTasksError,
    QuotaInsufficientError,
    TaskNotFoundError,
    UploadArtifactsError,
    UploadRequestsError,
)
from ..helper.decorators import require_api_key

class OutputTypes(enum.Enum):
    geotiff = 'geotiff'
    png = 'png'
    netcdf = 'netcdf'
    json = 'json'
    json_v2 = 'json_v2'
    csv = 'csv'

class Region(str, enum.Enum):
    aus = "aus"
    eu = "eu"
    us = "us"

regions = {
    Region.aus : {
        "name" : "australia-southeast1", 
        "url" : "https://terrakio-server-candidate-573248941006.australia-southeast1.run.app", 
        "bucket" : "terrakio-mass-requests"
    },
    
    Region.eu : {
        "name" : "europe-west4", 
        "url" : "https://terrakio-server-candidate-573248941006.europe-west4.run.app", 
        "bucket" : "terrakio-mass-requests-eu"
    },
    
    Region.us : {
        "name" : "us-central1", 
        "url" : "https://terrakio-server-candidate-573248941006.us-central1.run.app", 
        "bucket" : "terrakio-mass-requests-us"
    },

}

class Dataset_Dtype(enum.Enum):
    uint8 = 'uint8'
    float32 = 'float32'

class MassStats:
    def __init__(self, client):
        self._client = client
        self.console = Console()
        self.OutputTypes = OutputTypes
        self.Region = Region
        self.regions = regions
        self.Dataset_Dtype = Dataset_Dtype
    async def track_progress(self, task_id):
        task_info = await self.get_task(task_id=task_id)
        number_of_jobs = task_info["task"]["total"]
        start_time = parser.parse(task_info["task"]["createdAt"])
        
        self.console.print(f"[bold cyan]Tracking task: {task_id}[/bold cyan]")
        
        completed_jobs_info = []
        
        def get_job_description(job_info, include_status=False):
            if not job_info:
                return "No job info"
            
            service = job_info.get("service", "Unknown service")
            desc = service
            
            if include_status:
                status = job_info.get("status", "unknown")
                desc += f" - {status}"
            
            return desc
        
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        )
        
        with progress:
            last_completed_count = 0
            current_job_task = None
            current_job_description = None
            
            while len(completed_jobs_info) < number_of_jobs:
                task_info = await self.get_task(task_id=task_id)
                completed_number = task_info["task"]["completed"]
                current_job_info = task_info["currentJob"]
                
                if completed_number > last_completed_count:
                    if current_job_task is not None:
                        completed_description = current_job_description.replace(" - pending", "").replace(" - running", "").replace(" - waiting", "")
                        completed_description += " - completed"
                        
                        progress.update(
                            current_job_task,
                            description=f"[{last_completed_count + 1}/{number_of_jobs}] {completed_description}",
                            completed=100
                        )
                        completed_jobs_info.append({
                            "task": current_job_task,
                            "description": completed_description,
                            "job_number": last_completed_count + 1
                        })
                        current_job_task = None
                        current_job_description = None
                    
                    last_completed_count = completed_number
                
                if current_job_info:
                    status = current_job_info["status"]
                    current_job_description = get_job_description(current_job_info, include_status=True)
                    
                    total_value = current_job_info.get("total", 0)
                    completed_value = current_job_info.get("completed", 0)
                    
                    if total_value == -9999:
                        percent = 0
                    elif total_value > 0:
                        percent = int(completed_value / total_value * 100)
                    else:
                        percent = 0
                    
                    if current_job_task is None:
                        current_job_task = progress.add_task(
                            f"[{completed_number + 1}/{number_of_jobs}] {current_job_description}",
                            total=100,
                            start_time=start_time
                        )
                    else:
                        progress.update(
                            current_job_task,
                            description=f"[{completed_number + 1}/{number_of_jobs}] {current_job_description}",
                            completed=percent
                        )
                    
                    if status == "Error":
                        self.console.print("[bold red]Error![/bold red]")
                        raise typer.Exit(code=1)
                    if status == "Cancelled":
                        self.console.print("[bold orange]Cancelled![/bold orange]")
                        raise typer.Exit(code=1)
                    elif status == "Completed":
                        completed_description = current_job_description.replace(" - pending", "").replace(" - running", "").replace(" - waiting", "")
                        completed_description += " - completed"
                        progress.update(
                            current_job_task, 
                            description=f"[{completed_number + 1}/{number_of_jobs}] {completed_description}",
                            completed=100
                        )
                
                if completed_number == number_of_jobs and current_job_info is None:
                    if current_job_task is not None:
                        completed_description = current_job_description.replace(" - pending", "").replace(" - running", "").replace(" - waiting", "")
                        completed_description += " - completed"
                        progress.update(
                            current_job_task,
                            description=f"[{number_of_jobs}/{number_of_jobs}] {completed_description}",
                            completed=100
                        )
                        completed_jobs_info.append({
                            "task": current_job_task,
                            "description": completed_description,
                            "job_number": number_of_jobs
                        })
                    break
                
                time.sleep(10)
        
        self.console.print(f"[bold green]All {number_of_jobs} jobs finished![/bold green]")

    @require_api_key
    async def create_collection(
        self, 
        collection: str, 
        bucket: Optional[str] = None, 
        location: Optional[str] = None, 
        collection_type: str = "basic"
    ) -> Dict[str, Any]:
        """
        Create a collection for the current user.

        Args:
            collection: The name of the collection (required)
            bucket: The bucket to use (optional, admin only)
            location: The location to use (optional, admin only)
            collection_type: The type of collection to create (optional, defaults to "basic")
            
        Returns:
            API response as a dictionary containing the collection id
            
        Raises:
            CollectionAlreadyExistsError: If the collection already exists
            InvalidCollectionTypeError: If the collection type is invalid
            CreateCollectionError: If the API request fails due to unknown reasons
        """
        payload = {
            "collection_type": collection_type
        }
        
        if bucket is not None:
            payload["bucket"] = bucket
        
        if location is not None:
            payload["location"] = location
        
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}", json=payload)
        if status != 200:
            if status == 400 or status == 409:
                raise CollectionAlreadyExistsError(f"Collection {collection} already exists", status_code=status)
            if status == 422:
                raise InvalidCollectionTypeError(f"Invalid collection type: {collection_type}", status_code=status)
            raise CreateCollectionError(f"Create collection failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def get_collection(self, collection: str) -> Dict[str, Any]:
        """
        Get a collection by name.

        Args:
            collection: The name of the collection to retrieve(required)
            
        Returns:
            API response as a dictionary containing collection information
            
        Raises:
            CollectionNotFoundError: If the collection is not found
            GetCollectionError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("GET", f"collections/{collection}")

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetCollectionError(f"Get collection failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def list_collections(
        self,
        collection_type: Optional[str] = None,
        limit: Optional[int] = 10,
        page: Optional[int] = 0
    ) -> List[Dict[str, Any]]:
        """
        List collections for the current user.

        Args:
            collection_type: Filter by collection type (optional)
            limit: Number of collections to return (optional, defaults to 10)
            page: Page number (optional, defaults to 0)
            
        Returns:
            API response as a list of dictionaries containing collection information
            
        Raises:
            ListCollectionsError: If the API request fails due to unknown reasons
        """
        params = {}
        
        if collection_type is not None:
            params["collection_type"] = collection_type
        
        if limit is not None:
            params["limit"] = limit
            
        if page is not None:
            params["page"] = page
        
        response, status = await self._client._terrakio_request("GET", "collections", params=params)
        if status != 200:
            raise ListCollectionsError(f"List collections failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def delete_collection(
        self, 
        collection: str, 
        full: Optional[bool] = False, 
        outputs: Optional[list] = [], 
        data: Optional[bool] = False
    ) -> Dict[str, Any]:
        """
        Delete a collection by name.

        Args:
            collection: The name of the collection to delete (required)
            full: Delete the full collection (optional, defaults to False)
            outputs: Specific output folders to delete (optional, defaults to empty list)
            data: Whether to delete raw data (xdata folder) (optional, defaults to False)
            
        Returns:
            API response as a dictionary confirming deletion
            
        Raises:
            CollectionNotFoundError: If the collection is not found
            DeleteCollectionError: If the API request fails due to unknown reasons
        """
        params = {
            "full": str(full).lower(),
            "data": str(data).lower()
        }
        
        if outputs:
            params["outputs"] = outputs
        
        response, status = await self._client._terrakio_request("DELETE", f"collections/{collection}", params=params)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise DeleteCollectionError(f"Delete collection failed with status {status}", status_code=status)

        return response

    # below are functions related to tasks
    @require_api_key
    async def list_tasks(
        self,
        limit: Optional[int] = 10,
        page: Optional[int] = 0
    ) -> List[Dict[str, Any]]:
        """
        List tasks for the current user.

        Args:
            limit: Number of tasks to return (optional, defaults to 10)
            page: Page number (optional, defaults to 0)
        
        Returns:
            API response as a list of dictionaries containing task information
            
        Raises:
            ListTasksError: If the API request fails due to unknown reasons
        """
        params = {
            "limit": limit,
            "page": page
        }
        response, status = await self._client._terrakio_request("GET", "tasks", params=params)

        if status != 200:
            raise ListTasksError(f"List tasks failed with status {status}", status_code=status)

        return response
        
    @require_api_key
    async def get_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get task information by task ID.

        Args:
            task_id: ID of task to track
        
        Returns:
            API response as a dictionary containing task information

        Raises:
            TaskNotFoundError: If the task is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("GET", f"tasks/info/{task_id}")

        if status != 200:
            if status == 404:
                raise TaskNotFoundError(f"Task {task_id} not found", status_code=status)
            raise GetTaskError(f"Get task failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def cancel_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a task by task ID.

        Args:
            task_id: ID of task to cancel

        Returns:
            API response as a dictionary containing task information

        Raises:
            TaskNotFoundError: If the task is not found
            CancelTaskError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("POST", f"tasks/cancel/{task_id}")
        
        if status != 200:
            if status == 404:
                raise TaskNotFoundError(f"Task {task_id} not found", status_code=status)
            raise CancelTaskError(f"Cancel task failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def cancel_collection_tasks(
        self,
        collection: str
    ) -> Dict[str, Any]:
        """
        Cancel all tasks for a collection.

        Args:
            collection: Name of collection

        Returns:
            API response as a dictionary containing task information for the collection

        Raises:
            CollectionNotFoundError: If the collection is not found
            CancelCollectionTasksError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}/cancel")
        
        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise CancelCollectionTasksError(f"Cancel collection tasks failed with status {status}", status_code=status)
    
        return response

    @require_api_key
    async def cancel_all_tasks(
        self
    ) -> Dict[str, Any]:
        """
        Cancel all tasks for the current user.

        Returns:
            API response as a dictionary containing task information for all tasks

        Raises:
            CancelAllTasksError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("POST", "tasks/cancel")

        if status != 200:
            raise CancelAllTasksError(f"Cancel all tasks failed with status {status}", status_code=status)

        return response

    # below are functions related to the web ui and needs to be deleted in the future
    @require_api_key
    async def upload_artifacts(
        self,
        collection: str,
        file_type: str,
        compressed: Optional[bool] = True
    ) -> Dict[str, Any]:
        """
        Retrieve signed url to upload artifact file to a collection.

        Args:
            collection: Name of collection
            file_type: The extension of the file
            compressed: Whether to compress the file using gzip or not (defaults to True)
        
        Returns:
            API response as a dictionary containing the upload URL

        Raises:
            CollectionNotFoundError: If the collection is not found
            UploadArtifactsError: If the API request fails due to unknown reasons
        """
        params = {
            "file_type": file_type,
            "compressed": str(compressed).lower(),
        }

        response, status = await self._client._terrakio_request("GET", f"collections/{collection}/upload", params=params)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise UploadArtifactsError(f"Upload artifacts failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def zonal_stats(
        self,
        collection: str,
        id_property: str,
        column_name: str,
        expr: str,
        resolution: Optional[int] = 1,
        in_crs: Optional[str] = "epsg:4326",
        out_crs: Optional[str] = "epsg:4326"
    ) -> Dict[str, Any]:
        """
        Run zonal stats over uploaded geojson collection.

        Args:
            collection: Name of collection
            id_property: Property key in geojson to use as id
            column_name: Name of new column to add
            expr: Terrak.io expression to evaluate
            resolution: Resolution of request (optional, defaults to 1)
            in_crs: CRS of geojson (optional, defaults to "epsg:4326")
            out_crs: Desired output CRS (optional, defaults to "epsg:4326")

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        payload = {
            "id_property": id_property,
            "column_name": column_name,
            "expr": expr,
            "resolution": resolution,
            "in_crs": in_crs,
            "out_crs": out_crs
        }
        
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}/zonal_stats", json=payload)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Zonal stats failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def zonal_stats_transform(
        self,
        collection: str,
        consumer: str
    ) -> Dict[str, Any]:
        """
        Transform raw data in collection. Creates a new collection.

        Args:
            collection: Name of collection
            consumer: Post processing script (file path or script content)

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        if os.path.isfile(consumer):
            with open(consumer, 'r') as f:
                script_content = f.read()
        else:
            script_content = consumer

        files = {
            'consumer': ('script.py', script_content, 'text/plain')
        }
        
        response, status = await self._client._terrakio_request(
            "POST", 
            f"collections/{collection}/transform", 
            files=files
        )

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Transform failed with status {status}", status_code=status)
        
        return response

    async def _get_upload_url(
        self,
        collection: str
    ) -> Dict[str, Any]:
        """
        Retrieve signed url to upload requests for a collection.

        Args:
            collection: Name of collection
        
        Returns:
            API response as a dictionary containing the upload URL

        Raises:
            CollectionNotFoundError: If the collection is not found
            UploadRequestsError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("GET", f"collections/{collection}/upload/requests")

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise UploadRequestsError(f"Upload requests failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def _upload_file(self, file_path: str, url: str, use_gzip: bool = True):
        """
        Helper method to upload a JSON file to a signed URL.
        
        Args:
            file_path: Path to the JSON file
            url: Signed URL to upload to
            use_gzip: Whether to compress the file with gzip
        """
        try:
            with open(file_path, 'r') as file:
                json_data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        
        return await self._upload_json_data(json_data, url, use_gzip)

    @require_api_key
    async def _upload_json_data(self, json_data, url: str, use_gzip: bool = True):
        """
        Helper method to upload JSON data directly to a signed URL.
        
        Args:
            json_data: JSON data (dict or list) to upload
            url: Signed URL to upload to
            use_gzip: Whether to compress the data with gzip
        """
        if hasattr(json, 'dumps') and 'ignore_nan' in json.dumps.__code__.co_varnames:
            dumps_kwargs = {'ignore_nan': True}
        else:
            dumps_kwargs = {}
        
        if use_gzip:
            import gzip
            body = gzip.compress(json.dumps(json_data, **dumps_kwargs).encode('utf-8'))
            headers = {
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip'
            }
        else:
            body = json.dumps(json_data, **dumps_kwargs).encode('utf-8')
            headers = {
                'Content-Type': 'application/json'
            }
        
        response = await self._client._regular_request("PUT", url, data=body, headers=headers)
        return response



    @require_api_key
    async def generate_data(
        self,
        collection: str,
        file_path: str,
        output: str,
        skip_existing: Optional[bool] = True,
        force_loc: Optional[bool] = None,
        server: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate data for a collection.

        Args:
            collection: Name of collection
            file_path: Path to the file to upload
            output: Output type (str)
            force_loc: Write data directly to the cloud under this folder
            skip_existing: Skip existing data
            server: Server to use
        
        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        
        await self.get_collection(collection = collection)

        upload_urls = await self._get_upload_url(
            collection = collection
        )
        
        url = upload_urls['url']

        await self._upload_file(file_path, url)
        
        payload = {"output": output, "skip_existing": skip_existing}
        
        if force_loc is not None:
            payload["force_loc"] = force_loc
        if server is not None:
            payload["server"] = server
        
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}/generate_data", json=payload)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Generate data failed with status {status}", status_code=status)
        
        return response


    @require_api_key
    async def post_processing(
        self,
        collection: str,
        folder: str,
        consumer: str
    ) -> Dict[str, Any]:
        """
        Run post processing for a collection.

        Args:
            collection: Name of collection
            folder: Folder to store output
            consumer: Path to post processing script

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """

        await self.get_collection(collection = collection)

        with open(consumer, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('folder', folder)
            form.add_field(
                'consumer',
                f.read(),
                filename='consumer.py',
                content_type='text/x-python'
            )
        
        response, status = await self._client._terrakio_request(
            "POST",
            f"collections/{collection}/post_process",
            data=form
        )
        
        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Post processing failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def training_samples(
        self,
        collection: str,
        aoi: str,
        expression_x: str,
        filter_x: str = "skip",
        filter_x_rate: float = 1,
        expression_y: str = "skip",
        filter_y: str = "skip",
        filter_y_rate: float = 1,
        samples: int = 1000,
        tile_size: float = 256,
        crs: str = "epsg:3577",
        res: float = 10,
        res_y: float = None,
        skip_test: bool = False,
        start_year: int = None,
        end_year: int = None,
        server: str = None,
        extra_filters: list[str] = None,
        extra_filters_rate: list[float] = None,
        extra_filters_res: list[float] = None
    ) -> dict:
        """
        Generate an AI dataset using specified parameters.

        Args:
            collection: The collection name where we save the results
            aoi: Path to GeoJSON file containing area of interest
            expression_x: Expression for X data (features)
            filter_x: Filter expression for X data (default: "skip")
            filter_x_rate: Filter rate for X data (default: 1)
            expression_y: Expression for Y data (labels) (default: "skip")
            filter_y: Filter expression for Y data (default: "skip")
            filter_y_rate: Filter rate for Y data (default: 1)
            samples: Number of samples to generate (default: 1000)
            tile_size: Size of tiles in pixels (default: 256)
            crs: Coordinate reference system (default: "epsg:3577")
            res: Resolution for X data (default: 10)
            res_y: Resolution for Y data, defaults to res if None
            skip_test: Skip expression validation test (default: False)
            start_year: Start year for temporal filtering
            end_year: End year for temporal filtering
            server: Server to use for processing
            extra_filters: Additional filter expressions
            extra_filters_rate: Rates for additional filters
            extra_filters_res: Resolutions for additional filters

        Returns:
            Response containing task_id and collection name

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails
            TypeError: If extra filters have mismatched rate and resolution lists
        """
        expressions = [{"expr": expression_x, "res": res, "prefix": "x"}]
        
        res_y = res_y or res
        
        if expression_y != "skip":
            expressions.append({"expr": expression_y, "res": res_y, "prefix": "y"})
        
        filters = []
        if filter_x != "skip":
            filters.append({"expr": filter_x, "res": res, "rate": filter_x_rate})
        
        if filter_y != "skip":
            filters.append({"expr": filter_y, "res": res_y, "rate": filter_y_rate})
        
        if extra_filters:
            try:
                extra_filters_combined = zip(extra_filters, extra_filters_res, extra_filters_rate, strict=True)
            except TypeError:
                raise TypeError("Extra filters must have matching rate and resolution.")
            
            for expr, filter_res, rate in extra_filters_combined:
                filters.append({"expr": expr, "res": filter_res, "rate": rate})
        
        if start_year is not None:
            for expr_dict in expressions:
                expr_dict["expr"] = expr_dict["expr"].replace("{year}", str(start_year))
            
            for filter_dict in filters:
                filter_dict["expr"] = filter_dict["expr"].replace("{year}", str(start_year))
        
        if not skip_test:
            for expr_dict in expressions:
                test_request = self._client.model._generate_test_request(expr_dict["expr"], crs, -1)
                await self._client._terrakio_request("POST", "geoquery", json=test_request)
            
            for filter_dict in filters:
                test_request = self._client.model._generate_test_request(filter_dict["expr"], crs, -1)
                await self._client._terrakio_request("POST", "geoquery", json=test_request)
        
        with open(aoi, 'r') as f:
            aoi_data = json.load(f)

        await self.get_collection(
            collection = collection,
        )

        payload = {
            "expressions": expressions,
            "filters": filters,
            "aoi": aoi_data,
            "samples": samples,
            "crs": crs,
            "tile_size": tile_size,
            "res": res,
            "output": "nc",
            "year_range": [start_year, end_year],
            "server": server
        }
        
        task_id_dict, status = await self._client._terrakio_request("POST", f"collections/{collection}/training_samples", json=payload)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Training sample failed with status {status}", status_code=status)
        
        task_id = task_id_dict["task_id"]
        
        await self._client.mass_stats.track_progress(task_id)
        
        return {"task_id": task_id, "collection": collection}

    @require_api_key
    async def download_files(
        self,
        collection: str,
        file_type: str,
        page: Optional[int] = 0,
        page_size: Optional[int] = 100,
        folder: Optional[str] = None,
        url: Optional[bool] = True
    ) -> Dict[str, Any]:
        """
        Get list of signed urls to download files in collection, or download the files directly.

        Args:
            collection: Name of collection
            file_type: Type of files to download - must be either 'raw' or 'processed'
            page: Page number (optional, defaults to 0)
            page_size: Number of files to return per page (optional, defaults to 100)
            folder: If processed file type, which folder to download files from (optional)
            url: If True, return signed URLs; if False, download files directly (optional, defaults to True)

        Returns:
            API response as a dictionary containing list of download URLs (if url=True),
            or a dictionary with downloaded file information (if url=False)

        Raises:
            CollectionNotFoundError: If the collection is not found
            DownloadFilesError: If the API request fails due to unknown reasons
            ValueError: If file_type is not 'raw' or 'processed'
        """
        if file_type not in ['raw', 'processed']:
            raise ValueError(f"file_type must be either 'raw' or 'processed', got '{file_type}'")
        
        params = {"file_type": file_type}
        
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if folder is not None:
            params["folder"] = folder

        response, status = await self._client._terrakio_request("GET", f"collections/{collection}/download", params=params)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise DownloadFilesError(f"Download files failed with status {status}", status_code=status)
        
        if url:
            return response
        
        downloaded_files = []
        files_to_download = response.get('files', []) if isinstance(response, dict) else []
        
        async with aiohttp.ClientSession() as session:
            for file_info in files_to_download:
                try:
                    file_url = file_info.get('url')
                    filename = file_info.get('file', '')
                    group = file_info.get('group', '')
                    
                    if not file_url:
                        downloaded_files.append({
                            'filename': filename,
                            'group': group,
                            'error': 'No URL provided'
                        })
                        continue
                    
                    async with session.get(file_url) as file_response:
                        if file_response.status == 200:
                            content = await file_response.read()
                            
                            output_dir = folder if folder else "downloads"
                            if group:
                                output_dir = os.path.join(output_dir, group)
                            os.makedirs(output_dir, exist_ok=True)
                            filepath = os.path.join(output_dir, filename)
                            
                            with open(filepath, 'wb') as f:
                                f.write(content)
                            
                            downloaded_files.append({
                                'filename': filename,
                                'group': group,
                                'filepath': filepath,
                                'size': len(content)
                            })
                        else:
                            downloaded_files.append({
                                'filename': filename,
                                'group': group,
                                'error': f"Failed to download: HTTP {file_response.status}"
                            })
                except Exception as e:
                    downloaded_files.append({
                        'filename': file_info.get('file', 'unknown'),
                        'group': file_info.get('group', ''),
                        'error': str(e)
                    })
        
        return {
            'collection': collection,
            'downloaded_files': downloaded_files,
            'total': len(downloaded_files)
        }

    @require_api_key
    async def gen_and_process(
        self,
        collection: str,
        requests_file: Union[str, Any],
        output: str,
        folder: str,
        consumer: Union[str, Any],
        extra: Optional[Dict[str, Any]] = None,
        force_loc: Optional[bool] = False,
        skip_existing: Optional[bool] = True,
        server: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate data and run post-processing in a single task.

        Args:
            collection: Name of collection
            requests_file: Path to JSON file or file object containing request configurations
            output: Output type (str)
            folder: Folder to store output
            consumer: Path to post processing script or file object
            extra: Additional configuration parameters (optional)
            force_loc: Write data directly to the cloud under this folder (optional, defaults to False)
            skip_existing: Skip existing data (optional, defaults to True)
            server: Server to use (optional)

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        await self.get_collection(collection = collection)

        upload_urls = await self._get_upload_url(collection=collection)
        url = upload_urls['url']
        
        # Handle requests_file - either file path (str) or file object
        if isinstance(requests_file, str):
            await self._upload_file(requests_file, url)
        else:
            # File object - read JSON and upload directly
            json_data = json.load(requests_file)
            await self._upload_json_data(json_data, url)

        # Handle consumer - either file path (str) or file object
        if isinstance(consumer, str):
            with open(consumer, 'rb') as f:
                consumer_content = f.read()
        else:
            # Assume it's a file object
            consumer_content = consumer.read()
        
        form = aiohttp.FormData()
        form.add_field('output', output)
        form.add_field('force_loc', str(force_loc).lower())
        form.add_field('skip_existing', str(skip_existing).lower())
        
        if server is not None:
            form.add_field('server', server)
        
        form.add_field('extra', json.dumps(extra or {}))
        form.add_field('folder', folder)
        form.add_field(
            'consumer',
            consumer_content,
            filename='consumer.py',
            content_type='text/x-python'
        )
        
        response, status = await self._client._terrakio_request(
            "POST",
            f"collections/{collection}/gen_and_process",
            data=form
        )
        
        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Gen and process failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def create_pyramids(
        self,
        name: str,
        levels: int,
        config: Dict[str, Any],
        collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create pyramid tiles for a dataset.

        Args:
            name: Dataset name
            levels: Maximum zoom level for pyramid (e.g., 8)
            config: Dictionary of configuration key-value pairs
            collection: Name of collection (optional, defaults to "{name}-pyramids")

        Returns:
            API response with task_id

        Raises:
            GetTaskError: If the API request fails
            CollectionNotFoundError: If the collection is not found
            CreateCollectionError: If collection creation fails
        """
        if collection is None or collection == "":
            collection = f"{name}-pyramids"
            try:
                await self.create_collection(collection=collection)
            except CollectionAlreadyExistsError:
                # Collection already exists, continue with it
                pass
        else:
            try:
                await self.get_collection(collection=collection)
            except CollectionNotFoundError:
                await self.create_collection(collection=collection)

        pyramid_request = {
            'collection_name': collection,
            'name': name,
            'max_zoom': levels,
            **config
        }

        response, status = await self._client._terrakio_request(
            "POST",
            "tasks/pyramids",
            json=pyramid_request
        )

        if status != 200:
            raise GetTaskError(
                f"Pyramid creation failed with status {status}: {response}", 
                status_code=status
            )
        
        task_id = response["task_id"]
        await self.track_progress(task_id)

        return {"task_id": task_id}

    @require_api_key
    async def tif(
        self,
        file: str,
        dataset: str,
        product: List[str],
        bucket: str,
        path: str,
        no_data: float,
        max_zoom: int,
        date: str,
        add_config: bool = True,
        generate_pyramids: bool = True,
        geot: Optional[List[float]] = None,
        no_interactive: bool = False,
        tile_size: int = 400,
        update_config: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest a tif file and optionally generate pyramids.

        Args:
            file: Path to the tif file to ingest
            dataset: Dataset name
            product: List of product names
            bucket: Storage bucket
            path: Storage path
            no_data: No data value
            max_zoom: Maximum zoom level
            date: Date string
            add_config: Add dataset configuration (default: True)
            generate_pyramids: Generate pyramids after ingestion (default: True)
            geot: Geotransform parameters (optional)
            no_interactive: Non-interactive mode (default: False)
            tile_size: Size of tiles (default: 400)
            update_config: Update config with new date (default: True)

        Returns:
            API response with task_id

        Raises:
            GetTaskError: If the API request fails
        """
        with rio.open(file) as src:
            if len(product) != src.meta["count"]:
                print("[bold red]Products don't match number of bands[/bold red]")
                raise typer.Exit(code=2)
            meta = src.meta
            dtype = meta["dtype"]
            transform = meta["transform"]
            if not geot:
                geot = [transform[2], transform[0], transform[1], transform[5], transform[3], transform[4]]
            x0, y0 = geot[0], geot[3]
            proj = pyproj.Proj(meta["crs"])

            j_max = int(math.ceil(meta['height'] / tile_size))
            i_max = int(math.ceil(meta['width'] / tile_size))

            if add_config:
                await self._client.datasets.create_dataset(
                    name=dataset,
                    products=product,
                    dates_iso8601=[date],
                    bucket=bucket,
                    path=f"{path}/%s_%s_%03d_%03d_%02d.snp",
                    data_type=dtype,
                    no_data=no_data,
                    i_max=i_max,
                    j_max=j_max,
                    y_size=tile_size,
                    x_size=tile_size,
                    proj4=proj.definition_string(),
                    abstract="",
                    geotransform=geot,
                    max_zoom=0,
                )
            else:
                if not no_interactive and update_config:
                    await self._client.datasets.update_dataset(
                        name=dataset,
                        append=True,
                        dates_iso8601=[date]
                    )
    
            with tempfile.TemporaryDirectory() as tmpdirname:
                progress = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                )
                
                with progress:
                    task = progress.add_task(description="[bold green]Writing tiles...[/bold green]", total=j_max*i_max)
                    for j in range(0, j_max+1):
                        for i in range(0, i_max+1):
                            left = x0 + i*tile_size*geot[1]
                            right = x0 + (i+1)*tile_size*geot[1]
                            top = y0 - j*tile_size*geot[1]
                            bottom = y0 - (j+1)*tile_size*geot[1]

                            data = src.read(window=from_bounds(left, bottom, right, top, src.transform), boundless=True)
                            for band in range(src.meta["count"]):
                                out = data[band]
                                if np.all(np.isnan(out)):
                                    progress.update(task, advance=1)
                                    continue
                            
                                out[np.isnan(out)] = no_data
                                out_bytes = out.tobytes()
                                
                                from dateutil import parser

                                date_obj = parser.parse(date)
                                with open(f"{tmpdirname}/{product[band]}_{date_obj.strftime('%Y%m%d%H%M%S')}_{i:03d}_{j:03d}_00.snp", 'wb') as f:
                                    comp = snappy.compress(out_bytes)
                                    f.write(comp)
                                progress.update(task, advance=1)

                subprocess.run(
                    ["gsutil", "-m", "cp", "-r", "*", f"gs://{bucket}/{path}"],
                    cwd=f"{tmpdirname}",
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

        if generate_pyramids:
            await self.create_pyramids(
                name = dataset,
                levels = max_zoom,
                config = {
                    "products": product,
                    "dates_iso8601": [date],
                }
            )

    def tile_generator(self, x_min, y_min, x_max, y_max, aoi, crs, res, tile_size, expression, output = OutputTypes.netcdf, fully_cover=True):
        
        i_max = int((x_max-x_min)/(tile_size*res))
        j_max = int((y_max-y_min)/(tile_size*res))
        if fully_cover:
            i_max += 1
            j_max += 1
        for j in range(0, int(j_max)):
            for i in range(0, int(i_max)):
                x = x_min + i*(tile_size*res)
                y = y_max - j*(tile_size*res)
                bbox = shapely.geometry.box(x, y-(tile_size*res), x + (tile_size*res), y)
                if not aoi.geometry[0].intersects(bbox):
                    continue
                feat  = {"type": "Feature", "geometry": bbox.__geo_interface__}
                data = {
                    "feature": feat,
                    "in_crs": crs,
                    "out_crs": crs,
                    "resolution": res,
                    "expr" : expression,
                    "output" : output.value,
                }
                yield data, i , j


    def get_bounds(self, aoi, crs, to_crs = None):
        gdf : gpd.GeoDataFrame = gpd.read_file(aoi)
        gdf = gdf.set_crs(crs, allow_override=True)
        if to_crs:
            gdf = gdf.to_crs(to_crs)
        bounds = gdf.geometry[0].bounds
        return *bounds, gdf

    def validate_date(self, date: str) -> str:
        try:
            date = dateutil.parser.parse(date)
            return date
        except ValueError:
            print(f"Invalid date: {date}")
            raise typer.BadParameter(f"Invalid date: {date}")


    @require_api_key
    async def dataset(
        self,
        products: List[str],
        name: str,
        bucket: str = "terrakio",
        location: str = "testing/MSWXsmall",
        aoi: Optional[str] = None,
        expression: Optional[str] = None,
        date: Optional[str] = "2021-01-01",
        tile_size: float = 100,
        crs: str = "epsg:4326",
        res: float = 10,
        out_res: float = 10,
        no_data: float = -9999,
        dtype: str = "float32",
        create_doc: bool = False,
        skip_test: bool = False,
        force_res: bool = False,
        to_crs: Optional[str] = None,
        fully_cover: bool = True,
        skip_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a dataset with the specified parameters.

        Args:
            products: List of product names
            name: Name of the dataset
            bucket: Storage bucket
            location: Storage location
            aoi: Path to GeoJSON file containing area of interest
            expression: Expression for data processing
            date: Date in YYYY-MM-DD format
            tile_size: Size of tiles (default: 100)
            crs: Coordinate reference system (default: "epsg:4326")
            res: Resolution (default: 10)
            out_res: Output resolution (default: 10)
            no_data: No data value (default: -9999)
            dtype: Data type (default: "float32")
            create_doc: Add dataset to the DB (default: False)
            skip_test: Skip testing the expression (default: False)
            force_res: Force resolution in case requests are too large (default: False)
            to_crs: Target coordinate reference system
            fully_cover: Fully cover the area (default: True)
            skip_existing: Skip existing data (default: False)

        Returns:
            Response containing task_id and collection name

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails
        """
        await self.create_collection(collection = name, bucket = bucket, location = location)
        date = self.validate_date(date)
        sample = None
        reqs = []
        x_min, y_min, x_max, y_max, aoi = self.get_bounds(aoi, crs, to_crs)
        if to_crs is None:
            to_crs = crs
        c=0
        for tile_req, i, j in self.tile_generator(x_min, y_min, x_max, y_max, aoi, to_crs, res, tile_size, expression, fully_cover = fully_cover):
            c+=1
            if force_res:
                tile_req["force_res"] = True
            req_names = []
            for product in products:
                req_names.append(f"{product}_{date.strftime('%Y%m%d')}000000_{i:03d}_{j:03d}_00")
            reqs.append({"group": name, "file": req_names, "request": tile_req})
            if sample is None:
                sample = tile_req["expr"]
        i_max = int((x_max-x_min)/(tile_size*res))
        j_max = int((y_max-y_min)/(tile_size*res))
        geot = [x_min, out_res, 0, y_max, 0, -out_res]
        if not skip_test:
            result = await self._client.geoquery(**reqs[0]["request"], debug = "requests")
            request_count = result.get('request_count', 0)

        user_quota = await self._client.auth.get_user_quota()
        user_quota = user_quota.get('quota', -9999)
        
        if user_quota !=-9999 and user_quota < len(reqs) * request_count:
            raise QuotaInsufficientError(f"User quota is insufficient. Please contact support to increase your quota.")

        upload_urls = await self._get_upload_url(collection=name)
        url = upload_urls['url']
        await self._upload_json_data(reqs, url, use_gzip=True)

        payload = {"output": "snp", "skip_existing": skip_existing}
        
        task_id, status = await self._client._terrakio_request("POST", f"collections/{name}/generate_data", json=payload)
        task_id = task_id["task_id"]
        if dtype == self.Dataset_Dtype.uint8.value:
            no_data = int(no_data)
        if create_doc:
            await self._client.datasets.create_dataset(
                name=name,
                products=products,
                dates_iso8601=[date.isoformat()],
                proj4=pyproj.CRS.to_proj4(aoi.crs),
                i_max=i_max,
                j_max=j_max,
                x_size=int((res*tile_size)/out_res),
                y_size=int((res*tile_size)/out_res),
                geotransform=geot,
                no_data=no_data,
                data_type=dtype,
                bucket=bucket,
                path=f"{location}/%s_%s_%03d_%03d_%02d.snp",
                max_zoom=0,
            )

        await self.track_progress(task_id)


    @require_api_key
    async def tiles(
        self,
        collection: str,
        name: str = "irrigation_2019",
        aoi: Optional[str] = None,
        expression: str = "NSWIrrigation.landuse@(year=2019)",
        output: OutputTypes = OutputTypes.netcdf,
        tile_size: float = 10000,
        crs: str = "epsg:3577",
        res: float = 10,
        skip_test: bool = False,
        force_res: bool = False,
        to_crs: Optional[str] = None,
        fully_cover: bool = True,
        skip_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate tiles with the specified parameters.

        Args:
            collection: Name of the collection
            name: Name of the dataset (default: "irrigation_2019")
            aoi: Path to GeoJSON file containing area of interest
            expression: Expression for data processing (default: "NSWIrrigation.landuse@(year=2019)")
            output: Output format (default: "netcdf")
            tile_size: Size of tiles (default: 10000)
            crs: Coordinate reference system (default: "epsg:3577")
            res: Resolution (default: 10)
            skip_test: Skip testing the expression (default: False)
            force_res: Force resolution in case requests are too large (default: False)
            to_crs: Target coordinate reference system
            fully_cover: Fully cover the area (default: True)
            skip_existing: Skip existing data (default: False)

        Returns:
            Response containing task_id

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails
        """
        

        await self.get_collection(collection=collection)

        reqs = []
        sample = None
        x_min, y_min, x_max, y_max, aoi = self.get_bounds(aoi, crs, to_crs)
        if to_crs is None:
            to_crs = crs
        for tile_req, i, j in self.tile_generator(x_min, y_min, x_max, y_max, aoi, to_crs, res, tile_size, expression, output, fully_cover):
            if force_res:  
                tile_req["force_res"] = True
            req_name = f"{name}_{i:02d}_{j:02d}"
            reqs.append({"group": "tiles", "file": req_name, "request": tile_req})
            if sample is None:
                sample = tile_req["expr"]

        if not skip_test:
            print("the reqs are ", reqs[0])
            result = await self._client.geoquery(**reqs[0]["request"], debug = "requests")
            request_count = result.get('request_count', 0)

        user_quota = await self._client.auth.get_user_quota()
        user_quota = user_quota.get('quota', -9999)
        
        if user_quota !=-9999 and user_quota < len(reqs) * request_count:
            raise QuotaInsufficientError(f"User quota is insufficient. Please contact support to increase your quota.")

        count = len(reqs)
        groups = list(set(dic["group"] for dic in reqs))
        print(f"[green]{count}[/green] requests with [blue]{len(groups)}[/blue] groups identified.")
        upload_urls = await self._get_upload_url(collection=collection)
        url = upload_urls['url']
        await self._upload_json_data(reqs, url, use_gzip=True)

        payload = {"output": output.value, "skip_existing": skip_existing}
        
        task_id, status = await self._client._terrakio_request("POST", f"collections/{collection}/generate_data", json=payload)
        task_id = task_id["task_id"]

        await self.track_progress(task_id)

    @require_api_key
    async def polygons(
        self,
        collection: str,
        aoi: str,
        expression: str = "mean:space(MSWX.air_temperature@(year=2022))",
        output: OutputTypes = OutputTypes.netcdf,
        id_field: str = "GID_0",
        crs: str = "epsg:4326",
        res: float = -1,
        skip_test: bool = False,
        skip_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate mass-stats for polygons in a GeoJSON file using the same expression.

        Args:
            collection: Name of the collection
            name: Name of the dataset
            aoi: Path to GeoJSON file containing area of interest
            expression: Expression for data processing (default: "mean:space(MSWX.air_temperature@(year=2022))")
            output: Output format (default: "netcdf")
            id_field: Field name to use as identifier (default: "GID_0")
            crs: Coordinate reference system (default: "epsg:4326")
            res: Resolution (default: -1)
            skip_test: Skip testing the expression (default: False)
            skip_existing: Skip existing data (default: False)

        Returns:
            Response containing task_id

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails
            ValueError: If id_field not found in feature properties
        """
        await self.get_collection(collection=collection)

        gdf = gpd.read_file(aoi)
        sample = None
        features = gdf.__geo_interface__
        reqs = []
        for feature in features["features"]:
            feat = {
                "type": "Feature",
                "properties": {},
                "geometry": feature["geometry"],
            }
            request = {
                "feature": feat,
                "expr": expression,
                "output": output.value,
                "in_crs": crs, 
                "out_crs": crs,
                "resolution": res,
            }
            if id_field not in feature["properties"]:
                raise ValueError(f"ID field {id_field} not found in feature properties.")
            reqs.append({"group": "polygons", "file": feature["properties"][id_field], "request": request, "metadata": feature["properties"]})
            if sample is None:
                sample = request["expr"]

        # Test first request to ensure expression is valid
        if not skip_test:
            result = await self._client.geoquery(**reqs[0]["request"], debug="requests")
            request_count = result.get('request_count', 0)

        user_quota = await self._client.auth.get_user_quota()
        user_quota = user_quota.get('quota', -9999)
        
        if user_quota != -9999 and user_quota < len(reqs) * request_count:
            raise QuotaInsufficientError(f"User quota is insufficient. Please contact support to increase your quota.")
        
        count = len(reqs)
        groups = list(set(dic["group"] for dic in reqs))
        print(f"[green]{count}[/green] requests with [blue]{len(groups)}[/blue] groups identified.")
        
        upload_urls = await self._get_upload_url(collection=collection)
        url = upload_urls['url']
        await self._upload_json_data(reqs, url, use_gzip=True)

        payload = {"output": output.value, "skip_existing": skip_existing}
        
        task_id, status = await self._client._terrakio_request("POST", f"collections/{collection}/generate_data", json=payload)
        task_id = task_id["task_id"]

        await self.track_progress(task_id)

        return {"task_id": task_id, "collection": collection}