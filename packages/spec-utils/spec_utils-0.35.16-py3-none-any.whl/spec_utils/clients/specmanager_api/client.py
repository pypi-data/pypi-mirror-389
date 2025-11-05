from __future__ import annotations
import datetime as dt
from pydantic import validate_arguments
from typing import Any, Optional, Sequence, Union, Dict, List, Tuple
from spec_utils.clients.http import APIKeyClient
from spec_utils.clients.specmanager_api.const import EmployeeType
from spec_utils.schemas import specmanager as sm_schema


class Client(APIKeyClient):

    __name__ = "SPECManagerAPI"

    def __enter__(self, *args, **kwargs) -> Client:
        return super().__enter__(*args, **kwargs)

    def get_clockings(
        self,
        type_: str,
        from_: Union[dt.datetime, str],
        to_: Union[dt.datetime, str],
        fromHistory: Optional[bool] = False,
        employeeDetail: Optional[bool] = False,
        employeeData: Optional[List[Union[int, str]]] = [],
        pageSize: Optional[int] = 20,
        page: Optional[int] = 1,
        **kwargs,
    ) -> Union[Dict, List]:
        """Get clockings from SM API with self.get() passing type_ and
            parameters recived.

        Args:
            type_ (str): Employee type. Check EmployeeType class for options.
            from_ (Union[dt.datetime, str]):
                Datetime to apply as start filter of clockings.
            to_ (Union[dt.datetime, str]):
                Datetime to apply as end filter of clockings.
            fromHistory (Optional[bool], optional):
                True or False to get clockings from HISTORICO.
                Defaults to False.
            employeeDetail (Optional[bool], optional):
                True to get serialized employee.
                Defaults to False.
            employeeData (Optional[List[Union[int, str]]], optional):
                List of Optional Data of employee to get from SM.
                Defaults to [].
            pageSize (Optional[int], optional):
                Max results per page.
                Defaults to 20.
            page (Optional[int], optional):
                Page number.
                Defaults to 1.

        Returns:
            Union[Dict, List]: List of match clockings
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
            "pageSize": pageSize,
            "page": page,
        }

        # append data
        if employeeData:
            params["employeeData"] = ",".join([str(e) for e in employeeData])

        # request.get -> json
        return self.get(path=path, params=params, **kwargs)

    def get_clockings_contractor(
        self,
        from_: Union[dt.datetime, str],
        to_: Union[dt.datetime, str],
        fromHistory: Optional[bool] = False,
        employeeDetail: Optional[bool] = False,
        employeeData: Optional[List[Union[int, str]]] = [],
        pageSize: Optional[int] = 20,
        page: Optional[int] = 1,
        **kwargs,
    ) -> Union[Dict, List]:
        """Get contractor clockings from SM API with self.get_clockings() and
            recived parameters.

        Args:
            from_ (Union[dt.datetime, str]):
                Datetime to apply as start filter of clockings.
            to_ (Union[dt.datetime, str]):
                Datetime to apply as end filter of clockings.
            fromHistory (Optional[bool], optional):
                True or False to get clockings from HISTORICO.
                Defaults to False.
            employeeDetail (Optional[bool], optional):
                True to get serialized employee.
                Defaults to False.
            employeeData (Optional[List[Union[int, str]]], optional):
                List of Optional Data of employee to get from SM.
                Defaults to [].
            pageSize (Optional[int], optional):
                Max results per page.
                Defaults to 20.
            page (Optional[int], optional):
                Page number.
                Defaults to 1.

        Returns:
            Union[Dict, List]: List of match clockings
        """

        # parameters prepare
        params = {
            "type_": EmployeeType.CONTRACTOR,
            "from_": from_,
            "to_": to_,
            "fromHistory": fromHistory,
            "employeeDetail": employeeDetail,
            "pageSize": pageSize,
            "page": page,
            "employeeData": employeeData,
        }

        # request.get -> json
        return self.get_clockings(**params, **kwargs)

    @validate_arguments
    def post_employee(self, type_: str, employee: sm_schema.Employee, **kwargs) -> dict:
        """Send employee to SM API with self.post()

        Args:
            type_ (str):
                Employee type enpoint to add in POST /employees/{type_} SM API.
                Check EmployeeType class for options.
            employee (sm_schema.Employee):
                Employee schema (spec_utils._schemas.specmanager.Employee).
                Can be Employee instance or dict with values.

        Returns:
            dict: Import result
        """

        # path prepare
        path = f"employees/{type_}"

        # request.get -> json
        return self.post(path=path, params=employee.to_params(), **kwargs)

    @validate_arguments
    def post_employees(
        self, type_: str, employees: List[sm_schema.Employee], **kwargs
    ) -> Tuple:
        """Send employees to SM API with self.post_employee()

        Args:
            type_ (str):
                Employee type enpoint to add in POST /employees/{type_} SM API.
                Check EmployeeType class for options.
            employees (List[sm_schema.Employee]): List of Employee schema.

        Returns:
            Tuple: List of import result
        """

        # yield each post_employee response
        def get_results():
            for e in employees:
                yield self.post_employee(type_=type_, employee=e, **kwargs)

        # return all employees result
        return tuple(result for result in get_results())

    @validate_arguments
    def set_access(
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

        def set_areas():
            for a in adc:
                ap = sm_schema.AccessParams(
                    employeeType=employee_type,
                    employeeNIF=employee_nif,
                    calendar=calendar,
                    adc=a,
                    startDate=start_date,
                    endDate=end_date,
                )
                yield self.post(path=path, params=ap.to_params())

        return list(set_areas())
