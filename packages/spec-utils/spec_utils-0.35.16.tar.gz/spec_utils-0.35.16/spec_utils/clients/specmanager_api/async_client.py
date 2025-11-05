from __future__ import annotations
import asyncio
import datetime as dt
import sys
from pydantic import validate_arguments
from typing import Any, AsyncGenerator, Dict, Optional, Sequence, Union, List
from spec_utils.clients.http import AsyncAPIKeyClient, JSONResponse
from spec_utils.schemas import specmanager as sm_schema


if (
    sys.platform.startswith("win")
    and sys.version_info[0] == 3
    and sys.version_info[1] >= 8
):
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)


class AsyncClient(AsyncAPIKeyClient):

    __name__ = "SPECManagerAPI"

    async def __aenter__(self, *args, **kwargs) -> AsyncClient:
        return await super().__aenter__(*args, **kwargs)

    async def get_clockings(
        self,
        type_: str,
        from_: Union[dt.datetime, str],
        to_: Union[dt.datetime, str],
        fromHistory: bool = False,
        employeeDetail: bool = False,
        employeeData: List[Union[int, str]] = [],
        pageSize: Optional[int] = None,
        page: int = 1,
        **kwargs,
    ) -> JSONResponse:
        """Get clockings from SM API with self.get() passing type_ and
            parameters recived.

        Args:
            type_ (str): Employee type. Check EmployeeType class for options.
            from_ (Union[dt.datetime, str]):
                Datetime to apply as start filter of clockings.
            to_ (Union[dt.datetime, str]):
                Datetime to apply as end filter of clockings.
            fromHistory (bool, optional):
                True or False to get clockings from HISTORICO.
                Defaults to False.
            employeeDetail (bool, optional):
                True to get serialized employee.
                Defaults to False.
            employeeData (List[Union[int, str]], optional):
                List of Optional Data of employee to get from SM.
                Defaults to [].
            pageSize (Optional[int], optional):
                Max results per page.
                Defaults to None.
            page (int, optional):
                Page number.
                Defaults to 1.

        Returns:
            JSONResponse: List of match clockings
        """

        # path prepare
        path = f"clockings/{type_}"

        # datetime to str
        if isinstance(from_, dt.datetime):
            from_ = from_.strftime("%Y%m%d%H%M%S")

        if isinstance(to_, dt.datetime):
            to_ = to_.strftime("%Y%m%d%H%M%S")

        # parameters prepare
        params = {
            "from": from_,
            "to": to_,
            "fromHistory": fromHistory,
            "employeeDetail": employeeDetail,
            "pageSize": pageSize or self.defaults.PAGE_SIZE,
            "page": page,
        }

        # append data
        if employeeData:
            params["employeeData"] = ",".join([str(e) for e in employeeData])

        # request.get -> json
        return await self.get(path=path, params=params, **kwargs)

    @validate_arguments
    async def post_employee(
        self, type_: str, employee: sm_schema.Employee, **kwargs
    ) -> JSONResponse:
        """Send employee to SM API with self.post()

        Args:
            type_ (str):
                Employee type enpoint to add in POST /employees/{type_} SM API.
                Check EmployeeType class for options.
            employee (sm_schema.Employee):
                Employee schema (spec_utils._schemas.specmanager.Employee).
                Can be Employee instance or dict with values.

        Returns:
            JSONResponse: Import result
        """

        # path prepare
        path = f"employees/{type_}"

        # to dict without unset
        json_employee = employee.model_dump(
            mode="json",
            exclude=employee.Meta.nondefault,
            exclude_unset=True,
        )

        # update nondefault fields
        for nondef in employee.Meta.nondefault:
            _method = getattr(employee, f"get_{nondef}")
            if callable(_method):
                json_employee.update(_method())

        # request.get -> json
        return await self.post(path=path, params=json_employee, **kwargs)

    @validate_arguments
    async def post_employees(
        self, type_: str, employees: List[sm_schema.Employee], **kwargs
    ) -> List[Dict[str, Any]]:
        """Send employees to SM API with self.post_employee()

        Args:
            type_ (str):
                Employee type enpoint to add in POST /employees/{type_} SM API.
                Check EmployeeType class for options.
            employees (List[sm_schema.Employee]): List of Employee schema.

        Returns:
            List[Dict[str, Any]]: List of import result
        """

        async def send_employee() -> AsyncGenerator[JSONResponse, None]:
            for employee in employees:
                yield await self.post_employee(type_=type_, employee=employee, **kwargs)

        return [res async for res in send_employee()]

    @validate_arguments
    async def set_access(
        self,
        employee_type: str,
        employee_nif: str,
        calendar: str,
        adc: Sequence[str],
        start_date: Union[dt.date, str],
        end_date: Union[dt.date, str],
    ) -> List[Dict[str, Any]]:
        """Set access permissions for an employee across multiple ADC areas.

        This method configures access permissions for a specific employee by making
        POST requests to the SPECManagerAPI for each ADC (Access Control) area provided.

        Args:
            employee_type (str): The type/category of the employee.
            employee_nif (str): The National Identification Number (NIF) of the employee.
            calendar (str): The calendar identifier to associate with the access.
            adc (Sequence[str]): A sequence of ADC (Access Control) area identifiers.
            start_date (Union[dt.date, str]): The start date for the access period.
            end_date (Union[dt.date, str]): The end date for the access period.

        Returns:
            List[Dict[str, Any]]: List of access set results.

        Note:
            The method iterates through each ADC area and creates individual access
            parameters for each one, then sends POST requests to set the access
            permissions via the SPECManagerAPI.
        """

        # path prepare
        path = "access/set"

        async def set_areas() -> AsyncGenerator[JSONResponse, None]:
            for a in adc:
                ap = sm_schema.AccessParams(
                    employeeType=employee_type,
                    employeeNIF=employee_nif,
                    calendar=calendar,
                    adc=a,
                    startDate=start_date,
                    endDate=end_date,
                )
                yield await self.post(path=path, params=ap.to_params())

        return [res async for res in set_areas()]
