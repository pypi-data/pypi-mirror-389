"""

MCP
"""

from typing import Dict, Any, Optional, List, Callable
from pydantic import Field
from typing import Annotated

from .base import with_file_support_decorator as econometric_tool


# 
FILE_INPUT_PARAMS = {
    "file_content": Annotated[
        Optional[str],
        Field(
            default=None,
            description="""CSVJSONTXT

 
- CSV: 
- JSON: {"": [], ...}  [{"1": , ...}, ...]
- TXT: 
  * 
  * 
  * :    = 

 
- base64
- 
- file_content
- .csv/.json/.txt

 
CSV: "1,2\\n1.2,3.4\\n2.3,4.5"
JSON: "{\\"x\\": [1,2,3], \\"y\\": [4,5,6]}"
TXT: "1.5\\n2.3\\n3.1"
TXT: "x y\\n1 2\\n3 4"
TXT: "x: 1 2 3\\ny: 4 5 6"
"""
        )
    ],
    "file_format": Annotated[
        str,
        Field(
            default="auto",
            description="""


- "auto": - 
- "csv": CSV - 
- "json": JSON - JSON
- "txt": TXT - 

 
1. JSON
2. CSV
3. TXT
4. .csv/.json/.txt

 
- "auto"
- 
- TXT//"""
        )
    ]
}


class ToolConfig:
    """"""
    
    def __init__(
        self,
        name: str,
        impl_func: Callable,
        tool_type: str,
        description: str = "",
        extra_params: Dict[str, Any] = None
    ):
        self.name = name
        self.impl_func = impl_func
        self.tool_type = tool_type
        self.description = description
        self.extra_params = extra_params or {}


def create_tool_wrapper(config: ToolConfig):
    """
    
    
    Args:
        config: 
    
    Returns:
        
    """
    @econometric_tool(config.tool_type)
    async def tool_wrapper(ctx, **kwargs):
        """"""
        # 
        return await config.impl_func(ctx, **kwargs)
    
    # 
    tool_wrapper.__name__ = config.name
    tool_wrapper.__doc__ = config.description
    
    return tool_wrapper


# 
TOOL_TYPE_PARAMS = {
    "multi_var_dict": {
        "data": Annotated[
            Optional[Dict[str, List[float]]],
            Field(
                default=None, 
                description="""

 
- 
- 
- {"1": [1, 2, ...], "2": [1, 2, ...]}

 
- 
- 
- 
- 1

 
{"GDP": [100.5, 102.3, 104.1], "CPI": [2.1, 2.3, 2.2]}

 
- 
- 
- """
            )
        ]
    },
    "regression": {
        "y_data": Annotated[
            Optional[List[float]],
            Field(
                default=None, 
                description="""

 
- 
- 
- x_data

 
- NaN
- 
-  n+2 n

 
[12.5, 13.2, 14.1, 13.8, 15.0]  # 

 
- OLS
- 
- """
            )
        ],
        "x_data": Annotated[
            Optional[List[List[float]]],
            Field(
                default=None, 
                description="""

 
- 
- 
- 
- [[x1_1, x2_1, ...], [x1_2, x2_2, ...], ...]

 
- y_data
- 
- 
- 

 
[[100, 50, 3],    # 1: =100, =50, =3
 [120, 48, 3],    # 2: =120, =48, =3
 [110, 52, 4]]    # 3: =110, =52, =4

 
- OLS
- 
- """
            )
        ],
        "feature_names": Annotated[
            Optional[List[str]],
            Field(
                default=None, 
                description="""

 
- 
- x_data
- 

 
["", "", "", ""]

 
- 
- 
- 
- x1, x2, x3...

 
- 
- 
- """
            )
        ]
    },
    "single_var": {
        "data": Annotated[
            Optional[List[float]],
            Field(
                default=None, 
                description="""

 
- 
- 
- 

 
- 
- 
- 
- 5
- ARIMA30+

 
[100.5, 102.3, 101.8, 103.5, 104.2, 103.8, 105.1]  # 

 
- 
- ADFKPSS
- ACFPACF
- ARIMA/GARCH
- 

 
- 
- 
- 
- """
            )
        ]
    },
    "panel": {
        "y_data": Annotated[
            Optional[List[float]],
            Field(
                default=None, 
                description="""

 
- 
- 
-  =  × 

 
1. [1, 2, ...]
2. [1, 2, ...]
3. entity_idstime_periods

 32
[1000, 1100, 800, 900, 1200, 1300]  # 
1: 2020=1000, 2021=1100
2: 2020=800,  2021=900
3: 2020=1200, 2021=1300

 
- 
- 
- """
            )
        ],
        "x_data": Annotated[
            Optional[List[List[float]]],
            Field(
                default=None, 
                description="""

 
- 
-  =  × 
-  = 
- y_data

 
- y_data
- 
- 

 322
[[50, 100],   # 1-2020: =50, =100
 [52, 110],   # 1-2021: =52, =110
 [40, 80],    # 2-2020
 [42, 90],    # 2-2021
 [60, 150],   # 3-2020
 [62, 160]]   # 3-2021

 
- 
- """
            )
        ],
        "entity_ids": Annotated[
            Optional[List[str]],
            Field(
                default=None, 
                description="""

 
- 
- 
-  = y_data

 
- 
- y_datax_data
- 

 32
["A", "A", "B", "B", "C", "C"]

["1", "1", "2", "2", "3", "3"]

 
- 
- 
- 
- Hausman

 
- ID
- 
- """
            )
        ],
        "time_periods": Annotated[
            Optional[List[str]],
            Field(
                default=None, 
                description="""

 
- 
- 
-  = y_data

 
- 
- y_datax_data
- 

 32
["2020", "2021", "2020", "2021", "2020", "2021"]

["2020-01", "2020-02", "2020-01", "2020-02", "2020-01", "2020-02"]

 
- 
- 
- 
- 

 
- 
- 
- """
            )
        ],
        "feature_names": Annotated[
            Optional[List[str]],
            Field(
                default=None, 
                description="""regression

 
- 
-  = x_data

 
["", "", "", ""]

 
- 
- 
- """
            )
        ]
    },
    "time_series": {
        "data": Annotated[
            Optional[Dict[str, List[float]]],
            Field(
                default=None, 
                description="""

 
- 
- 
- 
- 

 
- 2VARVECM
- single_var
- 
- 
- VAR40+
- VECM60+

 
{
    "GDP": [100.5, 102.3, 104.1, 105.8],     # GDP
    "CPI": [2.1, 2.3, 2.2, 2.4],             #  CPI
    "": [3.5, 3.6, 3.4, 3.7]             # 
}

 
- VAR
- VECM
- 
- 
- Granger
- 

 
- 
- 
- VAR
- VECM
- """
            )
        ]
    }
}


def get_tool_params(tool_type: str, extra_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    
    
    Args:
        tool_type: 
        extra_params: 
    
    Returns:
        
    """
    params = {}
    
    # 
    if tool_type in TOOL_TYPE_PARAMS:
        params.update(TOOL_TYPE_PARAMS[tool_type])
    
    # 
    params.update(FILE_INPUT_PARAMS)
    
    # 
    if extra_params:
        params.update(extra_params)
    
    return params