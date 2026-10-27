from fastapi import APIRouter

{domain}_router = APIRouter(prefix="/{domain}", tags=["{domain_class} Information"])
