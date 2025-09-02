import fastapi
from fastapi import FastAPI, HTTPException, Query, Path, status
import pydantic
from typing import List, Dict, Union
from starlette.requests import Request
import logging

# Configure logger
logger = logging.getLogger("fastapi")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


import sympy
import math
import random
import requests
from requests import RequestException
from typing import List, Dict, Any

from pydantic import BaseModel


# Define a list of emojis to use in the API
EMOJIS = ["😀", "🎉", "🚀", "🌟", "🔥", "💡", "🌈", "🍀", "🎶", "📚"]

app = FastAPI()

class NumberProperties(BaseModel):
    number: int
    properties: Dict[str, Union[bool, int, str, List[int]]]
    fun_fact: str
    emoji: str
    classification: List[str]

class ErrorResponse(BaseModel):
    error: str
    detail: str
    suggestion: str

def is_fibonacci(num: int) -> bool:
    """Universal Fibonacci check that works with all SymPy versions"""
    try:
        # Try modern function name first
        check_square = sympy.is_square
    except AttributeError:
        try:
            # Fallback to legacy name
            check_square = sympy.issquare
        except AttributeError:
            # Final fallback to pure Python
            def check_square(x):
                s = math.isqrt(x)
                return s*s == x
    
    return check_square(5*num**2 + 4) or check_square(5*num**2 - 4)

def get_factors(num: int) -> List[int]:
    """Get all factors of a number"""
    factors = set()
    for i in range(1, int(math.sqrt(abs(num))) + 1):
        if num % i == 0:
            factors.update({i, num // i})
    return sorted(factors)

def get_local_fun_fact(num: int) -> str:
    """Generate a fun fact locally"""
    facts = [
        f"{num} is {'even' if num % 2 == 0 else 'odd'}.",
        f"{num} is {'prime' if sympy.isprime(num) else 'composite'}.",
        f"{num} is {'a Fibonacci number' if is_fibonacci(num) else 'not a Fibonacci number'}.",
        f"{num} squared is {num ** 2}.",
        f"{num} in binary is {bin(num)[2:]}.",
        f"{num} in hexadecimal is {hex(num)[2:]}.",
        f"The factorial of {num} is {math.factorial(num) if num < 20 else 'too large to calculate'}.",
        f"{num} is {'a perfect square' if math.isqrt(num) ** 2 == num else 'not a perfect square'}.",
        f"{num} is {'a perfect cube' if round(num ** (1/3)) ** 3 == num else 'not a perfect cube'}.",
        f"{num} is the atomic number of {['beryllium','boron','carbon','nitrogen','oxygen','fluorine','neon'][num-4] if 4 <= num <= 10 else 'an unknown element'}."
    ]
    return random.choice(facts)

async def get_fun_fact(num: int) -> str:
    """Get a fun fact with fallback to local facts"""
    try:
        response = requests.get(
            f"http://numbersapi.com/{num}/math",
            timeout=2
        )
        response.raise_for_status()
        return response.text.strip()
    except RequestException as e:
        logger.warning(f"External fact API failed: {e}. Using local facts.")
        return get_local_fun_fact(num)

def classify_number(num: int) -> List[str]:
    """Classify number with various properties"""
    classifications = []
    
    if num % 2 == 0:
        classifications.append("even")
    else:
        classifications.append("odd")
    
    if sympy.isprime(num):
        classifications.append("prime")
    else:
        classifications.append("composite")
    
    if is_fibonacci(num):
        classifications.append("fibonacci")
    
    if math.isqrt(num) ** 2 == num:
        classifications.append("perfect-square")
    
    if round(num ** (1/3)) ** 3 == num:
        classifications.append("perfect-cube")
    
    if (num & (num - 1)) == 0 and num != 0:
        classifications.append("power-of-two")
    
    if num == sum(int(d) ** len(str(abs(num))) for d in str(abs(num))):
        classifications.append("armstrong")
    
    if num > 0 and sum(i for i in range(1, num) if num % i == 0) == num:
        classifications.append("perfect-number")
    
    return classifications

# API Endpoints
# API Endpoints
@app.get(
    "/number/{num}",
    response_model=NumberProperties,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get properties of a specific number",
    description="Returns mathematical properties, a fun fact, and an emoji for the given number."
)
async def get_number_properties(
    num: int = fastapi.Path(..., title="The number to analyze", example=42)
):
    """
    Analyze a number and return its mathematical properties with additional interesting information.
    
    - **num**: Any valid integer (positive, negative, or zero)
    - **returns**: Detailed number properties with fun facts
    """
    try:
        properties = {
            "is_even": num % 2 == 0,
            "is_prime": sympy.isprime(num),
            "is_fibonacci": is_fibonacci(num),
            "is_perfect_square": math.isqrt(num) ** 2 == num,
            "is_perfect_cube": round(num ** (1/3)) ** 3 == num,
            "is_power_of_two": (num & (num - 1)) == 0 and num != 0,
            "is_armstrong": num == sum(int(d) ** len(str(abs(num))) for d in str(abs(num))),
            "is_perfect_number": num > 0 and sum(i for i in range(1, num) if num % i == 0) == num,
            "absolute_value": abs(num),
            "sign": "positive" if num > 0 else "negative" if num < 0 else "zero",
            "factors": get_factors(num),
            "digit_sum": sum(int(d) for d in str(abs(num))),
            "binary": bin(num)[2:],
            "hexadecimal": hex(num)[2:],
            "factorial": math.factorial(num) if num < 20 else "Too large to calculate"
        }

        return {
            "number": num,
            "properties": properties,
            "fun_fact": await get_fun_fact(num),
            "emoji": EMOJIS[abs(num) % len(EMOJIS)],
            "classification": classify_number(num)
        }
        
    except Exception as e:
        logger.error(f"Error processing number {num}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e),
                "suggestion": "Try again later or contact support"
            }
        )

@app.get(
    "/number",
    response_model=NumberProperties,
    summary="Get properties of a number via query parameter",
    description="Alternative endpoint that takes the number as a query parameter instead of path parameter."
)
async def get_number_properties_via_query(
    num: int = Query(..., title="The number to analyze", example=42)
):
    """Wrapper for the path parameter version"""
    return await get_number_properties(num)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Welcome to the Number Properties API!",
        "documentation": "/docs or /redoc",
        "try_it": "/number/42 or /number?num=42"
    }