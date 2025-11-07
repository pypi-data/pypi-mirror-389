import os
from typing import Optional

import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType
from planqk.api.client import PlanqkApiClient
from planqk.api.sdk import DataPoolDto, DataPoolFileDto
from planqk.quantum.client import PlanqkQuantumClient
from planqk.quantum.client.sdk import AzureIonqJobInput, Job, CalibrationResponse, Backend, BackendStateInfo, AzureIonqJobInputCircuitItem
from planqk.service.client import PlanqkServiceClient, PlanqkServiceExecution

PLATFORM_BASE_URL = "https://api.hub.kipu-quantum.com/qc-catalog"

kipu_access_token = os.getenv("KIPU_ACCESS_TOKEN")
if kipu_access_token is None:
    raise ValueError("Please set the your personal access token of the Kipu Quantum Hub as KIPU_ACCESS_TOKEN environment variable.")

planqk_api_client = PlanqkApiClient(access_token=kipu_access_token)
planqk_quantum_client = PlanqkQuantumClient(access_token=kipu_access_token)

client = httpx.AsyncClient(
    base_url="https://api.hub.kipu-quantum.com/qc-catalog",
    headers={"X-Auth-Token": kipu_access_token}
)

openapi_spec = httpx.get("https://api.hub.kipu-quantum.com/qc-catalog/docs").json()

mcp = FastMCP.from_openapi(
    name="Kipu Quantum Hub MCP Server",
    instructions="""
        This server provides tools related to the Kipu Quantum Hub platform.
        It allows you to interact with the platform and perform various tasks.
    """,
    openapi_spec=openapi_spec,
    client=client,
    route_maps=[
        # Exclude all data pool routes as they are implemented manually below
        RouteMap(
            pattern=r"^qc-catalog/datapools/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
        RouteMap(
            pattern=r"^qc-catalog/service-jobs/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
    ],
)


def main():
    mcp.run()

@mcp.tool
def list_datapools() -> list[DataPoolDto]:
    """Retrieves a list of all datapools of the user."""
    data_pools = planqk_api_client.data_pools.get_data_pools()
    return data_pools


@mcp.tool
def get_datapool_details(datapool_id: str) -> DataPoolDto:
    """Retrieves the details of a specific datapool by its ID."""
    datapool = planqk_api_client.data_pools.get_data_pool(datapool_id=datapool_id)
    return datapool


@mcp.tool
def create_datapool(name: str) -> DataPoolDto:
    """Creates a new datapool with the given name and description."""
    new_datapool = planqk_api_client.data_pools.create_data_pool(name=name)
    return new_datapool


@mcp.tool
def update_datapool(datapool_id: str, name: str, description: str, short_description: str) -> DataPoolDto:
    """Updates the name of an existing datapool."""
    updated_datapool = planqk_api_client.data_pools.update_data_pool(id=datapool_id, name=name, description=description,
                                                                     short_description=short_description)
    return updated_datapool


@mcp.tool
def delete_datapool(datapool_id: str) -> None:
    """Deletes a datapool by its ID."""
    planqk_api_client.data_pools.delete_data_pool(id=datapool_id)
    return None


@mcp.tool
def list_files_in_datapool(datapool_id: str) -> list[DataPoolFileDto]:
    """Lists all files in a specific datapool."""
    files = planqk_api_client.data_pools.get_data_pool_files(id=datapool_id)
    return files


@mcp.tool
def upload_file_to_datapool_from_file_path(datapool_id: str, file_path: str, filename: str) -> DataPoolFileDto:
    """Uploads a file to a specific datapool using a file path."""
    with open(file_path, "rb") as file_to_upload:
        added_file = planqk_api_client.data_pools.add_data_pool_file(
            id=datapool_id,
            file=(filename, file_to_upload)  # Pass as tuple (filename, file_content)
        )
    return added_file


@mcp.tool
def upload_file_to_datapool(datapool_id: str, file_content: bytes, filename: str) -> DataPoolFileDto:
    """Uploads a file to a specific datapool using file content as bytes."""
    added_file = planqk_api_client.data_pools.add_data_pool_file(
        id=datapool_id,
        file=(filename, file_content)  # Pass as tuple (filename, file_content)
    )
    return added_file


@mcp.tool
def retrieve_file_content_from_datapool(data_pool_id: str, file_id: str) -> str:
    """Retrieves the content of a specific file in a datapool as a string."""
    file_content_stream = planqk_api_client.data_pools.get_data_pool_file(id=data_pool_id, file_id=file_id)
    content = b""
    for chunk in file_content_stream:
        content += chunk
    return content.decode("utf-8")


@mcp.tool
def delete_file_from_datapool(datapool_id: str, file_id: str) -> None:
    """Deletes a specific file from a datapool."""
    planqk_api_client.data_pools.delete_data_pool_file(id=datapool_id, file_id=file_id)
    return None


@mcp.tool
def list_available_quantum_backends() -> list[dict]:
    """Lists all available quantum quantum backends and simulators on the Kipu Quantum Hub platform."""
    backends = planqk_quantum_client.backends.get_backends()
    return backends


@mcp.tool
def get_quantum_backend_details(backend_id: str) -> Backend:
    """Retrieves the details of a specific quantum backend by its ID."""
    backend_details = planqk_quantum_client.backends.get_backend(id=backend_id)
    return backend_details


@mcp.tool
def check_backend_status(backend_id: str) -> BackendStateInfo:
    """Checks the current status of a specific quantum backend."""
    status = planqk_quantum_client.backends.get_backend_status(id=backend_id)
    return status


@mcp.tool
def get_backend_calibration(backend_id: str) -> CalibrationResponse:
    """Retrieves the latest calibration data for a specific quantum backend."""
    calibration = planqk_quantum_client.backends.get_backend_calibration(id=backend_id)
    return calibration


@mcp.tool
def submit_a_azure_ionq_simulator_job(name: str, circuit: list[AzureIonqJobInputCircuitItem], qubits: int = 2, shots: int = 100) -> Job:
    """
        Submits a quantum job to the Azure IonQ simulator backend.
        Circuit must follow IonQ native gate format.
        The following example circuit applies a Hadamard gate to the first qubit (creating a superposition) and an X gate to the second qubit (flipping it to |1⟩), resulting in the state |+1⟩.

        circuits=[
            {"type": "h", "targets": [0]},
            {"type": "x", "targets": [1], "controls": [0]},
        ]
    """
    ionq_input = AzureIonqJobInput(
        gateset="qis",
        qubits=qubits,
        circuit=circuit
    )

    job = planqk_quantum_client.jobs.create_job(
        backend_id="azure.ionq.simulator",
        name=name,
        shots=shots,
        input=ionq_input,
        input_params={},
        input_format="IONQ_CIRCUIT_V1"
    )
    return job


@mcp.tool
def list_jobs(page: Optional[int] = None, size: Optional[int] = None) -> list[Job]:
    """Get quantum jobs submitted by the user with pagination support."""
    jobs = planqk_quantum_client.jobs.search_jobs(page=page, size=size)
    return jobs


@mcp.tool
def get_job_details(job_id: str) -> Job:
    """Retrieves the details of a specific quantum job by its ID."""
    job_details = planqk_quantum_client.jobs.get_job(id=job_id)
    return job_details


@mcp.tool
def get_job_result(job_id: str) -> dict:
    """Retrieves the result of a completed quantum job by its ID."""
    job_result = planqk_quantum_client.jobs.get_job_result(id=job_id)
    return job_result


@mcp.tool
def list_services_on_marketplace() -> list[dict]:
    """Lists all available services on the Kipu Quantum Hub marketplace."""
    with httpx.Client() as client:
        response = client.get(
            PLATFORM_BASE_URL + "/v2/apis",
            headers={"x-auth-token": kipu_access_token},
        )
        services = response.json()
        return services


@mcp.tool
def get_service_details_from_marketplace(id: str) -> dict:
    """Retrieves the details of a specific service on the Kipu Quantum Hub marketplace by its ID.
    Important for the id, use the id not the service_id property.
    """
    with httpx.Client() as client:
        response = client.get(
            f"{PLATFORM_BASE_URL}/v2/apis/{id}",
            headers={"x-auth-token": kipu_access_token},
        )
        service_details = response.json()
        return service_details


@mcp.tool
def get_service_api_spec(id: str) -> dict:
    """Retrieves the OpenAPI specification of a specific service on the Kipu Quantum Hub marketplace by its ID.
    This helps to understand the required input and output formats for running the service.
    Important for the id, use the id not the service_id property.
    For executing services, the Service SDK is recommended. Refer to the get_code_documentation tool for code examples.
    """
    with httpx.Client() as client:
        response = client.get(
            f"{PLATFORM_BASE_URL}/v2/apis/{id}/api-spec",
            headers={"x-auth-token": kipu_access_token},
        )
        api_spec = response.json()
        return api_spec


@mcp.tool
def run_service_from_marketplace(gateway_endpoint: str, consumer_key: str, consumer_secret: str, request: dict) -> PlanqkServiceExecution:
    """Runs a service execution on the Kipu Quantum Hub marketplace with the provided input data.
    The gateway_endpoint can be found in the service details retrieved from the marketplace.
    Consumer key and secret are provided from the application that is subscribed to the service.
    For the request format, please refer to the service's OpenAPI specification.
    """

    service_client = PlanqkServiceClient(
        service_endpoint=gateway_endpoint,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret
    )

    # Start a service execution
    execution = service_client.run(request=request)

    return execution

@mcp.tool
def get_service_executions_of_subscription(subscriptionId: str) -> list[PlanqkServiceExecution]:
    """Retrieves a list of service executions for the user's subscription."""
    with httpx.Client() as client:
        response = client.get(
            f"{PLATFORM_BASE_URL}/subscriptions/{subscriptionId}/service-executions",
            headers={"x-auth-token": kipu_access_token},
        )
        executions_data = response.json()
        return executions_data

@mcp.tool
def list_use_cases(page: int = 0, size: int = 20, title: str = None) -> list[dict]:
    """Lists all available use cases on the Kipu Quantum Hub platform. Supports pagination and filtering by title."""
    with httpx.Client() as client:
        response = client.get(
            PLATFORM_BASE_URL + "/use-cases",
            params={"page": page, "size": size, "title": title} if title else {"page": page, "size": size},
            headers={"x-auth-token": kipu_access_token},
        )
        use_cases = response.json()
        return use_cases

@mcp.tool
def get_use_case_details(use_case_id: str) -> dict:
    """Retrieves the details of a specific use case by its ID."""
    with httpx.Client() as client:
        response = client.get(
            f"{PLATFORM_BASE_URL}/use-cases/{use_case_id}",
            headers={"x-auth-token": kipu_access_token},
        )
        use_case_details = response.json()
        return use_case_details

@mcp.tool
def list_algorithms(page: int = 0, size: int = 20, name: str = None) -> list[dict]:
    """Lists all available algorithms on the Kipu Quantum Hub platform. Supports pagination and filtering by name."""
    with httpx.Client() as client:
        response = client.get(
            PLATFORM_BASE_URL + "/algorithms",
            params={"page": page, "size": size, "search": name} if name else {"page": page, "size": size},
            headers={"x-auth-token": kipu_access_token},
        )
        algorithms = response.json()
        return algorithms

@mcp.tool
def get_algorithm_details(algorithm_id: str) -> dict:
    """Retrieves the details of a specific algorithm by its ID."""
    with httpx.Client() as client:
        response = client.get(
            f"{PLATFORM_BASE_URL}/algorithms/{algorithm_id}",
            headers={"x-auth-token": kipu_access_token},
        )
        algorithm_details = response.json()
        return algorithm_details

@mcp.tool
def get_code_documentation(topic: str, tokens: int = 100000) -> str:
    """Provides code documentation and examples for using the SDKs of the Kipu Quantum Hub platform.
    Service SDK: Provides an easy way to execute and interact with Services on the Platform.
    Quantum SDK: Provides an easy way to develop quantum code that runs on quantum hardware and simulators supported by the Kipu Quantum Hub.
    """
    with httpx.Client() as client:
        response = client.get(
            "https://context7.com/api/v1/gitlab_planqk-foss/planqk-docs",
            params={"type": "txt", "topic": topic, "tokens": tokens},
        )
        code_docs = response.text
        return code_docs

if __name__ == "__main__":
    main()
